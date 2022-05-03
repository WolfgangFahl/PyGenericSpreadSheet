'''
Created on 2022-04-30

@author: wf
'''
#from lodstorage.trulytabular import WikidataProperty
#from lodstorage.lod import LOD
#from spreadsheet.wikidata import Wikidata
from spreadsheet.googlesheet import GoogleSheet
import pprint
from lodstorage.lod import LOD

class WikibaseQuery(object):
    '''
    a Query for Wikibase
    '''

    def __init__(self,entity:str,debug:bool=False):
        '''
        Constructor
        
        Args:
            entity(str): the entity this query represents
            debug(bool): if True switch on debugging
        '''
        self.debug=debug
        self.entity=entity
        self.propertiesByName={}
        self.propertiesById={}
        self.propertiesByVarname={}
        self.propertiesByColumn={}
        
    def addPropertyFromDescriptionRow(self,row):
        '''
        add a property from the given row
        
        Args:
            row(dict): the row to add
        '''
        propName=row['PropertyName']
        propId=row['PropertyId']
        column=row['Column']
        # properties might contain blank - replace for SPARQL variable names
        propVarname=propName.replace(" ","_")
        row['PropVarname']=propVarname
        # set the values of the lookups
        self.propertiesByName[propName]=row
        self.propertiesByColumn[column]=row
        self.propertiesById[propId]=row
        self.propertiesByVarname[propVarname]=row
        
    def getColumnTypeAndVarname(self,propName):
        '''
        get a signature tuple consisting of columnName, propertType and SPARQL variable Name for the given property Name
        
        Args:
            propName(str): the name of the property
            
        Returns:
            column,propType,varName tupel
        '''
        column=self.propertiesByName[propName]["Column"]
        propType=self.propertiesByName[propName]["Type"]
        varName=self.propertiesByName[propName]["PropVarname"]
        return column,propType,varName
        
        
    def inFilter(self,values,propName:str="short_name",lang:str="en"):
        '''
        create a SPARQL IN filter clause
        
        Args:
            values(list): the list of values to filter for
            propName(str): the property name to filter with
            lang(str): the language to apply
        '''
        filterClause=f"\n  FILTER(?{propName} IN("
        delim=""
        for value in values:
            filterClause+=f"{delim}\n    '{value}'@{lang}"
            delim=","
        filterClause+="\n  ))."
        return filterClause
    
    def getValuesClause(self,values,propVarname:str="short_name",propType:str="text",lang:str=None,ignoreEmpty:bool=True,wbPrefix:str="http://www.wikidata.org/entity/"):
        '''
        create a SPARQL Values clause
        
        Args:
            values(list): the list of values to create values for
            propVarname(str): the property variable name to assign the values for
            ignoreEmpty(bool): ignore empty values if True
            wbPrefix(str): a wikibase/wikidata prefix to be removed for items values
        Returns:
            str: the SPARQL values clause
        '''
        valuesClause=f"\n  VALUES(?{propVarname}) {{"
        if lang is not None and propType=="text":
            lang=f'@{lang}'
        else:
            lang=''
        for value in values:
            if value or not ignoreEmpty:
                if not propType:
                    if value and value.startswith(wbPrefix):
                        value=value.replace(wbPrefix,"")
                    valuesClause+=f"\n   ( wd:{value} )"
                else:
                    # escape single quotes
                    value=value.replace("'","\\'")
                    valuesClause+=f"\n  ( '{value}'{lang} )"
        valuesClause+="\n  }."
        return valuesClause
        
    def asSparql(self,filterClause:str=None,orderClause:str=None,pk:str=None,lang:str="en"):
        '''
        get the sparqlQuery for this query optionally applying a filterClause
        
        Args:
            filterClause(str): a filter to be applied (if any)
            orderClause(str): an orderClause to be applied (if any)
            pk(str): primaryKey (if any)
            lang(str): the language to be used for labels
        '''
        sparql=f"""# 
# get {self.entity} records 
#  
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX schema: <http://schema.org/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?item ?itemLabel ?itemDescription
"""
        for propVarname,row in self.propertiesByVarname.items():
            propValue=row["Value"]
            propType=row["Type"]
            # items will automatically fetch labels
            propLabel=f" ?{propVarname}Label" if not propType else ""
            # extid' will automatically fetch formatted URIs
            propUrl=f" ?{propVarname}Url" if propType=="extid" else ""
            if not propValue:
                sparql+=f"\n  ?{propVarname}{propLabel}{propUrl}"
        sparql+="""\nWHERE {
  ?item rdfs:label ?itemLabel.
  FILTER(LANG(?itemLabel) = "%s")
  OPTIONAL { 
    ?item schema:description ?itemDescription.
    FILTER(LANG(?itemDescription) = "%s")
  }
""" % (lang,lang)
        for propVarname,row in self.propertiesByVarname.items():
            propName=row["PropertyName"]
            propValue=row["Value"]
            propId=row["PropertyId"]
            propType=row["Type"]
            if propValue:
                sparql+=f"\n  ?item wdt:{propId} wd:{propValue}."
            else:
                # primary keys are not optional
                optional=pk is None or not propName==pk
                if optional:
                    sparql+=f"\n  OPTIONAL {{"
                sparql+=f"\n    ?item wdt:{propId} ?{propVarname}."
                if not propType:
                    sparql+=f"\n    ?{propVarname} rdfs:label ?{propVarname}Label."
                    sparql+=f"""\n    FILTER(LANG(?{propVarname}Label) = "{lang}")"""
                elif propType=="extid":
                    sparql+=f"\n    wd:{propId} wdt:P1630 ?{propVarname}FormatterUrl." 
                    sparql+=f"\n    BIND(IRI(REPLACE(?{propVarname}, '^(.+)$', ?{propVarname}FormatterUrl)) AS ?{propVarname}Url)."
                if optional:
                    sparql+=f"\n  }}"
        if filterClause is not None:
                sparql+=f"\n{filterClause}"        
        sparql+="\n}"
        if orderClause is not None:
            sparql+=f"\n{orderClause}"
        return sparql
            
    @classmethod
    def sparqlOfGoogleSheet(cls,url:str,sheetName:str,entityName:str,pkColumn:str,mappingSheetName="Wikidata",lang:str="en",debug:bool=False):
        '''
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
        '''
        queries=WikibaseQuery.ofGoogleSheet(url, mappingSheetName, debug)
        gs=GoogleSheet(url)
        gs.open([sheetName]) 
        lod=gs.asListOfDicts(sheetName)
        lodByPk,_dup=LOD.getLookup(lod,pkColumn)
        query=queries[entityName]
        propRow=query.propertiesByColumn[pkColumn]
        pk=propRow["PropertyName"]
        pkVarname=propRow["PropVarname"]
        pkType=propRow["Type"]
        valuesClause=query.getValuesClause(lodByPk.keys(),propVarname=pkVarname,propType=pkType,lang=lang)
        
        sparql=query.asSparql(filterClause=valuesClause,orderClause=f"ORDER BY ?{pkVarname}",pk=pk)
        return query,sparql
    
    @classmethod
    def ofGoogleSheet(cls,url:str,sheetName:str="Wikidata",debug:bool=False)->dict:
        '''
        create a dict of wikibaseQueries from the given google sheets row descriptions
        
        Args:
            url(str): the url of the sheet
            sheetName(str): the name of the sheet with the description
            debug(bool): if True switch on debugging
        '''
        gs=GoogleSheet(url)
        gs.open([sheetName])
        entityMapRows=gs.asListOfDicts(sheetName)
        return WikibaseQuery.ofMapRows(entityMapRows,debug=debug)
        
    @classmethod
    def ofMapRows(cls,entityMapRows:list,debug:bool=False):
        '''
        create a dict of wikibaseQueries from the given entityMap list of dicts
        
        Args:
            entityMapRows(list): a list of dict with row descriptions
            debug(bool): if True switch on debugging
        '''
        queries={}
        entityMapDict={}
        for row in entityMapRows:
            if "Entity" in row:
                entity=row["Entity"]
                if not entity in entityMapDict:
                    entityMapDict[entity]={}
                entityRows=entityMapDict[entity]
                if "PropertyName" in row:
                    propertyName=row["PropertyName"]
                    entityRows[propertyName]=row    
        if debug:
            pprint.pprint(entityMapDict)
        for entity in entityMapDict:
            wbQuery=WikibaseQuery.ofEntityMap(entity,entityMapDict[entity])
            queries[entity]=wbQuery
        return queries
    
    @classmethod
    def ofEntityMap(cls,entity:str,entityMap:dict):
        '''
        create a WikibaseQuery for the given entity and entityMap
        
        Args:
            entity(str): the entity name
            entityMap(dict): the entity property descriptions
        Returns:
            WikibaseQuery
        '''
        wbQuery=WikibaseQuery(entity)
        for row in entityMap.values():
            wbQuery.addPropertyFromDescriptionRow(row)
        return wbQuery
        
        
    