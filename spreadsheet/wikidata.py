'''
Created on 2022-04-18

@author: wf
'''
import datetime
import typing
from dataclasses import dataclass
from enum import auto, Enum
from pathlib import Path
import json
import os
import re
import traceback
from typing import List, Union
from wikibaseintegrator.datatypes import BaseDataType, URL, ExternalID, Item, Time, String, MonolingualText
from wikibaseintegrator.models import Claim, Reference, Snak
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login, WikibaseIntegrator
from lodstorage.sparql import SPARQL
import pprint
import dateutil.parser
from wikibaseintegrator.wbi_enums import WikibaseDatePrecision

from spreadsheet.version import Version


class Wikidata:
    '''
    wikidata access
    
    see http://learningwikibase.com/data-import/
    '''
    TEST_WD_URL = "https://test.wikidata.org"
    WD_URL = "https://www.wikidata.org"
    
    def __init__(self,baseurl,debug:bool=False):
        '''
        Constructor
        
        Args:
            baseurl(str): the baseurl of the wikibase to use
            debug(bool): if True output debug information
        '''
        if baseurl is None:
            baseurl = self.WD_URL
        self.baseurl=baseurl
        self.debug=debug
        self.apiurl=f"{self.baseurl}/w/api.php"
        self.login=None
        self.user=None
        self._wbi = None

    @property
    def wbi(self) -> WikibaseIntegrator:
        """
        WikibaseIntegrator
        """
        if self._wbi is None or (self.login is not None and self._wbi.login is None):
            wbi_config['USER_AGENT'] = f'{Version.name}/{Version.version} (https://www.wikidata.org/wiki/User:{self.user})'
            wbi_config['MEDIAWIKI_API_URL'] = self.apiurl
            self._wbi = WikibaseIntegrator(login=self.login)
        return self._wbi

    @wbi.setter
    def wbi(self, wbi: typing.Union[WikibaseIntegrator, None]):
        """
        set the WikibaseIntegrator
        """
        self._wbi = wbi
    
    def getCredentials(self) -> (str, str):
        """
        get my credentials https://test.wikidata.org/wiki/Property:P370

        from the wd npm command line tool

        Throws:
            Exception: if no credentials are available for the baseurl

        Returns:
            (username, password) of the account assigned to the baseurl
        """
        user=None
        pwd=None
        home = str(Path.home())
        configFilePath=f"{home}/.config/wikibase-cli/config.json"
        if os.path.isfile(configFilePath):
            with open(configFilePath, mode="r") as f:
                wikibaseConfigJson = json.load(f)
                credentials=wikibaseConfigJson["credentials"]
                credentialRecord = credentials.get(self.baseurl, None)
                if self.baseurl == self.TEST_WD_URL and self.baseurl not in credentials and self.WD_URL in credentials:
                    credentialRecord = credentials.get(self.WD_URL)
                if credentialRecord is None:
                    raise Exception(f"no credentials available for {self.baseurl}")
                user=credentialRecord["username"]
                pwd=credentialRecord["password"]
        return user,pwd
            
    def loginWithCredentials(self, user: str = None, pwd: str = None):
        """
        login using the given credentials or credentials
        retrieved via self.getCredentials

        Args:
            user(str): the username
            pwd(str): the password
        """
        if user is None:
            user,pwd=self.getCredentials()       
            
        if user is not None:
            self.login = wbi_login.Login(user=user, password=pwd, mediawiki_api_url=self.apiurl)
            if self.login:
                self.user=user
            
    def logout(self):
        '''
        log the user out again
        '''
        self.user=None
        self.login=None
        self.wbi = None

    def getItemByName(self,itemName:str,itemType:str,lang:str="en"):
        '''
        get an item by Name
        ToDo: Needs to be reworked as always WDQS is used as endpoint even if a different one is defined
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
                ?item wdt:P31 wd:%s.
                ?item rdfs:label ?itemLabel.
                FILTER(?itemLabel= %s )
              }
            }""" % (itemType,itemLabel,lang,itemType,itemLabel)
        endpointUrl="https://query.wikidata.org/sparql"
        sparql=SPARQL(endpointUrl)
        itemRows=sparql.queryAsListOfDicts(sparqlQuery)
        item=None
        if len(itemRows)>0:
            item=itemRows[0]["item"].replace("http://www.wikidata.org/entity/","")
        return item
            
    def addDict(
            self,
            row:dict,
            mapDict:dict,
            itemId: Union[str, None] = None,
            lang:str="en",
            write:bool=False,
            ignoreErrors:bool=False
    ) -> (str, dict):
        """
        ToDo: Refactor to use add_record
        add the given row mapping with the given map Dict

        Args:
            row(dict): the data row to add
            mapDict(dict): the mapping dictionary to use
            itemId: wikidata id of the item the data should be added to. If None a new item is created
            lang(str): the language for lookups
            write(bool): if True do actually write
            ignoreErrors(bool): if True ignore errors

        Returns:
            (qid, errors)
        """
        mappings = []
        for record in mapDict.values():
            mapping = PropertyMapping.from_record(record)
            mappings.append(mapping)
        return self.add_record(row, mappings, item_id=itemId, lang=lang, write=write, ignore_errors=ignoreErrors)

    def get_record(
            self,
            item_id:str,
            property_mappings: Union[List[str], List['PropertyMapping']],
            include_label: bool = True,
            include_description: bool = True
    ) -> dict:
        """
        Get the properties form the given item
        Args:
            item_id: id of the item to get the data from
            property_mappings: list of property values to extract
            include_label:
            include_description:

        Returns:
            dict with the property values
        """
        item = self.wbi.item.get(item_id)
        lang = "en"
        record = dict()
        if include_label and item.labels.get(lang) is not None:
            record["label"] = item.labels.get(lang).value
        if include_description and item.descriptions.get(lang) is not None:
            record["description"] = item.descriptions.get(lang).value
        qualifier_lookup = PropertyMapping.get_qualifier_lookup(property_mappings)
        pms = []
        for pm in property_mappings:
            if not isinstance(pm, PropertyMapping) or not pm.is_qualifier():
                pms.append(pm)
        for prop in pms:
            prop_id = prop
            if isinstance(prop, PropertyMapping):
                prop_id = prop.propertyId
            claims = item.claims.get(prop_id)
            prop_label = prop_id
            if isinstance(prop, PropertyMapping):
                prop_label = prop.column
            values = []
            for claim in claims:
                value = self._get_claim_value(claim)
                values.append(value)
                if isinstance(prop, PropertyMapping) and prop.column in qualifier_lookup:
                    for qualifier_pm in qualifier_lookup[prop.column]:
                        qualifier_claims = claim.qualifiers.get(qualifier_pm.propertyId)  # ToDo: not fail-safe
                        qualifier_values = []
                        for qualifier_claim in qualifier_claims:
                            qualifier_values.append(self._get_claim_value(qualifier_claim))
                        record[qualifier_pm.column] = qualifier_values[0] if len(qualifier_values) == 1 else qualifier_values
            if len(values) == 1:
                record[prop_label] = values[0]
            else:
                record[prop_label] = values
        return record

    def _get_claim_value(self, claim: Union[Claim, Snak]) -> typing.Any:
        """
        Get the raw value of the claim without the metadata
        Args:
            claim: claim

        Returns:
            raw value of the claim
        """
        value = None
        snak = claim
        if isinstance(claim, Claim):
            snak = claim.mainsnak
        raw_value = snak.datavalue.get("value")
        datatype = snak.datatype
        if datatype == "wikibase-item":
            value = raw_value.get("id", None)
        elif datatype == "monolingualtext":
            value = raw_value.get("text")
        elif datatype == "string":
            value = raw_value
        elif datatype == "url":
            value = raw_value
        elif datatype == "time":
            value = dateutil.parser.parse(raw_value.get("time")[1:])
            precision = raw_value.get("precision")
            if precision == 11:
                value = value.date()
            elif precision == 9:
                value = value.year
        elif datatype == "external-id":
            value = raw_value
        else:
            pass
        return value

    def add_record(
            self,
            record: dict,
            property_mappings: List['PropertyMapping'],
            item_id: Union[str, None] = None,
            lang: str = "en",
            write: bool = False,
            ignore_errors: bool = False,
            summary: str = None,
            reference: Reference = None
    ) -> (str, dict):
        """
        add the given row mapping with the given map Dict

        Args:
            record(dict): the data row to add
            property_mappings(list): the mapping dictionary to use
            item_id: wikidata id of the item the data should be added to. If None a new item is created
            lang(str): the language for lookups
            write(bool): if True do actually write
            ignore_errors(bool): if True ignore errors
            summary: summary of the item edits
            reference: reference to add to all claims

        Returns:
            (qId, errors)
        """
        claims = []
        errors = dict()
        qualifier_lookup = PropertyMapping.get_qualifier_lookup(property_mappings)
        properties = [pm for pm in property_mappings if not pm.is_qualifier()]
        for prop in properties:
            qualifier_mappings = qualifier_lookup.get(prop.column, None)
            prop_claims, claim_errors = self._get_claims_for_property(record, prop, qualifier_mappings, reference, lang)
            errors = {**errors, **claim_errors}
            claims.extend(prop_claims)
        label = self.sanitize_label(record.get("label", None))
        description = record.get("description", None)
        item = self.get_or_create_item(item_id)
        item.add_claims(claims)
        if label:
            item.labels.set(language=lang, value=label)
        if description:
            item.descriptions.set(language=lang, value=description)
        if write:
            if len(errors) == 0 or ignore_errors:
                item = item.write(summary=summary)
        return item.id, errors

    def _get_claims_for_property(
            self,
            record: dict,
            prop_mapping: 'PropertyMapping',
            qualifier_mappings: Union[List['PropertyMapping'], None],
            reference: Reference,
            lang: str
    ) -> (List[Claim], dict):
        """
        Get the claims that can be derived from the given property mapping and record.
        Generates a claim with its qualifiers and reference from the given record and mapping.
        If the record value of the property is a list multiple claims are generated

        Args:
            record: data record
            prop_mapping: property definition for the claims that should be generated from the given record
            qualifier_mappings: descriptions of the qualifiers of the property
            reference: reference of the statement
            lang: language to use

        Returns:
            list of statements
        """
        claims = []
        value = self.get_prop_value(record, prop_mapping, lang)
        values = value if isinstance(value, list) else [value]
        errors = dict()
        for value in values:
            claim = None
            try:
                claim = self.convert_to_claim(value=value, pm=prop_mapping)
            except Exception as ex:
                errors[prop_mapping.column] = ex
                if self.debug:
                    print(traceback.format_exc())
            if claim is not None:
                # add reference
                if reference is not None:
                    claim.references.add(reference)
                # add qualifier
                if qualifier_mappings is not None:
                    qualifier_errors = self._add_qualifier_to_claim(record, claim, qualifier_mappings, lang)
                    errors = {**errors, **qualifier_errors}
            if claim is not None:
                claims.append(claim)
        return claims, errors

    def _add_qualifier_to_claim(
            self,
            record: dict,
            claim: Claim,
            qualifier_mappings: List['PropertyMapping'],
            lang: str
    ) -> dict:
        """
        add the qualifiers to the given claim
        Args:
            record:
            claim: add qualifiers to this claim
            qualifier_mappings: list of PropertyMappings of the qualifiers

        Returns:
            dict of occurred errors with the qualifier column as key. If no error occurs an empty dict is returned
        """
        errors = dict()
        for qualifier_pm in qualifier_mappings:
            qualifier_value = self.get_prop_value(record, qualifier_pm, lang)
            if qualifier_value is None:
                continue
            else:
                try:
                    qualifier = self.convert_to_claim(qualifier_value, qualifier_pm)
                    claim.qualifiers.add(qualifier)
                except Exception as ex:
                    errors[qualifier_pm.column] = ex
                    if self.debug:
                        print(traceback.format_exc())
        return errors

    def get_or_create_item(self, item_id:str):
        """
        Get or create the requested wikidata item
        Args:
            item_id: item to retrieve if None create a new item
        """
        if item_id is None:
            item = self.wbi.item.new()
        else:
            item = self.wbi.item.get(item_id)
        return item

    def get_prop_value(self, record: dict, pm: 'PropertyMapping', lang: str) -> typing.Any:
        """
        Retrieve the property value from the record and prepare the value if necessary
        Args:
            record: record containing the property data
            pm: property mapping
            lang: language to use

        Returns:
            value of the property from the record
        """
        value = record.get(pm.column, None)
        if value is None:
            value = pm.value
        if value and pm.valueLookupType and not self.is_wikidata_item_id(value):
            # find the wikidata item id of value
            value = self.getItemByName(value, pm.valueLookupType, lang)
        if value and isinstance(value, str):
            value = value.strip()
        return value

    def convert_to_claim(self, value, pm: 'PropertyMapping') -> BaseDataType:
        """
        Convert the given value to a corresponding wikidata claim
        Args:
            value: value of the claim
            pm: information about the property statement ot generate

        Raises:
            Exception: if property datatype is unknown or not supported

        Returns:
            BaseDataType
        """
        if value is None:
            return None
        if pm.propertyType is None:
            pm.propertyType = self.get_wddatatype_of_property(pm.propertyId)
        if pm.propertyType is WdDatatype.year:
            yearString = f"+{value}-01-01T00:00:00Z"
            claim = Time(yearString, prop_nr=pm.propertyId, precision=WikibaseDatePrecision.YEAR)
        elif pm.propertyType is WdDatatype.date:
            claim = self.get_date_claim(value, pm.propertyId)
        elif pm.propertyType is WdDatatype.extid:
            claim = ExternalID(value=value, prop_nr=pm.propertyId)
        elif pm.propertyType is WdDatatype.string:
            claim = String(value=str(value), prop_nr=pm.propertyId)
        elif pm.propertyType is WdDatatype.text:
            claim = MonolingualText(text=str(value), prop_nr=pm.propertyId)
        elif pm.propertyType is WdDatatype.url:
            claim = URL(value=value, prop_nr=pm.propertyId)
        elif pm.propertyType is WdDatatype.itemid:
            claim = Item(value=value, prop_nr=pm.propertyId)
        else:
            raise Exception(f"({pm.propertyType}) unknown or not supported datatype")
        return claim

    @staticmethod
    def get_date_claim(date: Union[str, datetime.date, datetime.datetime], prop_nr: Union[str, int]) -> Claim:
        """
        Get the data claim for the given date and property id
        Args:
            date: date value
            prop_nr: id of the property

        Returns:
            Claim
        """
        if isinstance(date, datetime.date):
            date_value = datetime.datetime.combine(date, datetime.time())
        elif isinstance(date, datetime.datetime):
            date_value = date
        elif isinstance(date, str):
            date_value = dateutil.parser.parse(date)
        else:
            raise Exception(f"Value '{date}' can not be parsed to date")
        isoDate = date_value.isoformat()
        date_string = f"+{isoDate}Z"
        claim = Time(date_string, prop_nr=prop_nr, precision=WikibaseDatePrecision.DAY)
        return claim

    @staticmethod
    def is_wikidata_item_id(value: str) -> bool:
        """
        Returns true if the given value is a wikidata item id
        """
        return bool(re.fullmatch(r"Q[0-9]+", value))

    @staticmethod
    def is_wikidata_property_id(value: str) -> bool:
        """
        Returns true if the given value is a wikidata property id
        """
        return bool(re.fullmatch(r"P[0-9]+", value))

    @staticmethod
    def sanitize_label(label: str, limit: int = None, postfix: str = None) -> str:
        """
        sanitize given label by ensuring it is not too long
        Args:
            label: label to sanitize
            limit: max length of the label

        Returns:
            sanitized label
        """
        if limit is None:
            limit = 250
        if postfix is None:
            postfix = "..."
        if label is not None and len(label) > limit:
            label = label[:limit-len(postfix)] + postfix
        return label

    def get_datatype_of_property(self, property_id: Union[str, int]) -> Union[str, None]:
        """
        Get the datatype of the given property
        Args:
            property_id: id of the property e.g. P31 or 31

        Returns:
            datatype of the property of None if no datatype is defined
        """
        if isinstance(property_id, int) or not property_id.startswith("P"):
            property_id = f"P{property_id}"
        query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wikibase: <http://wikiba.se/ontology#>
            
            SELECT Distinct ?o
            WHERE {
              wd:%s wikibase:propertyType ?o.
            }
        """ % (property_id)
        endpointUrl = "https://query.wikidata.org/sparql"
        sparql = SPARQL(endpointUrl)
        itemRows = sparql.queryAsListOfDicts(query)
        wikibase_prefix = "http://wikiba.se/ontology#"
        types = []
        for record in itemRows:
            types.append(record.get("o")[len(wikibase_prefix):])
        if len(types) > 1:
            print("Property has more than one type! please check")
        elif len(types) == 0:
            print("Property has no defined datatype! please check")
            return None
        return types[0]

    def get_wddatatype_of_property(self, property_id: Union[str, int]) -> 'WdDatatype':
        """
        Get the datatype of the given property
        Args:
            property_id: id of the property e.g. P31 or 31

        Returns:
            WdDatatype of the property of None if no datatype is defined
        """
        property_type = self.get_datatype_of_property(property_id)
        return WdDatatype.get_by_wikibase(property_type)


class WdDatatype(Enum):
    """
    Supported wikidata datatypes
    """
    itemid = auto()
    year = auto()
    date = auto()
    extid = auto()
    text = auto()
    url = auto()
    string = auto()

    @classmethod
    def _missing_(cls, value):
        """
        default datatype
        """
        return cls.text

    @classmethod
    def get_by_wikibase(cls, property_type: str) -> Union['WdDatatype', None]:
        """
        Get WdDatatype by the corresponding wikibase datatype
        Args:
            property_type: wikibase name of the type

        Returns:
            WdDatatype
        """
        wikibase_map = {
            "WikibaseItem": cls.itemid,
            "Time": cls.date,
            "Monolingualtext": cls.text,
            "String": cls.string,
            "ExternalId": cls.extid,
            "Url": cls.url
        }
        return wikibase_map.get(property_type, None)


@dataclass
class PropertyMapping:
    """
    wikidata property mapping
    """
    column: Union[str, None]  # if None, the value is used
    propertyName: str
    propertyId: str
    propertyType: WdDatatype
    qualifierOf: str = None
    valueLookupType: typing.Any = None  # type (instance of/P31) of the property value → used to lookup the qid if property value if value is not already a qid
    value: typing.Any = None  # set this value for the property

    @classmethod
    def from_record(cls, record: dict) -> 'PropertyMapping':
        """
        initialize PropertyMapping from the given record
        Args:
            record: property mapping information

        Returns:
            PropertyMapping
        """
        legacy_lookup = {
            "Column": "column",
            "PropertyName": "propertyName",
            "PropertyId": "propertyId",
            "Type": "propertyType",
            "Qualifier": "qualifierOf",
            "Lookup": "valueLookupType",
            "Value": "value"
        }
        record = record.copy()
        for i in range(len(record)):
            key = list(record.keys())[i]
            if key in legacy_lookup:
                record[legacy_lookup[key]] = record[key]
        # handle missing property type
        if record.get("propertyType", None) in [None, ""]:
            if record.get("valueLookupType", None) not in [None, ""]:
                record["propertyType"] = WdDatatype.itemid
            elif record.get("value", None) not in [None, ""]:
                record["propertyType"] = WdDatatype.itemid
        if record.get("propertyType", None) is not None and not isinstance(record.get("propertyType"), WdDatatype):
            record["propertyType"] = WdDatatype[record.get("propertyType", None)]
        mapping = PropertyMapping(
                column=record.get("column", None),
                propertyName=record.get("propertyName", None),
                propertyId=record.get("propertyId", None),
                propertyType=record.get("propertyType", None),
                qualifierOf=record.get("qualifierOf", None),
                valueLookupType=record.get("valueLookupType", None),
                value=record.get("value", None)
        )
        return mapping

    def is_qualifier(self) -> bool:
        """
        Returns true if the property mapping describes a qualifier
        """
        is_qualifier = not (self.qualifierOf is None or self.qualifierOf == "")
        return is_qualifier

    @classmethod
    def get_qualifier_lookup(cls, properties: List['PropertyMapping']) -> typing.Dict[str, List['PropertyMapping']]:
        """
        Get a lookup for a property and all its qualifie
        Args:
            properties: property mappings to generate the lookup from
         Returns:
             dict as property qualifier lookup
        """
        res = dict()
        for pm in properties:
            if not isinstance(pm, PropertyMapping):
                continue
            if pm.qualifierOf is None or pm.qualifierOf == "":
                continue
            else:
                if pm.qualifierOf in res:
                    res[pm.qualifierOf].append(pm)
                else:
                    res[pm.qualifierOf] = [pm]
        return res


class UrlReference(Reference):
    """
    Reference consisting of
        reference URL (P854)
        retrieved (P813)
    """

    def __init__(self, url, date: Union[str, datetime.date, datetime.datetime, None] = None):
        """
        constructor
        Args:
            url: reference URL
            date: retrieved at
        """
        super().__init__()
        self.url = url
        if date is None:
            date = datetime.date.today()
        self.date = date
        self.add(URL(value=self.url, prop_nr="P854"))
        self.add(Wikidata.get_date_claim(date, prop_nr="P813"))
