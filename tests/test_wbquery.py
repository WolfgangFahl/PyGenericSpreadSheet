'''
Created on 2022-04-30

@author: wf
'''
from tests.basetest import BaseTest

from spreadsheet.wbquery import WikibaseQuery
from spreadsheet.googlesheet import GoogleSheet
from lodstorage.lod import LOD

class TestWikibaseQuery(BaseTest):
    '''
    test the Wikibase Query
    '''
    
    def testWikibaseQuery(self):
        '''
        test wikibase Query handling
        '''
        url="https://docs.google.com/spreadsheets/d/16KURma_XUV68S6_VNWG-ESs-mPgbbAnnBNLwWlBnVFY"
        debug=self.debug
        debug=True
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
  ?GND_ID
  ?describedAt
  ?official_website
  ?WikiCFP_event_ID
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
  }
  OPTIONAL {
    ?item wdt:P973 ?describedAt.
  }
  OPTIONAL {
    ?item wdt:P856 ?official_website.
  }
  OPTIONAL {
    ?item wdt:P5124 ?WikiCFP_event_ID.
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
       
        