# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   Webreader Objects
@author: Jack Kirby Cook

"""

import os.path
import json
from itertools import cycle
import random
import requests
from requests.exceptions import RequestException
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.util.retry import Retry
from collections import namedtuple as ntuple
from collections import OrderedDict as ODict
import time

from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebReader', 'RetryAdapter', 'Proxy', 'ProxyPool', 'Authenticate', 'Headers', 'HeadersPool']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class Headers(ODict): 
    def __next__(self): return self
    @classmethod
    def fromjson(cls, file):
        if not os.path.isfile(file): raise FileNotFoundError(file)
        with open(file, 'r') as infile: content = json.load(infile)
        assert isinstance(content, dict)
        return cls([(key, value) for key, value in content.items()])  
  
class HeadersPool(object):
    def __iter__(self): return self
    def __next__(self): return random.choice(self.__pool)
    def __init__(self, *items):
        assert all([isinstance(item, Headers) for item in items])
        self.__pool = items
       
    @classmethod
    def fromjson(cls, file):
        if not os.path.isfile(file): raise FileNotFoundError(file)
        with open(file, 'r') as infile: contents = json.load(infile)
        assert isinstance(contents, list)
        assert all([isinstance(content, dict) for content in contents])
        return cls([Headers([(key, value) for key, value in content.items()]) for content in contents])

    
class Proxy(ntuple('Proxy', 'host port')): 
    httpproxyformat = 'http://{host}:{port}'
    def __str__(self): return self.httpproxyformat.format(**self._asdict())
    def __next__(self): return self

class ProxyPool(object):
    def __iter__(self): return self
    def __next__(self): return next(self.__pool)
    def __init__(self, *items):
        assert all([isinstance(item, Proxy) for item in items])
        self.__pool = cycle(items)


class Authenticate(ntuple('Authenticate', 'username password')): 
    def __call__(self): return HTTPBasicAuth(self.username, self.password)

class RetryAdapter(ntuple('RetryAdapter', 'retries backoff httpcodes')): 
    def __new__(cls, retries=3, backoff=0.3, httpcodes=(500, 502, 504)): return super().__new__(cls, retries, backoff, httpcodes)
    def __call__(self): 
        retry = Retry(total=self.retries, read=self.retries, connect=self.retries, backoff_factor=self.backoff, status_forcelist=self.httpcodes)
        adapter = HTTPAdapter(max_retries=retry)
        return adapter     


class WebReader(object):   
    def __init__(self, *args, attempts=10, delay=3, **kwargs):
        self.__attempts, self.__delay = attempts, delay
        self.__retry = kwargs.get('retry', None)
        self.__authenticate = kwargs.get('authenticate', None)
        self.__headers = kwargs.get('headers', None)
        self.__proxy = kwargs.get('proxy', None)
        self.__lasttime = None

    def ready(self, currenttime): return currenttime - self.__lasttime  > self.__delay if self.__lasttime else True
    def wait(self, currenttime): return max([self.__delay - int(currenttime - self.__lasttime), 0]) if self.__lasttime else 0
    def record(self, currenttime): self.__lasttime = currenttime
    def sleep(self, waittime): time.sleep(waittime)

    def getheaders(self): return next(self.__headers) if isinstance(self.__headers, HeadersPool) else self.__headers
    def getproxy(self): return next(self.__proxy) if isinstance(self.__proxy, ProxyPool) else self.__proxy

    def __call__(self, url, datatype, *args, **kwargs):
        for attempt in range(self.__attempts):
            headers, proxy = self.getheaders(), self.getproxy()
            try: return self.execute(url, datatype, *args, headers=headers, proxy=proxy, **kwargs)
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
















