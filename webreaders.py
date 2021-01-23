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
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from collections import namedtuple as ntuple

from webscraping.webdata import EmptyWebDataError
from webscraping.webpages import EmptyWebPageError, RefusalError, BadRequestError

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
    accept_language = 'en-US,en;q=0.9'
    accept_encoding = 'gzip, deflate, br'
    accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    cachecontrol = 'max-age=0'

    def __repr__(self): return "{}(useragents={})".format(self.__class__.__name__, repr(self.__useragents))
    def __call__(self): return {**self.useragent, **self.accepts, 'cache-control':self.cachecontrol}
    def __next__(self): return {**self.useragent, **self.accepts, 'cache-control':self.cachecontrol}
    def __init__(self, useragents, *args, **kwargs): self.__useragents = useragents
    
    @property
    def useragent(self): return {'User-Agent':next(self.__useragents)}
    @property
    def accepts(self): return {'Accept-Language':self.accept_language, 'Accept-Enconding':self.accept_encoding, 'Accept':self.accept}


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
    def __init_subclass__(cls, *args, page, **kwargs): 
        setattr(cls, 'WebPage', page)
       
    def __str__(self): return self.__class__.__name__
    def __repr__(self): 
        content = {attr:repr(getattr(self, attr)) for attr in ('retrys', 'authenticate', 'headers') if hasattr(self, attr)}
        content['attempts'] = str(self.__attempts)
        return "{}({})".format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))    
    
    def __init__(self, *args, attempts=3, wait=5, **kwargs):
        self.__attempts = attempts
        try: self.retrys = kwargs['retrys']
        except KeyError: pass
        try: self.authenticate = kwargs['authenticate']
        except KeyError: pass
        try: self.headers = kwargs['headers']
        except KeyError: pass
        self.__wait = wait
       
    def __call__(self, *args, **kwargs):
        try: yield from self.controller(*args, **kwargs)
        except MaxWebRequestAttemptError: raise FailureWebRequestError(self)       
    
    def controller(self, *args, attempt=0, params={}, **kwargs):
        try: 
            print("WebRequest: {}".format(self.__class__.__name__)) 
            print("Attempt: {}|{}".format(str(attempt+1), str(self.__attempts+1)))                      
            headers, retrys, auth = self.setup(*args, **kwargs)
            session = self.start(headers=headers, retrys=retrys, auth=auth)        
            webpage = self.WebPage(session, *args, wait=self.__wait, **kwargs)
            webpage.load(*args, params=params, **kwargs)            
            yield from webpage(*args, **kwargs)   
            print("WebRequest Success: {}".format(self.__class__.__name__))
            try: self.stop(session)
            except NameError: pass   
        except BadRequestError as error:
            print("WebRequest BadRequest: {}".format(self.__class__.__name__))
            print(str(error))
            try: self.stop(session)
            except NameError: pass   
            return
            yield
        except (EmptyWebPageError, EmptyWebDataError, RefusalError) as error:
            print("WebRequest Failure: {}".format(self.__class__.__name__))
            print(str(error))
            try: self.stop(session)
            except NameError: pass              
            if attempt < self.__attempts: yield from self.controller(*args, attempt=attempt+1, **kwargs)
            else: raise MaxWebRequestAttemptError(attempt)  
            
    def stop(self, session): session.close()        
    def start(self, headers=None, retrys=None, auth=None):
        session = requests.Session() 
        if headers is not None: session.headers.update(headers)
        if auth is not None: session.auth = auth
        if retrys is not None: 
            session.mount('http://', retrys())
            session.mount('https://', retrys())
        return session
              
    def setup(self, *args, **kwargs):
        auth = self.getAuthenticate(*args, **kwargs)
        retrys = self.getRetrys(*args, **kwargs)
        headers = self.getHeaders(*args, **kwargs)
        return headers, retrys, auth
    
    def getAuthenticate(self, *args, **kwargs): return self.authenticate() if hasattr(self, 'authenticate') else None
    def getRetrys(self, *args, **kwargs): return self.retrys() if hasattr(self, 'retry') else None
    def getHeaders(self, *args, **kwargs): return next(self.headers) if hasattr(self, 'headers') else None











