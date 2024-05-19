"""
Created on 2022-04-18

@author: wf
"""

import json
import time
import random
import os
from typing import Dict,List

import gspread
from ez_wikidata.wbquery import WikibaseQuery
from google.oauth2.service_account import Credentials
from lodstorage.lod import LOD


class GoogleSheet(object):
    """
    GoogleSheet Handling
    """

    def __init__(self, url: str, readonly: bool = True, max_retries:int=5, max_wait:float=60.0):
        """
        Initializes an instance of GoogleSheet.

        Args:
            url: URL to the Google Sheet.
            readonly: If True, uses read-only scopes, otherwise uses full access scopes.
        """
        self.url = url
        self.sheet_dict = {}
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly'] \
                      if readonly else \
                      ['https://www.googleapis.com/auth/spreadsheets']
        self.sheet_dict = {}
        self.max_retries=max_retries
        self.max_wait=max_wait
        self.credentials = self.get_credentials()
        
    def safe_api_call(self, func, *args, **kwargs):
        """
        Safe wrapper for API calls with exponential backoff.

        Args:
            func: The API function to call.
            *args: Arguments for the API function.
            **kwargs: Keyword arguments for the API function.

        Returns:
            The result of the API function call.
        """
        base_sleep = 1  # Initial sleep time in seconds
        total_sleep = 0  # Total time slept

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except gspread.exceptions.APIError as e:
                if e.response.status_code != 429:
                    raise  # Reraise if not a quota limit error

                # Calculate sleep time with exponential backoff
                sleep_time = min(base_sleep * (2 ** attempt) + random.random(), self.max_wait - total_sleep)
                if total_sleep + sleep_time > self.max_wait:
                    raise Exception(f"Exceeded maximum wait time of {self.max_wait} seconds for Google API calls.") from e

                print(f"Quota exceeded, retrying in {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                total_sleep += sleep_time
        raise Exception("Maximum retries reached without success.")
    
    def get_credentials(self):
        """
        Check for Google API credentials in the home directory or
        the GOOGLE_API_KEY environment variable
        """
        google_api_key_json=os.getenv("GOOGLE_API_KEY")
        credentials=None
        if google_api_key_json:
            creds_dict=json.loads(google_api_key_json)
            credentials=Credentials.from_service_account_info(creds_dict, scopes=self.scopes)
        else:
            cred_path = os.path.join(os.path.expanduser("~"), ".ose", "google-api-key.json")
            if os.path.exists(cred_path):
                credentials = Credentials.from_service_account_file(cred_path, scopes=self.scopes)
        return credentials
          

    def open(self, sheet_names: list = None) -> dict:
        """
        Opens the Google Sheet and loads the data from specified sheet names into a dictionary.

        Args:
            sheet_names: Optional list of sheet names to open. Opens all sheets if None.

        Returns:
            A dictionary with sheet names as keys and lists of dictionaries (rows) as values.
        """
        credentials = self.get_credentials()
        if not credentials:
            raise Exception("Credentials not found.")

        self.gc = gspread.authorize(credentials)
        self.sh = self.safe_api_call(self.gc.open_by_url, self.url)
        # Retrieve all sheet names if none are provided
        sheet_names = sheet_names or [sheet.title for sheet in self.sh.worksheets()]

        for sheet_name in sheet_names:
            worksheet = self.sh.worksheet(sheet_name)
            records = self.safe_api_call(worksheet.get_all_records)
            self.sheet_dict[sheet_name] = records
      
        return self.sheet_dict

    def asListOfDicts(self, sheet_name: str)->List:
        """
        Converts a sheet to a list of dictionaries.

        Args:
            sheet_name: The name of the sheet to convert.

        Returns:
            A list of dictionaries, each representing a row in the sheet.
        """
        if not sheet_name in self.sheet_dict:
            self.open[sheet_name]
        lod = self.sheet_dict.get(sheet_name)
        return lod

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
        queries=WikibaseQuery.ofMapRows(entityMapRows, debug=debug)
        return queries

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
