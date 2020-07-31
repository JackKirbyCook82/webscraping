# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   Webreader Objects
@author: Jack Kirby Cook

"""

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


def create_retry(retries, backoff, httpcodes):
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff, status_forcelist=httpcodes)
    adapter = HTTPAdapter(max_retries=retry)
    return adapter

def create_authentication(username, password):
    return HTTPBasicAuth(username, password)

def create_proxy(host, port):
    proxy = 'http://{}:{}'.format(host, port)
    return {'http':proxy, 'https':proxy}
    
def create_headers(headers={}, **content):
    headers.update(content)
    return headers


class WebReader(object):   
    def __init__(self, *args, **kwargs):
        pass
    
    def __call__(self, url, datatype, *args, **kwargs):
        pass
    
    def execute(self, url, datatype, *args, **kwargs):
        with requests.Session() as session:
            response = session.get(str(url))
            if not response.status_code == requests.codes.ok: print('URL Request Failure:')
            else: print('URL Request Success:')  
            print(str(url), '\n')
            response.raise_for_status()
            data = self.datamethods[datatype](response)
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


# retry={'retries':3, 'backoff':0.3, 'httpcodes':(500, 502, 504)}
# session.mount('http://', retryadapter)
# session.mount('https://', retryadapter)


#class Sleeper(object):
#    def __init__(self, delay=None): self.__delay, self.__lasttime = delay if delay else 0, None        
#    def ready(self, currenttime): return currenttime - self.__lasttime  > self.__delay if self.__lasttime else True
#    def wait(self, currenttime): return max([self.__delay - int(currenttime - self.__lasttime), 0]) if self.__lasttime else 0
#    def record(self, lasttime): self.__lasttime = lasttime
#    
#    def __call__(self, function):
#        def wrapper(*args, **kwargs):
#            starttime = time.time()
#            if not self.ready(starttime):
#                waittime = self.wait(starttime)
#                print('Download Waiting: {} Seconds'.format(waittime))
#                time.sleep(waittime)
#            response = function(*args, **kwargs)
#            self.record(time.time())
#            return response
#        update_wrapper(wrapper, function)
#        return wrapper   
           
















