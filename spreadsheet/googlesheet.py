'''
Created on 2022-04-18

@author: wf
'''
import requests
from io import StringIO
import pandas as pd

class GoogleSheet(object):
    '''
    GoogleSheet Handling
    '''

    def __init__(self, url):
        '''
        Constructor
        '''
        self.url=url
        self.dfs={}
        
    def open(self,sheetNames):
        '''
        Args:
            sheets(list): a list of sheetnames
        '''
        self.sheetNames=sheetNames
        for sheetName in sheetNames:
            #csvurl=f"{self.url}/export?format=csv"
            csvurl=f"{self.url}/gviz/tq?tqx=out:csv&sheet={sheetName}"
            response=requests.get(csvurl)
            csvStr=response.content.decode('utf-8')
            self.dfs[sheetName]=pd.read_csv(StringIO(csvStr),keep_default_na=False)
        
    def fixRows(self,lod:list):
        """
        fix Rows by filtering unnamed columns and trimming
        column names
        """
        for row in lod:
            for key in list(row.keys()):
                if key.startswith("Unnamed"):
                    del row[key]
                trimmedKey=key.strip()
                if trimmedKey!=key:
                    value=row[key]
                    row[trimmedKey]=value
                    del row[key]
                    
    def asListOfDicts(self,sheetName):
        '''
        convert the given sheetName to a list of dicts
        
        Args:
            sheetName(str): the sheet to convert
        '''
        lod=self.dfs[sheetName].to_dict('records') 
        self.fixRows(lod)
        return lod
        