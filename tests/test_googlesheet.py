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

    def setUp(self, debug=True, profile=True):
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
