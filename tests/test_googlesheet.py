"""
Created on 2024-03-19

@author: wf
"""
from spreadsheet.googlesheet import GoogleSheet
from tests.basetest import BaseTest
import json

class TestGoogleSheet(BaseTest):
    """
    test the GoogleSheet handling
    """

    def setUp(self, debug=False, profile=True):
        BaseTest.setUp(self, debug=debug, profile=profile)

    def test_google_sheet(self):
        """ 
        test reading a google sheet
        """
        url = "https://docs.google.com/spreadsheets/d/1-Vf2LA8BXdXvF5lTLvyJ0mYmaffjK6Lh4hb1wbwfjcY/edit#gid=0"
        gs = GoogleSheet(url)
        if not gs.credentials:
            print("can't get GoogleSheet API - no credentials available")
        sheet_dict = gs.open()
        if self.debug:
            print(f"found {len(sheet_dict)} sheets")
        self.assertEqual(1,len(sheet_dict))
        if self.debug:
            print(json.dumps(sheet_dict,indent=2,default=str))
        self.assertTrue("website_generators" in sheet_dict)
        for _key,lod in sheet_dict.items():
            prefix=None
            for record in lod:
                name=record["generator"]
                row_prefix=name.split(" ")[0]
                if not prefix or row_prefix!=prefix:
                    count_sum=0
                prefix=row_prefix
                count=record["count"]
                count_sum+=count
                groupcount=record["groupcount"]
                self.assertEqual(groupcount,count_sum)
                    
