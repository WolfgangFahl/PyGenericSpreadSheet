import unittest
import uuid
from datetime import datetime

from wikibaseintegrator.datatypes import URL, ExternalID, Item, Time, String, MonolingualText

from tests.basetest import BaseTest
from spreadsheet.wikidata import PropertyMapping, UrlReference, WdDatatype, Wikidata
from spreadsheet.googlesheet import GoogleSheet
from lodstorage.lod import LOD

class TestWikidata(BaseTest):
    '''
    test the Wikidata access
    '''

    def setUp(self,debug=False,profile=True):
        super().setUp(debug, profile)
        self.wd = Wikidata("https://www.wikidata.org",debug=debug)
    
    def testItemLookup(self):
        '''
        lookup items
        '''
        debug=True
        wd=Wikidata("https://www.wikidata.org",debug=True)
        country=wd.getItemByName("USA","Q3624078")
        if debug:
            print(country)
        self.assertEqual("Q30",country)
        ecir=wd.getItemByName("ECIR","Q47258130")
        if debug:
            print(ecir)
        self.assertEqual("Q5412436",ecir)
        
    def testAddItem(self):
        '''
        test the wikidata access
        '''
        # http://learningwikibase.com/data-import/
        # https://github.com/SuLab/scheduled-bots/blob/main/scheduled_bots/wikipathways/bot.py
        debug=self.debug
        #debug=True
        url="https://docs.google.com/spreadsheets/d/1AZ4tji1NDuPZ0gwsAxOADEQ9jz_67yRao2QcCaJQjmk"
        self.gs=GoogleSheet(url)   
        spreadSheetNames=["WorldPrayerDays","Wikidata"] 
        self.gs.open(spreadSheetNames)  
        rows=self.gs.asListOfDicts("WorldPrayerDays")
        mapRows=self.gs.asListOfDicts("Wikidata")
        mapDict,_dup=LOD.getLookup(mapRows, "PropertyId", withDuplicates=False)
        # 1935
        row=rows[7]
        if self.debug:
            print(row)
            print(mapDict)
       
        # do not write anymore - the data has already been imported
        #write=not BaseTest.inPublicCI()
        write=False
        #if write:
        #    wd.login()
        qid, errors = self.wd.addDict(row, mapDict,write=write)
        if len(errors)>0:
            print(errors)
        self.assertEqual(0,len(errors))
        # we didn't write so no item
        self.assertTrue(qid is None)
        pass

    def test_convert_to_claim(self):
        """
        tests convert_to_claim
        """
        acronym = PropertyMapping(column="acronym", propertyId="P1813", propertyName="short name", propertyType=WdDatatype.text)
        homepage = PropertyMapping(column="homepage", propertyId="P856", propertyName="official website", propertyType=WdDatatype.url)
        inception = PropertyMapping(column="inception", propertyId="P571", propertyName="inception", propertyType=WdDatatype.year)
        start_time = PropertyMapping(column="startTime", propertyId="P580", propertyName="start time", propertyType=WdDatatype.date)
        issn = PropertyMapping(column="issn", propertyId="P236", propertyName="ISSN", propertyType=WdDatatype.extid)
        country = PropertyMapping(column="country", propertyId="P17", propertyName="country", propertyType=WdDatatype.itemid)
        volume = PropertyMapping(column="volume", propertyId="P478", propertyName="volume", propertyType=WdDatatype.string)
        test_params = [  # (value, expected value, expected  type, property mapping)
            ("AAAI", {'text': 'AAAI', 'language': 'en'}, MonolingualText, acronym),
            ("http://ceur-ws.org/", "http://ceur-ws.org/", URL, homepage),
            ("1995", {'time': '+1995-01-01T00:00:00Z', 'before': 0, 'after': 0, 'precision': 9, 'timezone': 0, 'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'}, Time, inception),
            ("1995-05-04", {'time': '+1995-05-04T00:00:00Z', 'before': 0, 'after': 0, 'precision': 11, 'timezone': 0, 'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'}, Time,start_time),
            ("1613-0073", "1613-0073", ExternalID, issn),
            ("Q30", {'entity-type': 'item', 'numeric-id': 30, 'id': 'Q30'}, Item, country),
            ("1", "1", String, volume),
            ("A", "A", String, volume),
            (1, "1", String, volume),
        ]
        for params in test_params:
            with self.subTest("test claim generation", params=params):
                value, expected_value, expected_type, pm = params
                claim = self.wd.convert_to_claim(value, pm)
                self.assertTrue(isinstance(claim, expected_type))
                self.assertEqual(expected_value, claim.mainsnak.datavalue["value"])

    def test_is_wikidata_item_id(self):
        """
        tests is_wikidata_item_id
        """
        test_params = [("human", False), ("Q5", True), ("P17", False)]
        for param in test_params:
            with self.subTest(param=param):
                value, expected = param
                actual = self.wd.is_wikidata_item_id(value)
                self.assertEqual(expected, actual)

    def test_is_wikidata_property_id(self):
        """
        tests is_wikidata_item_id
        """
        test_params = [("country", False), ("P17", True), ("Q5", False)]
        for param in test_params:
            with self.subTest(param=param):
                value, expected = param
                actual = self.wd.is_wikidata_property_id(value)
                self.assertEqual(expected, actual)

    def test_sanitize_label(self):
        """
        tests sanitize_label
        """
        test_params = [("Hello World", 8, None, "Hello..."), ("A"*255, None, None, "A"*247+"..."), ("P17", 2, "!", "P!")]
        for param in test_params:
            with self.subTest(param=param):
                label, limit, postfix, expected = param
                actual = self.wd.sanitize_label(label, limit, postfix)
                self.assertEqual(expected, actual)

    def test_get_record(self):
        """
        tests get_record
        ToDo: add more test cases
        """
        expected = {"P31": "Q1143604", "P1813": "JIST-WP 2017", "P577": datetime(2017, 11, 20).date(), "P973": "http://ceur-ws.org/Vol-2000/"}
        actual = self.wd.get_record("Q113543868", expected.keys(), include_label=False, include_description=False)
        self.assertDictEqual(expected, actual)

    @unittest.skipIf(BaseTest.inPublicCI(), "Tests creating and modifying items. To run in CI setup credentials")
    def test_add_record(self):
        """
        tests add_record by creating an item in test.wikidata.org adding property values.
        Also tests adding property values to existing items.
        """
        wd = Wikidata(baseurl="https://test.wikidata.org")
        wd.loginWithCredentials()
        property_mappings = [
            WikidataSandboxProperties.TEXT,
            WikidataSandboxProperties.ITEM,
            WikidataSandboxProperties.DATE,
            WikidataSandboxProperties.YEAR,
            WikidataSandboxProperties.URL,
            WikidataSandboxProperties.EXT_ID,
            PropertyMapping(column="dateQualifier", propertyId="P96927", propertyName="year sandbox property",propertyType=WdDatatype.year, qualifierOf="date")
        ]
        record = {
            "label": str(uuid.uuid4()),
            "description": "test item added to test correctness of api",
            "text": "test",
            "date": datetime.now().date(),
            "dateQualifier": datetime.now().year,
            "item": "Q377",
            "url": "https://example.org",
            "year": 2000,
            "identifier": str(uuid.uuid4())
        }

        # test creating an item
        qid, _ = wd.add_record(record=record, property_mappings=property_mappings, write=True)
        actual = wd.get_record(qid, property_mappings=property_mappings)
        self.assertDictEqual(record, actual)

        # test modifying an item (not overwriting existing value)
        record["year"] = [record["year"], 2022]
        qid, _ = wd.add_record({"year":2022}, property_mappings=property_mappings, item_id=qid, write=True)
        actual = wd.get_record(qid, property_mappings=property_mappings)
        self.assertDictEqual(record, actual)

    @unittest.skipIf(BaseTest.inPublicCI(), "Tests creating and modifying items. To run in CI setup credentials")
    def test_addDict(self):
        """
        test addDict
        """
        wd = Wikidata(baseurl="https://test.wikidata.org")
        wd.loginWithCredentials()
        legacy_mappings = [{"Entity": "proceedings", "Column": None, "PropertyName": "instanceof", "PropertyId": "P95201",
            "Value": "Q377", "Type": "itemid", "Qualifier": None, "Lookup": None},
            {"Entity": "proceedings", "Column": "short name", "PropertyName": "short name", "PropertyId": "P95227",
                "Type": "text", "Qualifier": None, "Lookup": ""},
            {"Entity": "proceedings", "Column": "pubDate", "PropertyName": "publication date", "PropertyId": "P95226",
                "Type": "date", "Qualifier": None, "Lookup": ""},
            {"Entity": "proceedings", "Column": "url", "PropertyName": "described at URL", "PropertyId": "P95231",
                "Type": "url", "Qualifier": None, "Lookup": ""},
            {"Entity": "proceedings", "Column": "language of work or name", "PropertyName": "language of work or name",
                "PropertyId": "P82", "Type": "itemid", "Qualifier": "url", "Lookup": ""},
            {"Entity": "proceedings", "Column": "urn", "PropertyName": "URN-NBN", "PropertyId": "P95232",
                "Type": "extid", "Qualifier": None, "Lookup": ""}]
        mappings = [
            PropertyMapping("instanceof", "instanceof", "P95201", propertyType=WdDatatype.itemid, value="Q1143604"),
            PropertyMapping("short name", "short name", "P95227", propertyType=WdDatatype.text),
            PropertyMapping("pubDate", "publication date", "P95226", propertyType=WdDatatype.date),
            PropertyMapping("url", "described at URL", "P95231", propertyType=WdDatatype.url),
            PropertyMapping("language of work or name", "language of work or name", "P82", propertyType=WdDatatype.itemid, qualifierOf="url"),
            PropertyMapping("urn", "URN-NBN", "P95232", propertyType=WdDatatype.extid)
        ]
        record = {
            "label": str(uuid.uuid4()),
            "short name": "test",
            "pubDate": datetime.now().date(),
            "url": "http://example.org",
            "language of work or name": "Q377",
            "urn": str(uuid.uuid4())
        }
        mapDict, _ = LOD.getLookup(legacy_mappings, "PropertyId")
        qid, _ = wd.addDict(record, mapDict=mapDict, write=True)
        actual = wd.get_record(qid, mappings)
        record["instanceof"] = "Q377"
        self.assertEqual(record, actual)

    @unittest.skipIf(BaseTest.inPublicCI(), "Tests creating and modifying items. To run in CI setup credentials")
    def test_value_lookup(self):
        """
        tests the lookup of wikidata ids from label value
        Note: Currently the lookup is always against wikidata. Changing this requires to adapt this test accordingly.
        """
        lookup_type, label, expected_qid = ("Q3336843", "Scotland", "Q22")  # type qid, label, qid
        mappings = [
            PropertyMapping("item", "wikibase-item sandbox property", "P95201", propertyType=WdDatatype.itemid, valueLookupType=lookup_type)
        ]
        record = {"label": str(uuid.uuid4()), "item": label}
        expected_record = {"label": record["label"], "item": expected_qid}

        wd = Wikidata(baseurl="https://test.wikidata.org")
        wd.loginWithCredentials()
        qid, _ = wd.add_record(record, mappings, write=True)
        actual = wd.get_record(qid, mappings)
        self.assertDictEqual(expected_record, actual)

    def test_get_datatype_of_property(self):
        """
        tests get_datatype_of_property
        """
        test_params = [("P31", "WikibaseItem"), ("31", "WikibaseItem"), (31, "WikibaseItem"), ("P580", "Time"),
                       ("P1813", "Monolingualtext"), ("P856", "Url"), ("P8978", "ExternalId")]
        for param in test_params:
            with self.subTest(param=param):
                pid, expected = param
                actual = self.wd.get_datatype_of_property(pid)
                self.assertEqual(expected, actual)

    def test_get_wddatatype_of_property(self):
        """
        tests get_datatype_of_property
        """
        test_params = [("P31", WdDatatype.itemid), ("31", WdDatatype.itemid), (31, WdDatatype.itemid),
                       ("P580", WdDatatype.date), ("P1813", WdDatatype.text), ("P856", WdDatatype.url),
                       ("P8978", WdDatatype.extid), ("P478", WdDatatype.string)]
        for param in test_params:
            with self.subTest(param=param):
                pid, expected = param
                actual = self.wd.get_wddatatype_of_property(pid)
                self.assertEqual(expected, actual)

    def test_UrlReference(self):
        """
        tests UrlReference
        """
        test_params = [("http://example.org", "2022-01-01")]
        for param in test_params:
            with self.subTest(param=param):
                url, date = param
                reference = UrlReference(url, date)
                json = reference.get_json()
                json_str = str(json)
                self.assertIn("P854", json_str)
                self.assertIn("P813", json_str)
                self.assertIn(url, json_str)
                self.assertIn(date, json_str)


