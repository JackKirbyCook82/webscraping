# -*- coding: utf-8 -*-
"""
Created on Weds Jul 29 2020
@name:   Webscraping WebAPI Objects
@author: Jack Kirby cook

"""

import pandas as pd

from utilities.dataframes import dataframe_tofile, dataframe_fromfile

from webscraping.url import URL, Protocol, Domain, Path, Parms
from webscraping.webdrivers import FailureWebDriverError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['URLAPI', 'WebAPI']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class WebAPIError(Exception):
    def __str__(self): return "{}: {}".format(self.__class__.__name__, self.args[0].__class__.__name__)   

class FailureWebAPIError(WebAPIError): pass


class URLAPI(object):
    def __init_subclass__(cls, *args, protocol, domain, path=[], parms={}, **attrs):
        setattr(cls, '_protocol', protocol)
        setattr(cls, '_domain', domain)
        setattr(cls, '_path', path)
        setattr(cls, '_parms', parms)
        for name, attr in attrs.items(): setattr(cls, name, attr)

    def __repr__(self): return "{}(protocol={}, domain={})".format(self.__class__.__name__, self._protocol, self._domain)
    def __init__(self, *args, **kwargs): pass
    def __iter__(self): return self.__call__
    def __call__(self, *args, **kwargs): 
        for path in self.path(*args, **kwargs): 
            for parms in self.parms(*args, **kwargs): 
                yield URL(protocol=self.protocol, domain=self.domain, path=path, parms=parms)
    
    def protocol(self, *args, **kwargs): return Protocol(self._protocol)
    def domain(self, *args, **kwargs): return Domain(self._domain)  
    def path(self, *args, **kwargs): yield Path(*self._path)
    def parms(self, *args, **kwargs): yield Parms(**self._parms)


class WebAPI(object):
    def __repr__(self): return "{}(files={})".format(self.__class__.__name__, self.__files)   
    def __init__(self, files, urlapi, webreader, *args, **kwargs):
        assert isinstance(files, dict)
        self.__files = self.__files
        self.__urlapi = urlapi
        self.__webreader = webreader
 
    def __call__(self, *args, **kwargs):
        for url in self.__urlapi(*args, **kwargs): self.execute(url, *args, **kwargs)   
            
    def execute(self, url, *args, **kwargs):
        try: 
            downloaded = self.download(url, *args, **kwargs)   
            self.recordall(downloaded, *args, **kwargs) 
            print('Scraping Success: {}\n{}'.format(self.__class__.__name__, str(url)))
        except FailureWebDriverError:               
            print('Scraping Failure: {}\n{}'.format(self.__class__.__name__, str(url)))
            raise FailureWebAPIError(self)

    def download(self, url, *args, **kwargs):        
        dataframes = dict.fromkeys(self.__files.keys())
        for data in self.__webreader(str(url), *args, **kwargs): 
            assert isinstance(data, dict)
            assert data.keys() == dataframes.keys() and all([isinstance(value, pd.DataFrame) for value in data.values()])
            for key, dataframe in data.items():
                if dataframes[key] is None: dataframes[key] = dataframe
                else: dataframes[key] = pd.concat([dataframes[key], dataframe], ignore_index=True)
        return dataframes            

    def recordall(self, dataframes, *args, **kwargs): 
        assert isinstance(dataframes, dict)
        for dataset, dataframe in dataframes.items(): self.record(dataset, dataframe, *args, **kwargs)

    def record(self, dataset, dataframe, *args, **kwargs):
        try: dataframe = pd.concat([self.load(dataset), dataframe], ignore_index=True).drop_duplicates(ignore_index=True, keep='last')
        except FileNotFoundError: pass        
        self.save(dataset, dataframe)        

    def load(self, dataset): return dataframe_fromfile(self.__files[dataset], index=None, header=0, forceframe=True)  
    def save(self, dataset, dataframe): dataframe_tofile(self.__files[dataset], dataframe, index=False, header=True)   










