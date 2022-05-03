'''
Created on 2022-04-30

@author: wf
'''
from tests.basetest import BaseTest

from spreadsheet.wbquery import WikibaseQuery
from spreadsheet.googlesheet import GoogleSheet
from lodstorage.lod import LOD
from lodstorage.sparql import SPARQL
import pprint

class TestWikibaseQuery(BaseTest):
    '''
    test the Wikibase Query
    '''
    
    def setUp(self, debug=False, profile=True):
        BaseTest.setUp(self, debug=debug, profile=profile)
        self.endpointUrl="https://query.wikidata.org/sparql"
    
    def testSingleQuoteHandlingIssue4(self):
        '''
        see https://github.com/WolfgangFahl/PyGenericSpreadSheet/issues/4
        '''
        debug=self.debug
        #debug=True
        url="https://docs.google.com/spreadsheets/d/1AZ4tji1NDuPZ0gwsAxOADEQ9jz_67yRao2QcCaJQjmk"
        sheetName="WorldPrayerDays"
        entityName="WorldPrayerDay"
        _query,sparqlQuery=WikibaseQuery.sparqlOfGoogleSheet(url,sheetName,entityName,pkColumn="Theme",debug=debug)
        if debug:
            print(sparqlQuery)
        wpdlist=self.getSparqlResult(sparqlQuery, debug)
        if wpdlist:
            self.assertTrue(len(wpdlist)>90)
        self.assertTrue("God\\'s Wisdom" in sparqlQuery)
    
    def getContinentQuery(self,pkColumn:"item",debug:bool=False):
        url="https://docs.google.com/spreadsheets/d/1ciz_hvLpPlSm_Y30HapuERBOyRBh-NC4UFxKOBU49Tw"
        sheetName="Continent"
        entityName=sheetName
        wbQuery,sparqlQuery=WikibaseQuery.sparqlOfGoogleSheet(url,sheetName,entityName,pkColumn=pkColumn,debug=debug)
        clist=self.getSparqlResult(sparqlQuery, debug)
        return wbQuery,sparqlQuery,clist
            
    def getSparqlResult(self,sparqlQuery,debug:bool=False):
        rows=None
        if debug:
            print(sparqlQuery)
        if self.endpointUrl:
            sparql=SPARQL(self.endpointUrl)
            rows=sparql.queryAsListOfDicts(sparqlQuery)
            if debug:
                pprint.pprint(rows)
        return rows
        
    def testSupportFormatterUrisForExternalIdentifiersIssue5(self):
        '''
        see https://github.com/WolfgangFahl/PyGenericSpreadSheet/issues/5
        
        support formatter URIs for external identifiers #5 
        '''
        debug=self.debug
        pkColumn="LoCId"
        #debug=True
        _wbQuery,sparqlQuery,clist=self.getContinentQuery(pkColumn,debug=debug)
        self.assertTrue(len(clist)>=5)
        self.assertTrue("BIND(IRI(REPLACE(" in sparqlQuery)
        
    def testAllowItemsAsValuesInGetValuesClause(self):
        '''
        allow items as values in getValuesClause 
        see https://github.com/WolfgangFahl/PyGenericSpreadSheet/issues/6
        '''
        pkColumn="LoCId"
        debug=self.debug
        #debug=True
        wbQuery,clist=self.getContinentQuery(pkColumn,debug=debug)
        self.assertTrue(len(clist)>=5)
        continentsByItem,_dup=LOD.getLookup(clist,"item")
        if debug:   
            pprint.pprint(continentsByItem)
        pkProp="item"    
        valuesClause=wbQuery.getValuesClause(continentsByItem.keys(),pkProp,propType="")
        sparqlQuery=wbQuery.asSparql(filterClause=valuesClause,orderClause=f"ORDER BY ?{pkProp}",pk=pkProp)
        continentRows=self.getSparqlResult(sparqlQuery, debug)
        if self.debug:
            print(continentRows)     
        self.assertTrue("wd:Q15" in sparqlQuery)
        
     
    def testWikibaseQuery(self):
        '''
        test wikibase Query handling
        '''
        url="https://docs.google.com/spreadsheets/d/16KURma_XUV68S6_VNWG-ESs-mPgbbAnnBNLwWlBnVFY"
        debug=self.debug
        #debug=True
        queries=WikibaseQuery.ofGoogleSheet(url,debug=debug)
        self.assertEqual(3,len(queries))
        if debug:
            print(queries.keys())
        gs=GoogleSheet(url)
        gs.open(["Event"]) 
        eventRows=gs.asListOfDicts("Event")
        eventsByLabel,_dup=LOD.getLookup(eventRows,"label")
        eventQuery=queries["Event"]
        if debug:
            print(eventsByLabel.keys())
        #filterClause=eventQuery.inFilter(eventsByLabel.keys(),"short_name","en")
        filterClause=eventQuery.getValuesClause(eventsByLabel.keys(),lang="en")
        sparql=eventQuery.asSparql(filterClause=filterClause,orderClause="ORDER BY ?short_name",pk="short name")
        if debug:
            print(sparql)
        expected="""# 
# get Event records 
#  
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX schema: <http://schema.org/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?item ?itemLabel ?itemDescription

  ?part_of_the_series ?part_of_the_seriesLabel
  ?series_ordinal
  ?short_name
  ?title
  ?country ?countryLabel
  ?location ?locationLabel
  ?start_time
  ?end_time
  ?GND_ID ?GND_IDUrl
  ?describedAt
  ?official_website
  ?WikiCFP_event_ID ?WikiCFP_event_IDUrl
WHERE {
  ?item rdfs:label ?itemLabel.
  FILTER(LANG(?itemLabel) = "en")
  OPTIONAL { 
    ?item schema:description ?itemDescription.
    FILTER(LANG(?itemDescription) = "en")
  }

  ?item wdt:P31 wd:Q2020153.
  OPTIONAL {
    ?item wdt:P179 ?part_of_the_series.
    ?part_of_the_series rdfs:label ?part_of_the_seriesLabel.
    FILTER(LANG(?part_of_the_seriesLabel) = "en")
  }
  OPTIONAL {
    ?item wdt:P1545 ?series_ordinal.
  }
    ?item wdt:P1813 ?short_name.
  OPTIONAL {
    ?item wdt:P1476 ?title.
  }
  OPTIONAL {
    ?item wdt:P17 ?country.
    ?country rdfs:label ?countryLabel.
    FILTER(LANG(?countryLabel) = "en")
  }
  OPTIONAL {
    ?item wdt:P276 ?location.
    ?location rdfs:label ?locationLabel.
    FILTER(LANG(?locationLabel) = "en")
  }
  OPTIONAL {
    ?item wdt:P580 ?start_time.
  }
  OPTIONAL {
    ?item wdt:P582 ?end_time.
  }
  OPTIONAL {
    ?item wdt:P227 ?GND_ID.
    wd:P227 wdt:P1630 ?GND_IDFormatterUrl.
    BIND(IRI(REPLACE(?GND_ID, '^(.+)$', ?GND_IDFormatterUrl)) AS ?GND_IDUrl).
  }
  OPTIONAL {
    ?item wdt:P973 ?describedAt.
  }
  OPTIONAL {
    ?item wdt:P856 ?official_website.
  }
  OPTIONAL {
    ?item wdt:P5124 ?WikiCFP_event_ID.
    wd:P5124 wdt:P1630 ?WikiCFP_event_IDFormatterUrl.
    BIND(IRI(REPLACE(?WikiCFP_event_ID, '^(.+)$', ?WikiCFP_event_IDFormatterUrl)) AS ?WikiCFP_event_IDUrl).
  }

  VALUES(?short_name) {
  ( 'ACISP 1996'@en )
  ( 'ACISP 1997'@en )
  ( 'ACISP 1998'@en )
  ( 'ACISP 1999'@en )
  ( 'ACISP 2000'@en )
  ( 'ACISP 2001'@en )
  ( 'ACISP 2002'@en )
  ( 'ACISP 2003'@en )
  ( 'ACISP 2004'@en )
  ( 'ACISP 2005'@en )
  ( 'ACISP 2006'@en )
  ( 'ACISP 2007'@en )
  ( 'ACISP 2008'@en )
  ( 'ACISP 2009'@en )
  ( 'ACISP 2010'@en )
  ( 'ACISP 2011'@en )
  ( 'ACISP 2012'@en )
  ( 'ACISP 2013'@en )
  ( 'ACISP 2014'@en )
  ( 'ACISP 2015'@en )
  ( 'ACISP 2016'@en )
  ( 'ACISP 2017'@en )
  ( 'ACISP 2018'@en )
  ( 'ACISP 2019'@en )
  ( 'ACISP 2020'@en )
  ( 'ACISP 2021'@en )
  }.
}
ORDER BY ?short_name""" 
        self.assertEqual(expected,sparql)
       
        