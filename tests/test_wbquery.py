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
        filterClause=eventQuery.inFilter(eventsByLabel.keys(),"short_name","en")
        sparql=eventQuery.asSparql(filterClause=filterClause,orderClause="ORDER BY ?short_name")
        if debug:
            print(sparql)
        expected="""# 
# get Event records 
#  
SELECT ?item ?itemLabel

  ?part_of_the_series
  ?series_ordinal
  ?short_name
  ?title
  ?country
  ?location
  ?start_time
  ?end_time
  ?GND_ID
  ?describedAt
  ?official_website
  ?WikiCFP_event_ID
WHERE {
  ?item rdfs:label ?itemLabel.
  FILTER(LANG(?itemLabel) = "en")

  ?item wdt:P31 wd:Q2020153.
  OPTIONAL { ?item wdt:P179 ?part_of_the_series. }
  OPTIONAL { ?item wdt:P1545 ?series_ordinal. }
  OPTIONAL { ?item wdt:P1813 ?short_name. }
  OPTIONAL { ?item wdt:P1476 ?title. }
  OPTIONAL { ?item wdt:P17 ?country. }
  OPTIONAL { ?item wdt:P276 ?location. }
  OPTIONAL { ?item wdt:P580 ?start_time. }
  OPTIONAL { ?item wdt:P582 ?end_time. }
  OPTIONAL { ?item wdt:P227 ?GND_ID. }
  OPTIONAL { ?item wdt:P973 ?describedAt. }
  OPTIONAL { ?item wdt:P856 ?official_website. }
  OPTIONAL { ?item wdt:P5124 ?WikiCFP_event_ID. }

  FILTER(?short_name IN(
    'ACISP 1996'@en,
    'ACISP 1997'@en,
    'ACISP 1998'@en,
    'ACISP 1999'@en,
    'ACISP 2000'@en,
    'ACISP 2001'@en,
    'ACISP 2002'@en,
    'ACISP 2003'@en,
    'ACISP 2004'@en,
    'ACISP 2005'@en,
    'ACISP 2006'@en,
    'ACISP 2007'@en,
    'ACISP 2008'@en,
    'ACISP 2009'@en,
    'ACISP 2010'@en,
    'ACISP 2011'@en,
    'ACISP 2012'@en,
    'ACISP 2013'@en,
    'ACISP 2014'@en,
    'ACISP 2015'@en,
    'ACISP 2016'@en,
    'ACISP 2017'@en,
    'ACISP 2018'@en,
    'ACISP 2019'@en,
    'ACISP 2020'@en,
    'ACISP 2021'@en
  )).
}
ORDER BY ?short_name"""
        self.assertEqual(expected,sparql)
       
        