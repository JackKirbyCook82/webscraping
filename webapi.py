# -*- coding: utf-8 -*-
"""
Created on Weds Jul 29 2020
@name:   WebAPI Objects
@author: Jack Kirby cook

"""

import os.path
import time
import random
import pandas as pd
from abc import ABC, abstractmethod

from utilities.dataframes import dataframe_tofile, dataframe_fromfile

from webscraping.url import URL
from webscraping.webpages import BadRequestError

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
    def __str__(self): return self.__class__.__name__
    def __repr__(self): 
        content = [self.__repository, self.__wait, self.__filetype, self.__compression]
        return "{}(repository='{}', wait={}, filetype='{}', compression='{}')".format(self.__class__.__name__, *content)   
    
    def __init__(self, *args, repository, webreader, wait=10, filetype='csv', compression=None, **kwargs):
        assert os.path.isdir(repository)
        if isinstance(wait, int): pass
        elif isinstance(wait, tuple): assert len(wait) == 2
        else: raise TypeError(type(wait))
        self.__wait = wait
        self.__filetype = filetype
        self.__compression = compression       
        self.__repository = repository     
        self.__webreader = webreader

    @property
    def repository(self): return self.__repository
    @property
    def webreader(self): return self.__webreader
    
    def sleep(self):
        if isinstance(self.__wait, int): time.sleep(self.__wait)
        elif isinstance(self.__wait, tuple): time.sleep(random.uniform(*self.__wait))
        else: raise TypeError(type(self.__wait))     
  
    def __call__(self, *args, dataset, **kwargs):
        queue, query = self.queue(*args, **kwargs), self.query(*args, **kwargs)
        assert isinstance(queue, dict) and isinstance(query, dict)
        assert all([isinstance(values, list) for key, values in queue.items()])
        assert all([isinstance(values, dict) for key, values in query.items()])
        assert all([set(queue[key]) == set(query[key].keys()) for key in queue.keys()])
        for queueKey in queue.keys(): random.shuffle(queue[queueKey])
        for queueKey, queueValues in queue.items():
            completed = set(self.completed(dataset, queueKey))
            for queueValue in queueValues:
                if queueValue in completed: continue
                crawling = [value for value in queue[queueKey] if value != queueValue and value not in completed] 
                for completedKey, completedValue in self.execute(dataset, queueKey, queueValue, *args, **query[queueKey][queueValue], crawling=crawling, **kwargs):
                    assert queueKey == completedKey
                    completed.add(completedValue)
                    self.sleep()

    def execute(self, dataset, queueKey, queueValue, *args, **kwargs):         
        try: 
            for completedKey, completedValue in self.generator(dataset, *args, **kwargs):
                self.addreport(dataset, completedKey, completedValue)
                yield (completedKey, completedValue)
        except BadRequestError: 
            self.addreport(dataset, queueKey, queueValue)
            yield (queueKey, queueValue)

    def generator(self, dataset, *args, **kwargs):
        for webquery in self.download(*args, dataset=dataset, **kwargs):
            print('Downloading Success: {}'.format(str(self)))
            print(str(webquery))
            for queryDataset, queryDataframe in webquery.asdict().items(): self.addrecord(dataset, queryDataset, queryDataframe, ignore=webquery.dateTag)            
            yield webquery.query
    
    def download(self, *args, **kwargs):
        downloaded = None
        for webquery in self.webreader(*args, **kwargs):
            if webquery is None and downloaded is None: pass
            elif webquery is not None and downloaded is None: downloaded = webquery        
            elif webquery is not None and downloaded is not None: downloaded += webquery
            elif webquery is None and downloaded is not None: 
                yield downloaded                
                downloaded = None
            else: raise ValueError()

    def filename(self, queryDataset): return '.'.join([queryDataset, self.__compression, self.__filetype]) if self.__compression else '.'.join([queryDataset, self.__filetype])
    def file(self, websiteDataset, queryDataset): return os.path.join(self.repository, websiteDataset, self.filename(queryDataset))
    def load(self, websiteDataset, queryDataset): return dataframe_fromfile(self.file(websiteDataset, queryDataset), index=None, header=0, forceframe=True)  
    def save(self, websiteDataset, queryDataset, queryDataFrame): dataframe_tofile(self.file(websiteDataset, queryDataset), queryDataFrame, index=False, header=True)  

    def setreport(self, websiteKey, queryKey):
        with open(os.path.join(self.repository, websiteKey, '.'.join([queryKey, 'txt'])), "w") as _: pass
    def getreport(self, websiteKey, queryKey):
        with open(os.path.join(self.repository, websiteKey, '.'.join([queryKey, 'txt'])), "r") as txtfile: return [line.strip() for line in txtfile.readlines()]
    def addreport(self, websiteKey, queryKey, queryValue): 
        with open(os.path.join(self.repository, websiteKey, '.'.join([queryKey, 'txt'])), "a") as txtfile: txtfile.write(queryValue + "\n")        

    def addrecord(self, websiteDataset, queryDataset, queryDataFrame, ignore): 
        ignore = [ignore] if not isinstance(ignore, (tuple, list)) else list(ignore)
        assert isinstance(queryDataFrame, pd.DataFrame)        
        try: dataset, dataframe = queryDataset, self.load(websiteDataset, queryDataset)
        except FileNotFoundError: pass        
        try: dataset, dataframe = queryDataset, pd.concat([dataframe, queryDataFrame], ignore_index=True)
        except NameError: dataset, dataframe = queryDataset, queryDataFrame
        dataframe.drop_duplicates(subset=[column for column in dataframe.columns if column not in ignore], inplace=True, ignore_index=True, keep='last')   
        self.save(websiteDataset, dataset, dataframe)  
        
    @abstractmethod
    def queue(self): pass
    @abstractmethod
    def query(self): pass

    def completed(self, websiteKey, queryKey): 
        try: return self.getreport(websiteKey, queryKey) 
        except FileNotFoundError: 
            self.setreport(websiteKey, queryKey)
            return self.getreport(websiteKey, queryKey)












