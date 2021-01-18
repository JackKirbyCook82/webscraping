# -*- coding: utf-8 -*-
"""
Created on Weds Jul 29 2020
@name:   Webscraping WebAPI Objects
@author: Jack Kirby cook

"""

import os.path
import time
import random
import pandas as pd
from datetime import datetime as Datetime
from abc import ABC, abstractmethod

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


def urlsgmt(sgmttype):
    def decorator(method):
        def wrapper(self, *args, **kwargs): return sgmttype(method(self, *args, **kwargs))
        return wrapper
    return decorator


class URLAPI(object):
    def __init_subclass__(cls, *args, protocol, domain, path=[], parms={}, **attrs):
        setattr(cls, '_protocol', protocol)
        setattr(cls, '_domain', domain)
        setattr(cls, '_path', path)
        setattr(cls, '_parms', parms)
        for name, attr in attrs.items(): setattr(cls, name, attr)
        cls.protocol = urlsgmt(Protocol)(cls.protocol)
        cls.domain = urlsgmt(Domain)(cls.domain)
        cls.path = urlsgmt(Path)(cls.path)
        cls.parms = urlsgmt(Parms)(cls.parms)
 
    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, '_protocol') and hasattr(cls, '_domain') and hasattr(cls, '_path') and hasattr(cls, '_parms')
        return super().__new__(cls)
 
    def __repr__(self): return "{}(protocol='{}', domain='{}', path={}, parms={})".format(self.__class__.__name__, self._protocol, self._domain, self._path, self._parms)    
    def __call__(self, *args, **kwargs): 
        url = self.execute(*args, **kwargs)
        return url if url else self.construct(*args, **kwargs)    

    def execute(self, *args, **kwargs): return kwargs.get('link', kwargs.get('url', None))
    def construct(self, *args, **kwargs): return URL(protocol=self.protocol(*args, **kwargs), domain=self.domain(*args, **kwargs), path=self.path(*args, **kwargs), parms=self.parms(*args, **kwargs))    

    def protocol(self, *args, **kwargs): return self._protocol.format(**kwargs)
    def domain(self, *args, **kwargs): return self._domain.format(**kwargs)
    def path(self, *args, **kwargs): return [item.format(**kwargs) for item in self._path]
    def parms(self, *args, **kwargs): return {key.format(**kwargs):value.format(**kwargs) for key, value in self._parms.items()}


class WebAPI(ABC):
    recordedTag = 'recorded'
    recordedFormat = "%Y/%m/%d"
    
    def recordedDate(self): return Datetime.now()
    def recordedParser(self, string): return Datetime.strptime(string, self.recordedFormat).date()
    def recordedString(self, date): return date.strftime(self.recordedFormat)

    def __repr__(self): return "{}(repository='{}', wait={}, filetype='{}', compression='{}')".format(self.__class__.__name__, self.__repository, self.__wait, self.__filetype, self.__compression)   
    def __init__(self, repository, urlapi, webreader, *args, wait=5, filetype='csv', compression=None, **kwargs):
        assert os.path.isdir(repository)
        self.__repository = repository     
        self.__urlapi = urlapi
        self.__webreader = webreader
        self.__wait = wait
        self.__filetype = filetype
        self.__compression = compression
        if isinstance(wait, int): pass
        elif isinstance(wait, tuple): assert len(wait) == 2
        else: raise TypeError(type(wait))

    @property
    def repository(self): return self.__repository
    @property
    def urlapi(self): return self.__urlapi
    @property
    def webreader(self): return self.__webreader
    
    @abstractmethod
    def queue(self, *args, **kwargs): pass

    def sleep(self):
        if isinstance(self.__wait, int): time.sleep(self.__wait)
        elif isinstance(self.__wait, tuple): time.sleep(random.uniform(*self.__wait))
        else: raise TypeError(type(self.__wait))
    
    def __call__(self, *args, **kwargs):
        for query in self.queue(*args, **kwargs):
            assert isinstance(query, dict)
            url = self.urlapi(*args, **query, **kwargs) 
            assert isinstance(url, (URL, str))
            self.execute(url, *args, **query, **kwargs)        
            try: self.sleep()
            except AttributeError: pass
        
    def execute(self, url, *args, **kwargs):
        try: 
            downloaded = self.download(url, *args, **kwargs)   
            assert isinstance(downloaded, dict)
            success = self.recordall(**downloaded)
            assert all(success)
            print('Downloading Success: {}\n{}'.format(self.__class__.__name__, str(url)))
        except FailureWebDriverError:               
            print('Downloading Failure: {}\n{}'.format(self.__class__.__name__, str(url)))
            raise FailureWebAPIError(self) 
        print("\n")
             
    def download(self, url, *args, **kwargs):      
        data = {}
        for newdata in self.__webreader(str(url), *args, **kwargs): 
            assert isinstance(newdata, dict)
            assert all([isinstance(value, pd.DataFrame) for value in newdata.values()])
            for dataset, dataframe in newdata.items():
                dataframe[self.recordedTag] = self.recordedString(self.recordedDate())
                try: data[dataset] = pd.concat([data[dataset], dataframe], ignore_index=True)
                except KeyError: data[dataset] = dataframe
        return data    
     
    def recordall(self, **data):
        assert all([isinstance(value, pd.DataFrame) for value in data.values()])
        return [self.record(dataset, dataframe) for dataset, dataframe in data.items()]
        
    def record(self, dataset, downloaded):
        try: dataframe = self.load(dataset)
        except FileNotFoundError: pass        
        try: dataframe = pd.concat([dataframe, downloaded], ignore_index=True)
        except NameError: dataframe = downloaded
        dataframe = dataframe.drop_duplicates(subset=[column for column in dataframe.columns if column != self.recordedTag], ignore_index=True, keep='last')     
        self.save(dataset, dataframe)  
        return True
        
    def filename(self, dataset): return '.'.join([dataset, self.__compression, self.__filetype]) if self.__compression else '.'.join([dataset, self.__filetype])
    def file(self, dataset): return os.path.join(self.repository, self.filename(dataset))
    def load(self, dataset): return dataframe_fromfile(self.file(dataset), index=None, header=0, forceframe=True)  
    def save(self, dataset, dataframe): dataframe_tofile(self.file(dataset), dataframe, index=False, header=True)  

