class TestPropertyMapping(BaseTest):
    """
    tests PropertyMapping
    """

    def test_from_record(self):
        """
        tests from_record
        """
        test_params = [
            ("languageOfWork", "language of work or name", "P407", "itemid", "official website", "")
        ]
        for params in test_params:
            col, name, p_id, p_type, qualifier, lookup = params
            record = {
                "column": col,
                "propertyName": name,
                "propertyType": WdDatatype[p_type],
                "propertyId": p_id,
                "qualifierOf": qualifier,
                "valueLookupType": lookup
            }
            legacy_record = {
                "Column": col,
                "PropertyName": name,
                "PropertyId": p_id,
                "Type": p_type,
                "Qualifier": qualifier,
                "Lookup": lookup
            }
            for i, rec in enumerate([record, legacy_record]):
                mode = "legacy" if i == 1 else ""
                with self.subTest(f"test parsing from {mode} record", rec=rec):
                    mapping = PropertyMapping.from_record(rec)
                    for key, expected_value in record.items():
                        actual_value = getattr(mapping, key)
                        self.assertEqual(expected_value, actual_value)

    def test_is_qualifier(self):
        """
        tests id_qualifier
        """
        positive_case = PropertyMapping(column="volume", propertyId="P478", propertyName="volume", propertyType=WdDatatype.string, qualifierOf="part of the series")
        negative_case = PropertyMapping(column="acronym", propertyId="P1813", propertyName="short name", propertyType=WdDatatype.text)
        self.assertTrue(positive_case.is_qualifier())
        self.assertFalse(negative_case.is_qualifier())


class WikidataSandboxProperties:
    """
    Wikidata sandbox items to be used to add and modify items in test.wikidata.org
    """
    TEXT = PropertyMapping(column="text", propertyId="P95227", propertyName="monolingualtext sandbox property", propertyType=WdDatatype.text)
    DATE = PropertyMapping(column="date", propertyId="P95226", propertyName="time sandbox property", propertyType=WdDatatype.date)
    ITEM = PropertyMapping(column="item", propertyId="P95201", propertyName="wikibase-item sandbox property",propertyType=WdDatatype.itemid)
    URL = PropertyMapping(column="url", propertyId="P95231", propertyName="url sandbox property",propertyType=WdDatatype.url)
    YEAR = PropertyMapping(column="year", propertyId="P96927", propertyName="year sandbox property",propertyType=WdDatatype.year)
    EXT_ID = PropertyMapping(column="identifier", propertyId="P95232", propertyName="external-id sandbox property", propertyType=WdDatatype.extid)
