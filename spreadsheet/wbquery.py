'''
Created on 2022-04-30

@author: wf
'''
from lodstorage.trulytabular import WikidataProperty
from lodstorage.lod import LOD
from spreadsheet.wikidata import Wikidata
from spreadsheet.googlesheet import GoogleSheet
import pprint

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
        self.properties={}
        
    def addPropertyFromDescriptionRow(self,row):
        '''
        add a property from the given row
        
        Args:
            row(dict): the row to add
        '''
        self.properties[row['PropertyName']]=row
        
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
        
    def asSparql(self,filterClause:str=None,orderClause:str=None,lang:str="en"):
        '''
        get the sparqlQuery for this query optionally applying a filterClause
        
        Args:
            filterClause(str): a filter to be applied (if any)
            orderClause(str): an orderClause to be applied (if any)
            lang(str): the language to be used for labels
        '''
        sparql=f"""# 
# get {self.entity} records 
#  
SELECT ?item ?itemLabel
"""
        for propName,row in self.properties.items():
            propVar=propName.replace(" ","_")
            propValue=row["Value"]
            if not propValue:
                sparql+=f"\n  ?{propVar}"
        sparql+="""\nWHERE {
  ?item rdfs:label ?itemLabel.
  FILTER(LANG(?itemLabel) = "%s")
""" % lang
        for propName,row in self.properties.items():
            propVar=propName.replace(" ","_")
            propValue=row["Value"]
            propId=row["PropertyId"]
            if propValue:
                sparql+=f"\n  ?item wdt:{propId} wd:{propValue}."
            else:
                sparql+=f"\n  OPTIONAL {{ ?item wdt:{propId} ?{propVar}. }}"
        if filterClause is not None:
                sparql+=f"\n{filterClause}"        
        sparql+="\n}"
        if orderClause is not None:
            sparql+=f"\n{orderClause}"
        return sparql
            

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
        
        
    