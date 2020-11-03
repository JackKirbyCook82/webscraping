# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod

from webscraping.elements import EmptyElementError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebPage(ABC):    
    def __init_subclass__(cls, *args, pageNext=None, pageIteration=None, pageCaptcha=None, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        if pageNext is not None: setattr(cls, 'PageNext', pageNext)
        if pageIteration is not None: setattr(cls, 'PageIteration', pageIteration)
        if pageCaptcha is None: setattr(cls, 'PageCaptcha', pageCaptcha)
        setattr(cls, 'PageContents', pageContents)
    
    def __repr__(self): return "{}(driver={}, timeout={})".format(self.__class__.__name__, repr(self.__driver), self.__timeout)     
    def __str__(self): return self.__class__.__name__        
    def __init__(self, driver, timeout, *args, **kwargs): self.__driver, self.__timeout, self.__pagecontents = driver, timeout, {}      
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)    
    
    def __getitem__(self, key): 
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.__pagecontents[key] = self.PageContents[key](self.driver, self.timeout)
        return self.__pagecontents[key]

    def __iter__(self): 
        try: return iter(self.PageIteration(self.driver, self.timeout))
        except AttributeError: return iter([])
    
    def __next__(self): 
        try: self.PageNext(self.__driver, self.__timeout)
        except (AttributeError, EmptyElementError): return False
        return True

    def load(self, url, *args, **kwargs): 
        print("WebPage Loading: {}".format(str(self)))
        self.driver.get(str(url))      
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    

    













