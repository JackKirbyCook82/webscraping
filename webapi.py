# -*- coding: utf-8 -*-
"""
Created on Webs Jan 22 2020
@name:   WebAPI Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
import os.path

from utilities.dataframes import dataframe_tofile, dataframe_fromfile

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebAPI']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebAPI(ABC):
    def __repr__(self): return "{}(repository='{}', saving='{}')".format(self.__class__.__name__, self.__repository, self.__saving)   
    def __init__(self, repository, urlapi, webreader, *args, saving=True, **kwargs):
        self.__urlapi = urlapi
        self.__webreader = webreader
        self.__repository = repository
        self.__saving = saving
       
    @property
    def repository(self): return self.__repository
    @property
    def saving(self): return self.__saving        
    @property
    def urlapi(self): return self.__urlapi
    @property
    def webreader(self): return self.__webreader
    
    def load(self, *args, **kwargs): 
        file = self.file(*args, **kwargs)
        return dataframe_fromfile(file, index=None, header=0, forceframe=True)            
    def save(self, webtable, *args, **kwargs): 
        file = self.file(*args, **kwargs)
        dataframe_tofile(file, webtable, index=False, header=True)   

    @abstractmethod
    def filename(self, *args, **kwargs): pass
    def file(self, *args, **kwargs): return os.path.join(self.repository, self.filename(*args, **kwargs))
    



        
        