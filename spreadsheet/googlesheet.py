"""
Created on 2022-04-18

@author: wf
"""
from io import StringIO
from typing import Dict

import pandas as pd
import requests
from ez_wikidata.wbquery import WikibaseQuery
from lodstorage.lod import LOD


class GoogleSheet(object):
    """
    GoogleSheet Handling
    """

    def __init__(self, url):
        """
        Constructor
        """
        self.url = url
        self.dfs = {}

    def open(self, sheetNames):
        """
        Args:
            sheets(list): a list of sheetnames
        """
        self.sheetNames = sheetNames
        for sheetName in sheetNames:
            # csvurl=f"{self.url}/export?format=csv"
            csvurl = f"{self.url}/gviz/tq?tqx=out:csv&sheet={sheetName}"
            response = requests.get(csvurl)
            csvStr = response.content.decode("utf-8")
            self.dfs[sheetName] = pd.read_csv(StringIO(csvStr), keep_default_na=False)

    def fixRows(self, lod: list):
        """
        fix Rows by filtering unnamed columns and trimming
        column names
        """
        for row in lod:
            for key in list(row.keys()):
                if key.startswith("Unnamed"):
                    del row[key]
                trimmedKey = key.strip()
                if trimmedKey != key:
                    value = row[key]
                    row[trimmedKey] = value
                    del row[key]

    def asListOfDicts(self, sheetName):
        """
        convert the given sheetName to a list of dicts

        Args:
            sheetName(str): the sheet to convert
        """
        lod = self.dfs[sheetName].to_dict("records")
        self.fixRows(lod)
        return lod

    @classmethod
    def toWikibaseQuery(
        cls, url: str, sheetName: str = "WikidataMapping", debug: bool = False
    ) -> Dict[str, "WikibaseQuery"]:
        """
        create a dict of wikibaseQueries from the given google sheets row descriptions

        Args:
            url(str): the url of the sheet
            sheetName(str): the name of the sheet with the description
            debug(bool): if True switch on debugging
        """
        gs = GoogleSheet(url)
        gs.open([sheetName])
        entityMapRows = gs.asListOfDicts(sheetName)
        return WikibaseQuery.ofMapRows(entityMapRows, debug=debug)

    @classmethod
    def toSparql(
        cls,
        url: str,
        sheetName: str,
        entityName: str,
        pkColumn: str,
        mappingSheetName: str = "WikidataMapping",
        lang: str = "en",
        debug: bool = False,
    ) -> ("WikibaseQuery", str):
        """
        get a sparql query for the given google sheet

        Args:
            url(str): the url of the sheet
            sheetName(str): the name of the sheet with the description
            entityName(str): the name of the entity as defined in the Wikidata mapping
            pkColumn(str): the column to use as a "primary key"
            mappingSheetName(str): the name of the sheet with the Wikidata mappings
            lang(str): the language to use (if any)
            debug(bool): if True switch on debugging

        Returns:
            WikibaseQuery
        """
        queries = cls.toWikibaseQuery(url, mappingSheetName, debug)
        gs = GoogleSheet(url)
        gs.open([sheetName])
        lod = gs.asListOfDicts(sheetName)
        lodByPk, _dup = LOD.getLookup(lod, pkColumn)
        query = queries[entityName]
        propRow = query.propertiesByColumn[pkColumn]
        pk = propRow["PropertyName"]
        pkVarname = propRow["PropVarname"]
        pkType = propRow["Type"]
        valuesClause = query.getValuesClause(
            lodByPk.keys(), propVarname=pkVarname, propType=pkType, lang=lang
        )

        sparql = query.asSparql(
            filterClause=valuesClause, orderClause=f"ORDER BY ?{pkVarname}", pk=pk
        )
        return query, sparql
