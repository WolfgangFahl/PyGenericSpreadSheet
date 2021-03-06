'''
Created on 2021-12-29

@author: wf
'''
import unittest
from tests.basetest import BaseTest
from spreadsheet.spreadsheet import SpreadSheetType

class TestSpreadsheet(BaseTest):
    '''
    test the spread sheet handling
    '''

    def setUp(self):
        BaseTest.setUp(self)
        pass


    def testFormat(self):
        '''
        test the different formats
        '''
        choices=SpreadSheetType.asSelectFieldChoices()
        debug=True
        if debug:
            print(choices)
        for stype in SpreadSheetType:
            if debug:
                print (f"{stype.name}:{stype.getPostfix()}:{stype.getMimeType()}:{stype.getName()}:{stype.getTitle()}")
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()