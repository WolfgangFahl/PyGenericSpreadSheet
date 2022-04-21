'''
Created on 2022-04-18

@author: wf
'''
from pathlib import Path
import json
import os
import re
#from wikidataintegrator import wdi_core, wdi_login
from wikibaseintegrator import wbi_core, wbi_login, wbi_datatype
from lodstorage.sparql import SPARQL
import pprint
import dateutil.parser

class Wikidata:
    '''
    wikidata access
    
    see http://learningwikibase.com/data-import/
    '''
    
    def __init__(self,baseurl,debug:bool=False):
        '''
        Constructor
        
        Args:
            baseurl(str): the baseurl of the wikibase to use
            debug(bool): if True output debug information
        ''' 
        self.baseurl=baseurl
        self.debug=debug
        self.apiurl=f"{self.baseurl}/w/api.php"
        pass
    
    def getCredentials(self):
        '''
        get my credentials
        
        from the wd npm command line tool
        '''
        user=None
        pwd=None
        home = str(Path.home())
        configFilePath=f"{home}/.config/wikibase-cli/config.json"
        if os.path.isfile(configFilePath):
            with open(configFilePath, mode="r") as f:
                wikibaseConfigJson = json.load(f)
                credentials=wikibaseConfigJson["credentials"]
                if not self.baseurl in credentials:
                    raise Exception(f"no credentials available for {self.baseurl}")
                credentialRow=credentials[self.baseurl]
                user=credentialRow["username"]
                pwd=credentialRow["password"]
                pass
        return user,pwd
            
    def login(self):
        '''
        login using the credentials taken via self.getCredentials
        '''
        user,pwd=self.getCredentials()
        if user is not None:
            self.login = wbi_login.Login(user=user, pwd=pwd, mediawiki_api_url=self.apiurl)
            
    def addItem(self,ist:list,label:str,description:str,lang:str="en",write:bool=True):
        '''
        Args:
            ist(list): item statements
            label(str): the english label
            description(str): the english description
            lang(str): the label language
            write(bool): if True do actually write
        '''
        wbPage=wbi_core.ItemEngine(data=ist,mediawiki_api_url=self.apiurl)
        wbPage.set_label(label, lang=lang)
        wbPage.set_description(description, lang=lang)
        if self.debug:
            pprint.pprint(wbPage.get_json_representation())
        if write:
            # return the identifier of the generated page
            return wbPage.write(self.login) # edit_summary=
        else:
            return None
            
    def getItemByName(self,itemName:str,itemType:str,lang:str="en"):
        '''
        get an item by Name
        
        Args:
            itemName(str): the item to look for
            itemType(str): the type of the item
            lang(str): the language of the itemName
        '''
        itemLabel=f'"{itemName}"@{lang}'
        sparqlQuery="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    
    SELECT ?item ?itemLabel
    WHERE {
      {
        ?item wdt:P31 wd:%s.
        ?item rdfs:label ?itemLabel.
        # short name
        ?item wdt:P1813 %s
        FILTER(LANG(?itemLabel)= "%s" )
      } UNION {
        ?item wdt:P31 wd:Q3624078.
        ?item rdfs:label ?itemLabel.
        FILTER(?itemLabel= %s )
      }
    }""" % (itemType,itemLabel,lang,itemLabel)
        endpointUrl="https://query.wikidata.org/sparql"
        sparql=SPARQL(endpointUrl)
        itemRows=sparql.queryAsListOfDicts(sparqlQuery)
        item=None
        if len(itemRows)>0:
            item=itemRows[0]["item"].replace("http://www.wikidata.org/entity/","")
        return item
            
    def addDict(self,row:dict,mapDict:dict,lang:str="en",write:bool=False,ignoreErrors:bool=False):
        '''
        add the given row mapping with the given map Dict
        
        Args:
            row(dict): the data row to add
            mapDict(dict): the mapping dictionary to use
            lang(str): the language for lookups
            write(bool): if True do actually write
            ignoreErrors(bool): if True ignore errors
        '''
        ist=[]
        errors={}
        for propId in mapDict.keys():
            propMap=mapDict[propId]
            column=propMap["Column"]
            colType=propMap["Type"]
            lookup=propMap["Lookup"]
            colValue=None
            try:
                if column:
                    if column in row:
                        colValue=row[column]
                else:
                    colValue=propMap["Value"]
                if colValue:
                    if lookup:
                        # ignore if the value is already a Wikibase Entity identifier of the form
                        # Q12345 ...
                        if not re.match(r"Q[0-9]+",colValue):
                            colValue=self.getItemByName(colValue, lookup, lang)
                if colValue and isinstance(colValue,str):
                    colValue=colValue.strip()
                if colValue:
                    if colType=="year":
                        yearString=f"+{colValue}-01-01T00:00:00Z"
                        ist.append(wbi_datatype.Time(yearString,prop_nr=propId,precision=9))
                    elif colType=="date":
                            dateValue = dateutil.parser.parse(colValue)
                            isoDate=dateValue.isoformat()
                            dateString=f"+{isoDate}Z"
                            ist.append(wbi_datatype.Time(dateString,prop_nr=propId,precision=11))
                    elif colType=="url":
                        ist.append(wbi_datatype.Url(value=colValue,prop_nr=propId))
                    elif colType=="extid":
                        ist.append(wbi_datatype.ExternalID(value=colValue,prop_nr=propId))
                    elif colType=="text":
                        ist.append(wbi_datatype.MonolingualText(text=colValue,prop_nr=propId))
                    else:
                        ist.append(wbi_datatype.ItemID(value=colValue,prop_nr=propId))
            except Exception as ex:
                errors[column]=ex
        label=row["label"]
        description=row["description"]
        qid=None
        if len(errors)==0 or ignoreErrors:
            qid=self.addItem(ist,label,description,write=write)
        return qid,errors
        
        
            
                