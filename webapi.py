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
from datatime import date as Date

from utilities.dataframes import dataframe_tofile, dataframe_fromfile
from utilities.strings import uppercase

from webscraping.url import URL, Protocol, Domain, Path, Parms
from webscraping.webdrivers import FailureWebDriverError, FailureWebRequestError

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


class WebAPI(object):
    queryFileTag = 'queryRecord'
    queryIDTag = 'queryID'
    queryDateTag = 'queryDate'
    queryDateFormat = "%Y/%m/%d"
    
    def dateString(self, string): return Datetime.strptime(string, self.queryDateFormat).date()
    def dateParser(self, date): return date.strftime(self.queryDateFormat)

    def __str__(self): return '|'.join([self.__class__.__name__, self.__website, self.__dataset])
    def __repr__(self): 
        content = [self.__website, self.__dataset, self.__repository, self.__wait, self.__filetype, self.__compression]
        return "{}(website={}, dataset={}, repository='{}', wait={}, filetype='{}', compression='{}')".format(self.__class__.__name__, *content)   
    
    def __init__(self, website, dataset, repository, urlapi, webreader, *args, wait=5, filetype='csv', compression=None, **kwargs):
        assert os.path.isdir(repository)
        if isinstance(wait, int): pass
        elif isinstance(wait, tuple): assert len(wait) == 2
        else: raise TypeError(type(wait))
        self.__website = website
        self.__dataset = dataset      
        self.__wait = wait
        self.__filetype = filetype
        self.__compression = compression       
        self.__repository = repository     
        self.__urlapi = urlapi
        self.__webreader = webreader

    @property
    def repository(self): return self.__repository
    @property
    def urlapi(self): return self.__urlapi
    @property
    def webreader(self): return self.__webreader

    def sleep(self):
        if isinstance(self.__wait, int): time.sleep(self.__wait)
        elif isinstance(self.__wait, tuple): time.sleep(random.uniform(*self.__wait))
        else: raise TypeError(type(self.__wait))   
    
    def __call__(self, *args, **kwargs):
        for query in self.queue(*args, **kwargs):
            assert isinstance(query, dict)
            url = self.urlapi(*args, **query, **kwargs) 
            assert isinstance(url, (URL, str))
            try: self.execute(url, *args, **kwargs)
            except (FailureWebDriverError, FailureWebRequestError) as error: raise error
            try: self.sleep()
            except AttributeError: pass
        
    def execute(self, url, *args, **kwargs):
        for queryID, queryData in self.download(url,*args, **kwargs):
            print('Downloading Success: {}'.format(str(self)))
            print('Query: {}'.format(queryID))
            print('Datasets: {}'.format(', '.join(['|'.join([uppercase(dataset), str(len(dataframe.index))]) for dataset, dataframe in queryData.items()])))
            self.recordall(**queryData)    
            self.report(queryID)                      

    def download(self, url, *args, **kwargs):
        queryData = {}
        for queryID, queryDataset, queryDataFrame, queryComplete in self.downloader(url, *args, **kwargs):
            try: queryData[queryDataset] = pd.concat([queryData[queryDataset], queryDataFrame], ignore_index=True)
            except KeyError: queryData[queryDataset] = queryDataFrame
            if queryComplete: 
                yield queryID, queryData
                queryData = {}
    
    def downloader(self, url, *args, **kwargs):
        for queryID, queryDataset, queryDataFrame, queryComplete, queryDate in self.webreader(str(url), *args, **kwargs):
            assert isinstance(queryDataFrame, pd.DataFrame) and isinstance(queryDate, Date) and isinstance(queryComplete, bool)
            queryDataFrame[self.queryIDTag] = queryID
            queryDataFrame[self.queryDateTag] = self.dateString(queryDate)
            yield queryID, queryDataset, queryDataFrame, queryComplete
     
    def report(self, queryID): 
        file = os.path.join([self.respository, self.__website, self.__dataset, self.queryFileTag])
        try: dataframe = dataframe_fromfile(file, index=None, header=0, forceframe=True)  
        except FileNotFoundError: pass
        try: dataframe = pd.concat([dataframe, pd.DataFrame({'website':[self.__website], 'dataset':[self.__dataset], 'query':[queryID]})], ignore_index=True)
        except NameError: dataframe = pd.DataFrame({'website':[self.__website], 'dataset':[self.__dataset], 'query':[queryID]})
        dataframe_tofile(file, dataframe, index=False, header=True)  
        
    def recordall(self, **queryData):
        assert all([isinstance(value, pd.DataFrame) for value in queryData.values()])
        for queryDataset, queryDataFrame in queryData.items(): self.record(queryDataset, queryDataFrame)
        
    def record(self, queryDataset, queryDataFrame):
        try: dataset, dataframe = queryDataset, self.load(queryDataset)
        except FileNotFoundError: pass        
        try: dataset, dataframe = queryDataset, pd.concat([dataframe, queryDataFrame], ignore_index=True)
        except NameError: pass
        dataframe = dataframe.drop_duplicates(subset=[column for column in dataframe.columns if column != self.queryDateTag], ignore_index=True, keep='last')     
        self.save(dataset, dataframe)  
        
    def filename(self, queryDataset): return '.'.join([queryDataset, self.__compression, self.__filetype]) if self.__compression else '.'.join([queryDataset, self.__filetype])
    def file(self, queryDataset): return os.path.join(self.repository, self.__website, self.__dataset, self.filename(queryDataset))
    def load(self, queryDataset): return dataframe_fromfile(self.file(queryDataset), index=None, header=0, forceframe=True)  
    def save(self, queryDataset, queryDataFrame): dataframe_tofile(self.file(queryDataset), queryDataFrame, index=False, header=True)  

















