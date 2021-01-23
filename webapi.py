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
from abc import ABC, abstractmethod
from collections import OrderedDict as ODict
from datetime import datetime as Datetime
from datetime import date as Date

from utilities.dataframes import dataframe_tofile, dataframe_fromfile
from utilities.strings import uppercase

from webscraping.url import URL

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['URLAPI', 'WebAPI']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class URLAPI(object):
    def __init_subclass__(cls, *args, protocol, domain, path=[], parms={}, **attrs):
        setattr(cls, '_protocol', protocol)
        setattr(cls, '_domain', domain)
        setattr(cls, '_path', path)
        setattr(cls, '_parms', parms)
        for name, attr in attrs.items(): setattr(cls, name, attr)
 
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
    reportTag = "report"
    queryTag = "query"
    dateTag = "recorded"
    dateFormat = "%Y/%m/%d"
    
    def dateString(self, string): return Datetime.strptime(string, self.dateFormat).date()
    def dateParser(self, date): return date.strftime(self.dateFormat)

    def __str__(self): return '{}|{}'.format(self.__class__.__name__, uppercase(self.__dataset))
    def __repr__(self): 
        content = [self.__dataset, self.__repository, self.__wait, self.__filetype, self.__compression]
        return "{}(dataset={}, repository='{}', wait={}, filetype='{}', compression='{}')".format(self.__class__.__name__, *content)   
    
    def __init__(self, *args, dataset, repository, webreader, wait=10, filetype='csv', compression=None, **kwargs):
        assert os.path.isdir(repository)
        if isinstance(wait, int): pass
        elif isinstance(wait, tuple): assert len(wait) == 2
        else: raise TypeError(type(wait))
        self.__wait = wait
        self.__dataset = dataset
        self.__filetype = filetype
        self.__compression = compression       
        self.__repository = repository     
        self.__webreader = webreader

    @property
    def repository(self): return os.path.join(self.__repository, self.__dataset)
    @property
    def webreader(self): return self.__webreader
    
    def sleep(self):
        if isinstance(self.__wait, int): time.sleep(self.__wait)
        elif isinstance(self.__wait, tuple): time.sleep(random.uniform(*self.__wait))
        else: raise TypeError(type(self.__wait))     
  
    def __call__(self, *args, **kwargs):
          queue, completed = self.queue(*args, **kwargs), set(self.completed(*args, **kwargs))
          queue = [(key, query) for key, query in queue.items()]
          random.shuffle(queue)
          queue, crawling = ODict(queue), list(queue.keys())
          for queryID, query in queue.items():
              if queryID in completed: continue
              for completedID in self.execute(*args, **query, crawling=crawling, **kwargs): completed.add(completedID)
              self.sleep()

    def execute(self, *args, **kwargs):
        for queryID, queryData in self.download(*args, **kwargs):
            print('Downloading Success: {}'.format(str(self)))
            print('Query: {}'.format(queryID))
            print('Datasets: {}'.format(', '.join(['|'.join([dataset, str(len(dataframe.index))]) for dataset, dataframe in queryData.items()])))
            self.recordall(**queryData)    
            self.addreport(queryID)                      
            yield queryID
        
    def download(self, *args, **kwargs):
        queryData = {}
        for queryID, queryDataset, queryDataFrame, queryComplete in self.downloader(*args, **kwargs):
            try: queryData[queryDataset] = pd.concat([queryData[queryDataset], queryDataFrame], ignore_index=True)
            except KeyError: queryData[queryDataset] = queryDataFrame
            if queryComplete: 
                yield queryID, queryData
                queryData = {}          
        
    def downloader(self, *args, **kwargs):
        for queryID, queryDataset, queryDataFrame, queryComplete, queryDate in self.webreader(*args, dataset=self.__dataset, **kwargs):
            assert isinstance(queryDataFrame, (pd.DataFrame, type(None))) and isinstance(queryDate, Date) and isinstance(queryComplete, bool)
            try: 
                queryDataFrame[self.queryTag] = queryID
                queryDataFrame[self.dateTag] = self.dateString(queryDate)
            except TypeError: pass
            yield queryID, queryDataset, queryDataFrame, queryComplete        
        
    def setreport(self):
        with open(os.path.join(self.repository, '.'.join([self.reportTag, 'txt'])), "w") as _: pass
    def addreport(self, queryID): 
        with open(os.path.join(self.repository, '.'.join([self.reportTag, 'txt'])), "a") as txtfile: txtfile.write(queryID + "\n")
    def getreport(self):
        with open(os.path.join(self.repository, '.'.join([self.reportTag, 'txt'])), "r") as txtfile: return txtfile.readlines()
        
    def recordall(self, **queryData):
        assert all([isinstance(value, pd.DataFrame) for value in queryData.values()])
        for queryDataset, queryDataFrame in queryData.items(): self.record(queryDataset, queryDataFrame)
        
    def record(self, queryDataset, queryDataFrame):
        try: dataset, dataframe = queryDataset, self.load(queryDataset)
        except FileNotFoundError: pass        
        try: dataset, dataframe = queryDataset, pd.concat([dataframe, queryDataFrame], ignore_index=True)
        except NameError: dataset, dataframe = queryDataset, queryDataFrame
        dataframe = dataframe.drop_duplicates(subset=[column for column in dataframe.columns if column != self.dateTag], ignore_index=True, keep='last')     
        self.save(dataset, dataframe)  
        
    def filename(self, queryDataset): return '.'.join([queryDataset, self.__compression, self.__filetype]) if self.__compression else '.'.join([queryDataset, self.__filetype])
    def file(self, queryDataset): return os.path.join(self.repository, self.filename(queryDataset))
    def load(self, queryDataset): return dataframe_fromfile(self.file(queryDataset), index=None, header=0, forceframe=True)  
    def save(self, queryDataset, queryDataFrame): dataframe_tofile(self.file(queryDataset), queryDataFrame, index=False, header=True)      

    @abstractmethod
    def queue(self, *args, **kwargs): pass
    def completed(self, *args, **kwargs): 
        try: return self.getreport() 
        except FileNotFoundError: 
            self.setreport()
            return self.getreport()













