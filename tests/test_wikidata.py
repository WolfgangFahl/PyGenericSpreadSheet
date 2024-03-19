"""
Created on 01.03.2024

@author: wf
"""
from ez_wikidata.wikidata import Wikidata
from lodstorage.lod import LOD

from spreadsheet.googlesheet import GoogleSheet
from tests.basetest import BaseTest


class TestWikidataWithGoogleSheet(BaseTest):
    """
    test wikidata handling via google sheets
    """

    def setUp(self, debug=False, profile=True):
        BaseTest.setUp(self, debug=debug, profile=profile)
        self.wd = Wikidata()

    def testAddItem(self):
        """
        test the wikidata access
        """
        # http://learningwikibase.com/data-import/
        # https://github.com/SuLab/scheduled-bots/blob/main/scheduled_bots/wikipathways/bot.py
        debug = self.debug
        debug = True
        url = "https://docs.google.com/spreadsheets/d/1AZ4tji1NDuPZ0gwsAxOADEQ9jz_67yRao2QcCaJQjmk"
        self.gs = GoogleSheet(url)
        spreadSheetNames = ["WorldPrayerDays", "Wikidata"]
        self.gs.open(spreadSheetNames)
        rows = self.gs.asListOfDicts("WorldPrayerDays")
        mapRows = self.gs.asListOfDicts("Wikidata")
        mapDict, _dup = LOD.getLookup(mapRows, "PropertyId", withDuplicates=False)
        # 1935
        row = rows[7]
        if self.debug:
            print(row)
            print(mapDict)

        # do not write anymore - the data has already been imported
        # write=not BaseTest.inPublicCI()
        write = False
        # if write:
        #    wd.login()
        wd_result = self.wd.addDict(row, mapDict, write=write)
        if len(wd_result.errors) > 0:
            print(wd_result.errors)
        self.assertEqual(0, len(wd_result.errors))
        # we didn't write so no item
        self.assertTrue(wd_result.qid is None)
        pass

    def testWikibaseQuery(self):
        """
        test wikibase Query handling
        """
        testcases = [
            (
                "Scholar",
                "Scholar",
                "WikidataMetadata",
                "https://docs.google.com/spreadsheets/d/10YQy1Obdtqw0sNTcaQxRrB0p-sKEzbxUcFtZPkUKz-g",
                1,
                "item",
                "item",
                """# 
# get Scholar records 
#  
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX schema: <http://schema.org/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?item ?itemLabel ?itemDescription

  ?family_name ?family_nameLabel
  ?given_name ?given_nameLabel
  ?official_website
  ?LinkedIn_personal_profile_ID ?LinkedIn_personal_profile_IDUrl
  ?ORCID_iD ?ORCID_iDUrl
  ?Google_Scholar_author_ID ?Google_Scholar_author_IDUrl
  ?GND_ID ?GND_IDUrl
  ?DBLP_author_ID ?DBLP_author_IDUrl
WHERE {
    ?item rdfs:label ?itemLabel. FILTER(LANG(?itemLabel) = "en")
    OPTIONAL {
        ?item schema:description ?itemDescription. FILTER(LANG(?itemDescription) = "en")
    }

  ?item wdt:P31 wd:Q5.
  OPTIONAL {
    ?item wdt:P734 ?family_name.
    ?family_name rdfs:label ?family_nameLabel.
    FILTER(LANG(?family_nameLabel) = "en")
  }
  OPTIONAL {
    ?item wdt:P735 ?given_name.
    ?given_name rdfs:label ?given_nameLabel.
    FILTER(LANG(?given_nameLabel) = "en")
  }
  OPTIONAL {
    ?item wdt:P856 ?official_website.
  }
  OPTIONAL {
    ?item wdt:P6634 ?LinkedIn_personal_profile_ID.
    wd:P6634 wdt:P1630 ?LinkedIn_personal_profile_IDFormatterUrl.
    BIND(IRI(REPLACE(?LinkedIn_personal_profile_ID, '^(.+)$', ?LinkedIn_personal_profile_IDFormatterUrl)) AS ?LinkedIn_personal_profile_IDUrl).
  }
  OPTIONAL {
    ?item wdt:P496 ?ORCID_iD.
    wd:P496 wdt:P1630 ?ORCID_iDFormatterUrl.
    BIND(IRI(REPLACE(?ORCID_iD, '^(.+)$', ?ORCID_iDFormatterUrl)) AS ?ORCID_iDUrl).
  }
  OPTIONAL {
    ?item wdt:P1960 ?Google_Scholar_author_ID.
    wd:P1960 wdt:P1630 ?Google_Scholar_author_IDFormatterUrl.
    BIND(IRI(REPLACE(?Google_Scholar_author_ID, '^(.+)$', ?Google_Scholar_author_IDFormatterUrl)) AS ?Google_Scholar_author_IDUrl).
  }
  OPTIONAL {
    ?item wdt:P227 ?GND_ID.
    wd:P227 wdt:P1630 ?GND_IDFormatterUrl.
    BIND(IRI(REPLACE(?GND_ID, '^(.+)$', ?GND_IDFormatterUrl)) AS ?GND_IDUrl).
  }
  OPTIONAL {
    ?item wdt:P2456 ?DBLP_author_ID.
    wd:P2456 wdt:P1630 ?DBLP_author_IDFormatterUrl.
    BIND(IRI(REPLACE(?DBLP_author_ID, '^(.+)$', ?DBLP_author_IDFormatterUrl)) AS ?DBLP_author_IDUrl).
  }

  VALUES(?item) {
  }.
}
ORDER BY ?item""",
            ),
            (
                "Event",
                "ACISP",
                "WikidataMapping",
                "https://docs.google.com/spreadsheets/d/16KURma_XUV68S6_VNWG-ESs-mPgbbAnnBNLwWlBnVFY",
                3,
                "short_name",
                "short name",
                """# 
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
  ?DBLP_event_ID ?DBLP_event_IDUrl
WHERE {
    ?item rdfs:label ?itemLabel. FILTER(LANG(?itemLabel) = "en")
    OPTIONAL {
        ?item schema:description ?itemDescription. FILTER(LANG(?itemDescription) = "en")
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
  OPTIONAL {
    ?item wdt:P10692 ?DBLP_event_ID.
    wd:P10692 wdt:P1630 ?DBLP_event_IDFormatterUrl.
    BIND(IRI(REPLACE(?DBLP_event_ID, '^(.+)$', ?DBLP_event_IDFormatterUrl)) AS ?DBLP_event_IDUrl).
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
ORDER BY ?short_name""",
            ),
        ]
        debug = self.debug
        # debug=True
        index = 0
        for (
            entityName,
            name,
            sheetName,
            url,
            expected_queries,
            pk,
            pk_label,
            expected,
        ) in testcases:
            # debug=True
            queries = GoogleSheet.toWikibaseQuery(url, sheetName, debug)
            self.assertEqual(expected_queries, len(queries))
            if debug:
                print(queries.keys())
            gs = GoogleSheet(url)
            gs.open([entityName])
            itemRows = gs.asListOfDicts(entityName)
            itemsByLabel, _dup = LOD.getLookup(itemRows, "label")
            itemsQuery = queries[entityName]
            if debug:
                print(itemsByLabel.keys())
            # filterClause=eventQuery.inFilter(eventsByLabel.keys(),"short_name","en")
            filterClause = itemsQuery.getValuesClause(
                itemsByLabel.keys(), propVarname=pk, lang="en"
            )
            sparql = itemsQuery.asSparql(
                filterClause=filterClause,
                orderClause=f"ORDER BY ?{pk}",
                pk=f"{pk_label}",
            )
            index += 1
            if debug:
                print(f"Testcase {index}")
                print(sparql)
            self.assertEqual(expected, sparql)
