# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   Webreader Objects
@author: Jack Kirby Cook

"""

import os.path
import time
import requests
import json
import zipfile
import random
from abc import ABC, abstractmethod
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from requests.packages.urllib3.util.retry import Retry
from collections import namedtuple as ntuple

from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebReader', 'RetryAdapter', 'Authenticate', 'Headers']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""
   

class WebRequestError(Exception):
    def __str__(self): return "{}: {}".format(self.__class__.__name__, self.args[0].__class__.__name__)   

class MaxWebRequestAttemptError(WebRequestError): pass
class FailureWebRequestError(WebRequestError): pass


class Authenticate(ntuple('Authenticate', 'username password')): 
    def __repr__(self): return "{}(username='{}', password='{}')".format(self.__class__.__name__, *self)  
    def __call__(self): return HTTPBasicAuth(self.username, self.password)


class RetryAdapter(ntuple('RetryAdapter', 'retries backoff httpcodes')): 
    def __repr__(self): return "{}(retries={}, backoff={}, httpcodes={})".format(self.__class__.__name__, *self)
    def __new__(cls, retries=3, backoff=0.3, httpcodes=(500, 502, 504)): return super().__new__(cls, retries, backoff, httpcodes)
    def __call__(self): 
        retry = Retry(total=self.retries, read=self.retries, connect=self.retries, backoff_factor=self.backoff, status_forcelist=self.httpcodes)
        adapter = HTTPAdapter(max_retries=retry)
        return adapter     


class Headers(list):
    def __repr__(self): return "{}()".format(self.__class__.__name__, len(self))
    def __next__(self): return random.choice(self)
    def __init__(self, headers): 
        assert isinstance(headers, (list, tuple, set))
        assert len(headers) > 0
        super().__init__(headers)
        
    @classmethod
    def load(cls, file, limit=100):
        assert isinstance(limit, int)
        headers = []
        for header in cls.loading(file):
            if len(headers) >= limit: break
            if header['hardware_type'].lower() != 'computer': continue    
            if header['software_type'].lower() != 'browser -> web-browser': continue
            if header['software_name'].lower() != 'chrome': continue
            if header['operation_system'].lower() != 'windows': continue
            headers.append(header)
        return cls(headers)
        
    @staticmethod
    def loading(file):
        assert os.path.splitext(file)[-1] == 'zip'
        with zipfile.ZipFile(file) as zfile:
            with zfile.open(os.path.basename(file)) as jfile: 
                for header in jfile:
                    if hasattr(header, 'decode'): header = header.decode()
                    yield json.loads(header)
              

class WebReader(ABC):   
    def __init_sublcass__(cls, *args, webpage, **kwargs): 
        setattr(cls, 'WebPage', webpage)
       
    def __str__(self): return self.__class__.__name__
    def __repr__(self): 
        asstring = lambda kwargs, function: ', '.join(['='.join([key, function(value)]) for key, value in content.items()])
        content = {'attempts':self.__attempts, 'delay':self.__delay}
        objects = {attr:getattr(self, attr) for attr in ('retry', 'authenticate', 'headers') if hasattr(self, attr)}
        return "{}({}, {})".format(self.__class__.__name__, asstring(content, str), asstring(objects, repr))    
    
    def __init__(self, *args, attempts=10, delay=3, **kwargs):
        self.__attempts, self.__delay = attempts, delay
        try: self.retry = kwargs['retry']
        except KeyError: pass
        try: self.authenticate = kwargs['authenticate']
        except KeyError: pass
        try: self.headers = kwargs['headers']
        except KeyError: pass
        self.__lasttime = None

    def ready(self, currenttime): return currenttime - self.__lasttime  > self.__delay if self.__lasttime else True
    def wait(self, currenttime): return max([self.__delay - int(currenttime - self.__lasttime), 0]) if self.__lasttime else 0
    def record(self, currenttime): self.__lasttime = currenttime
    def sleep(self, waittime): time.sleep(waittime)
       
    def __call__(self, url, *args, **kwargs):
        try: yield from self.controller(url, *args, **kwargs)
        except MaxWebRequestAttemptError: raise FailureWebRequestError(self)       
    
    def controller(self, url, *args, attempt=0, **kwargs):
        try: 
            print("WebRequest: {}".format(self.__class__.__name__))
            print("Attempt: {}|{}".format(str(attempt+1), str(self.__attempts+1)))            
            parms, retry = self.setup(*args, **kwargs)
            session = self.start(parms, retry)        
            if not self.ready(time.time()): self.sleep(self.wait(time.time()))
            response = session.get(str(url), **parms)
            self.record(time.time())
            response.raise_for_status()
            self.stop(session)
            data = self.parse(self.datatype, response)
            page = self.Page(data, *args, **kwargs)
            yield from self.execute(page, *args, **kwargs)            
            print("WebRequest Success: {}".format(self.__class__.__name__), "\n")
        except RequestException as error:
            try: self.stop(session)
            except NameError: pass
            print("WebRequest Failure: {}".format(self.__class__.__name__))
            print(str(error), '\n')
            if attempt < self.__attempts: yield from self.controller(url, *args, attempt=attempt+1, **kwargs)
            else: raise MaxWebRequestAttemptError(attempt)
        
    def start(self, parms, retry=None):
        session = requests.Session() 
        if retry is not None: 
            session.mount('http://', self.__retry())
            session.mount('https://', self.__retry())
        return session
            
    def stop(self, session):
        pass
    
    def setup(self, *args, **kwargs):
        auth = self.getAuthenticate(*args, **kwargs)
        retry = self.getRetry(*args, **kwargs)
        headers = self.getHeaders(*args, **kwargs)
        parms = {'headers':headers, 'auth':auth, 'cookies':kwargs.get('cookies', None)}
        try: parms['Referer'] = kwargs['referer']
        except KeyError: pass
        parms = {key:value for key, value in parms.items() if value is not None}
        return parms, retry 
    
    def getAuthenticate(self, *args, **kwargs): return self.authenticate() if hasattr(self, 'authenticate') else None
    def getRetry(self, *args, **kwargs): return self.retry() if hasattr(self, 'retry') else None
    def getHeaders(self, *args, **kwargs):
        try: return next(self.headers)
        except TypeError: return self.headers
        except AttributeError: return None    

    @abstractmethod
    def execute(self, page, *args, **kwargs): pass

    @keydispatcher
    def parse(self, datatype, response): raise KeyError(datatype)
    @parse.register('html')
    def parseHTML(response): return response.text
    @parse.register('json')
    def parseJSON(response): return response.json()
    @parse.register('zip')
    def parseZIP(response): return response.content
    @parse.register('csv')
    def parseCSV(response): return response.content.decode('utf-8')








