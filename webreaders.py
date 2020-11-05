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
    

class Authenticate(ntuple('Authenticate', 'username password')): 
    def __call__(self): return HTTPBasicAuth(self.username, self.password)


class RetryAdapter(ntuple('RetryAdapter', 'retries backoff httpcodes')): 
    def __new__(cls, retries=3, backoff=0.3, httpcodes=(500, 502, 504)): return super().__new__(cls, retries, backoff, httpcodes)
    def __call__(self): 
        retry = Retry(total=self.retries, read=self.retries, connect=self.retries, backoff_factor=self.backoff, status_forcelist=self.httpcodes)
        adapter = HTTPAdapter(max_retries=retry)
        return adapter     


class Headers(list):
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
              

class WebReader(object):   
    def __init__(self, *args, attempts=10, delay=3, **kwargs):
        self.__attempts, self.__delay = attempts, delay
        self.__retry = kwargs.get('retry', None)
        self.__authenticate = kwargs.get('authenticate', None)
        self.__headers = kwargs.get('headers', None)
        self.__lasttime = None

    def ready(self, currenttime): return currenttime - self.__lasttime  > self.__delay if self.__lasttime else True
    def wait(self, currenttime): return max([self.__delay - int(currenttime - self.__lasttime), 0]) if self.__lasttime else 0
    def record(self, currenttime): self.__lasttime = currenttime
    def sleep(self, waittime): time.sleep(waittime)

    def __call__(self, url, datatype, *args, **kwargs):
        for attempt in range(self.__attempts):
            try: headers = next(self.__headers)
            except TypeError: headers = self.__headers
            except AttributeError: headers = None
            try: return self.execute(url, datatype, *args, headers=headers, **kwargs)
            except RequestException: pass
        raise RequestException()
    
    def execute(self, url, datatype, *args, headers=None, proxy=None, **kwargs):
        with requests.Session() as session:
            if self.__retry is not None: 
                session.mount('http://', self.__retry())
                session.mount('https://', self.__retry())
            parms = {'headers':headers, 'proxies':{'http':str(proxy), 'https':str(proxy)}, 'auth':self.__authenticate()}
            if not self.ready(time.time()): self.sleep(self.wait(time.time()))
            response = session.get(str(url), **parms)
            self.record(time.time())
            if not response.status_code == requests.codes.ok: print('URL Request Failure:')
            else: print('URL Request Success:')  
            print(str(url), '\n')
            response.raise_for_status()
            data = self.parse(datatype, response)
        return data

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








