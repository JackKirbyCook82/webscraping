# -*- coding: utf-8 -*-
"""
Created on Weds Jan 28 2021
@name:   WebQuery Objects
@author: Jack Kirby Cook

"""

import pandas as pd
from datetime import datetime as Datetime

from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebQuery']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebQuery(object):
    dateTag = "date"
    dateFormat = "%Y/%m/%d"
    
    def dateParser(self, string): return Datetime.strptime(string, self.dateFormat).date()
    def dateString(self, date): return date.strftime(self.dateFormat)
    def date(self): return Datetime.now().date() 
    
    def __init_subclass__(cls, *args, website, query, **kwargs):
        datasets = tuple([dataset for dataset in [kwargs.get('dataset', None), *kwargs.get('datasets', [])] if dataset])
        assert len(datasets) > 0
        setattr(cls, '_website', website)
        setattr(cls, '_query', query)
        setattr(cls, '_datasets', datasets)

    def __new__(cls, query, **data):
        assert all([key in cls._datasets for key in data.keys()])
        assert all([isinstance(dataframe, pd.DataFrame) for dataframe in data.values()])
        return super().__new__(cls)
 
    def __init__(self, query, **data): 
        self.__query, self.__data = query, data
        for dataset, dataframe in self.__data.items(): 
            dataframe[self._query] = self.__query
            dataframe[self.dateTag] = self.dateString(self.date())        
    
    def __str__(self): 
        websiteStr = '{}|{}'.format(self.__class__.__name__, uppercase(self.website))
        queryStr = 'Query: {}|{}'.format(*[uppercase(item) for item in self.query])
        data = {dataset:self.get(dataset, None) for dataset in self.datasets}
        content = {dataset:len(dataframe.index) if isinstance(dataframe, pd.DataFrame) else 0 for dataset, dataframe in data.items()}
        datasetStr = 'Datasets: {}'.format(', '.join(['|'.join([uppercase(dataset), str(size)]) for dataset, size in content.items()]))
        return '\n'.join([websiteStr, queryStr, datasetStr])

    def __getitem__(self, dataset): return self.__data[dataset]
    def __setitem__(self, dataset, dataframe):
        assert dataset in self.datasets
        assert isinstance(dataframe, pd.DataFrame)
        assert self.query[0] in dataframe.columns
        dataframe[self.query[0]] = self.query[1]
        dataframe[self.dateTag] = self.dateString(self.date())
        try: self.__data[dataset] = pd.concat([self[dataset], dataframe], ignore_index=True)
        except KeyError: self.__data[dataset] = dataframe

    def __bool__(self): return bool(self.__data)
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other): 
        if not isinstance(other, WebQuery): raise TypeError(type(other).__name__)        
        return all([self.website == other.website, self.query == other.query, self.datasets == other.datasets]) 
                                
    def __iadd__(self, other):
        if self != other: raise ValueError()
        for dataset in self.datasets:
            self.__data[dataset] = pd.concat([self.get(dataset, None), other.get(dataset, None)], ignore_index=True)
            self.__data[dataset].sort_values(self.dateTag, inplace=True)
            self.__data[dataset].drop_duplicates(subset=[column for column in self.__data[dataset].columns if column != self.dateTag], ignore_index=True, keep='last', inplace=True)
        return self        

    @property
    def website(self): return self._website
    @property
    def query(self): return (self._query, self.__query)
    @property
    def datasets(self): return self._datasets

    def asdict(self): return self.__data
    def get(self, dataset, default): return self.__data.get(dataset, default)
    def pop(self, dataset, default): return self.__data.pop(dataset, default)
    



    
    
    
    