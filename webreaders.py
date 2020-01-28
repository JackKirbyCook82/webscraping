# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   Webreader Objects
@author: Jack Kirby Cook

"""

import time
from functools import update_wrapper
import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.util.retry import Retry

from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebReader']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class Sleeper(object):
    def __init__(self, delay=None): self.__delay, self.__lasttime = delay if delay else 0, None        
    def ready(self, currenttime): return currenttime - self.__lasttime  > self.__delay if self.__lasttime else True
    def wait(self, currenttime): return max([self.__delay - int(currenttime - self.__lasttime), 0]) if self.__lasttime else 0
    def record(self, lasttime): self.__lasttime = lasttime
    
    def __call__(self, function):
        def wrapper(*args, **kwargs):
            starttime = time.time()
            if not self.ready(starttime):
                waittime = self.wait(starttime)
                print('Download Waiting: {} Seconds'.format(waittime))
                time.sleep(waittime)
            response = function(*args, **kwargs)
            self.record(time.time())
            return response
        update_wrapper(wrapper, function)
        return wrapper
        
            
def create_retry(retries, backoff, httpcodes, **kwargs):
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff, status_forcelist=httpcodes)
    adapter = HTTPAdapter(max_retries=retry)
    return adapter


class WebReader(object): 
    requestmethods = {'get', 'post'}    
    datamethods = {'html': lambda response: response.text, 
                   'json': lambda response: response.json(), 
                   'zip' : lambda response: response.content,
                   'csv' : lambda response: response.content.deconde('utf-8')}
   
    def __new__(cls, *args, delay=0, **kwargs):
        instance = super().__new__(cls)
        instance.execute = Sleeper(delay)(instance.execute) if delay else instance.execute
        return instance
        
    def __init__(self, *args, headers={}, retry={'retries':3, 'backoff':0.3, 'httpcodes':(500, 502, 504)}, **kwargs):
        self.__headers, self.__retry= headers, retry    

    @keydispatcher
    def execute(self, method, session, url, *args, **kwargs): raise KeyError(method)
    @execute.register('get')
    def __get(self, session, url, *args, **kwargs): return session.get(url)
    @execute.register('post')
    def __post(self, session, url, *args, data={}, files={}, **kwargs): return session.post(url, data=data, files=files)

    def __call__(self, url, *args, method, datatype, cookies={}, username=None, password=None, **kwargs):
        assert method in self.requestmethods
        assert datatype in self.datamethods
        with requests.Session() as session:
            if self.__headers: session.headers.update(self.__headers)
            if cookies: session.cookies.update(cookies)              
            if username: session.auth = HTTPBasicAuth(username, password)
            retryadapter = create_retry(**self.__retry)
            session.mount('http://', retryadapter)
            session.mount('https://', retryadapter)
            
            response = self.execute(method, session, url, *args, **kwargs)
            if not response.status_code == requests.codes.ok: print('URL Request Failure:')
            else: print('URL Request Success:')  
            print(str(url), '\n')
            response.raise_for_status()
            data = self.datamethods[datatype](response)
        return data
        















