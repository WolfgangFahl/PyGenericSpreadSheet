"""
Created on 2021-12-29

@author: wf
"""
from spreadsheet.spreadsheet import SpreadSheetType
from tests.basetest import BaseTest

class TestSpreadsheet(BaseTest):
    """
    test the spread sheet handling
    """
    
    def setUp(self, debug=False, profile=True):
        BaseTest.setUp(self, debug=debug, profile=profile)

    def testFormat(self):
        """
        test the different formats
        """
        choices = SpreadSheetType.asSelectFieldChoices()
        debug = self.debug
        if debug:
            print(choices)
        for stype in SpreadSheetType:
            if debug:
                print(
                    f"{stype.name}:{stype.getPostfix()}:{stype.getMimeType()}:{stype.getName()}:{stype.getTitle()}"
                )
        pass

