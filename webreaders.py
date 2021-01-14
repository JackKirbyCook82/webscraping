# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   Webreader Objects
@author: Jack Kirby Cook

"""

import os.path
import requests
import json
import zipfile
import random
from lxml import html
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from collections import namedtuple as ntuple

from utilities.dispatchers import clskey_singledispatcher as keydispatcher

from webscraping.webdata import EmptyWebDataError, RefusalError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebReader', 'Retrys', 'Authenticate', 'UserAgents', 'Headers']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""
   

class WebRequestError(Exception):
    def __str__(self): return "{}: {}".format(self.__class__.__name__, self.args[0].__class__.__name__)   

class MaxWebRequestAttemptError(WebRequestError): pass
class FailureWebRequestError(WebRequestError): pass


class Authenticate(ntuple('Authenticate', 'username password')): 
    def __repr__(self): return "{}(username='{}', password='{}')".format(self.__class__.__name__, *self)  
    def __call__(self): return HTTPBasicAuth(self.username, self.password)


class Retrys(ntuple('Retrys', 'retries backoff httpcodes')): 
    def __repr__(self): return "{}(retries={}, backoff={}, httpcodes={})".format(self.__class__.__name__, *self)
    def __new__(cls, retries=3, backoff=0.3, httpcodes=(500, 502, 504)): return super().__new__(cls, retries, backoff, httpcodes)
    def __call__(self): 
        retry = Retry(total=self.retries, read=self.retries, connect=self.retries, backoff_factor=self.backoff, status_forcelist=self.httpcodes)
        adapter = HTTPAdapter(max_retries=retry)
        return adapter     


class Headers(object):
    accept_language = 'en-gb'
    accept_encoding = 'br, gzip, deflate'
    accept = 'test/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'

    def __repr__(self): return "{}(useragents={}, referer='{}')".format(self.__class__.__name__, repr(self.__useragents), self.__referer)
    def __next__(self): return {**self.useragent, **self.referer, **self.accepts}
    def __init__(self, useragents, *args, referer='http://www.google.com', **kwargs):
        self.__useragents = useragents
        self.__referer = referer
    
    @property
    def useragent(self): return {'User-Agent':next(self.__useragents)}
    @property
    def accepts(self): return {'Accept-Language':self.accept_language, 'Accept-Enconding':self.accept_encoding, 'Accept':self.accept}
    @property
    def referer(self): return {'Referer':self.__referer}


class UserAgents(list):
    def __repr__(self): return "{}(size={})".format(self.__class__.__name__, len(self))
    def __next__(self): return random.choice(list(self))
    def __init__(self, useragents): 
        assert isinstance(useragents, (list, tuple, set))
        assert len(useragents) > 0
        super().__init__(list(useragents))

    @classmethod
    def load(cls, file, limit=100):
        assert isinstance(limit, int)
        useragents = []
        for useragent in cls.loading(file):
            if len(useragents) >= limit: break
            if useragent['hardware_type'].lower() != 'computer': continue    
            if useragent['software_type'].lower() != 'browser -> web-browser': continue
            if useragent['software_name'].lower() != 'chrome': continue
            if useragent['operating_system'].lower() != 'windows': continue   
            useragents.append(useragent['user_agent'])
        return cls(useragents)
   
    @staticmethod
    def loading(file):
        directory, file = os.path.dirname(file), os.path.basename(file)
        try: filename, filecomp, fileext = str(file).split('.')
        except ValueError: filename, fileext = str(file).split('.') 
        try: 
            zfile = zipfile.ZipFile(os.path.join(directory, '.'.join([filename, filecomp])))
            with zfile.open('.'.join([filename, fileext])) as xfile:
                for useragent in xfile:
                    if hasattr(useragent, 'decode'): useragent = useragent.decode()
                    yield json.loads(useragent)
            zfile.close()        
        except NameError: 
            with open(os.path.join(directory, '.'.join([filename, fileext]))) as zfile:
                for useragent in xfile:
                    if hasattr(useragent, 'decode'): useragent = useragent.decode()
                    yield json.loads(useragent)                      
                

class WebReader(object):   
    def __init_subclass__(cls, *args, webpage, datatype, **kwargs): 
        setattr(cls, 'WebPage', webpage)
        setattr(cls, 'datatype', datatype)
       
    def __str__(self): return self.__class__.__name__
    def __repr__(self): 
        content = {attr:repr(getattr(self, attr)) for attr in ('retrys', 'authenticate', 'headers') if hasattr(self, attr)}
        content['attempts'] = self.__attempts
        return "{}({})".format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))    
    
    def __init__(self, *args, attempts=5, **kwargs):
        self.__attempts = attempts
        try: self.retrys = kwargs['retrys']
        except KeyError: pass
        try: self.authenticate = kwargs['authenticate']
        except KeyError: pass
        try: self.headers = kwargs['headers']
        except KeyError: pass
       
    def __call__(self, url, *args, **kwargs):
        try: yield from self.controller(url, *args, **kwargs)
        except MaxWebRequestAttemptError: raise FailureWebRequestError(self)       
    
    def controller(self, url, *args, attempt=0, **kwargs):
        try: 
            print("WebRequest: {}\n{}".format(self.__class__.__name__, str(url))) 
            print("Attempt: {}|{}".format(str(attempt+1), str(self.__attempt+1)))                      
            parms, retrys = self.setup(*args, **kwargs)
            session = self.start(parms, retrys)        
            response = session.get(str(url), **parms)
            response.raise_for_status()
            data = self.parse(self.datatype, response)
            webpage = self.WebPage(url, data, *args, **kwargs)
            yield from webpage(*args, **kwargs)   
            self.stop(session)
            print("WebRequest Success: {}".format(self.__class__.__name__))
        except (EmptyWebDataError, RefusalError) as error:
            try: self.stop(session)
            except NameError: pass
            print("WebRequest Failure: {}".format(self.__class__.__name__))
            print(str(error))
            if attempt < self.__attempts: yield from self.controller(url, *args, attempt=attempt+1, **kwargs)
            else: raise MaxWebRequestAttemptError(attempt)  
            
        
    def start(self, parms, retrys=None):
        session = requests.Session() 
        if retrys is not None: 
            session.mount('http://', retrys())
            session.mount('https://', retrys())
        return session
            
    def stop(self, session):
        pass
    
    def setup(self, *args, **kwargs):
        auth = self.getAuthenticate(*args, **kwargs)
        retrys = self.getRetrys(*args, **kwargs)
        headers = self.getHeaders(*args, **kwargs)
        parms = {'headers':headers, 'auth':auth, 'cookies':kwargs.get('cookies', None)}
        try: parms['Referer'] = kwargs['referer']
        except KeyError: pass
        parms = {key:value for key, value in parms.items() if value is not None}
        return parms, retrys
    
    def getAuthenticate(self, *args, **kwargs): return self.authenticate() if hasattr(self, 'authenticate') else None
    def getRetrys(self, *args, **kwargs): return self.retrys() if hasattr(self, 'retry') else None
    def getHeaders(self, *args, **kwargs):
        if isinstance(self.headers, Headers): return next(self.headers)
        elif isinstance(self.headers, dict): return self.headers
        elif isinstance(self.headers, type(None)): return self.headers
        else: raise TypeError(type(self.headers))


    @keydispatcher
    def parse(self, datatype, response): raise KeyError(datatype)
    @parse.register('html')
    def parseHTML(self, response): return html.fromstring(response.content)
    @parse.register('json')
    def parseJSON(self, response): return response.json()









