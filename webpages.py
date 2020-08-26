# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebPageError(Exception): pass


class WebPage(ABC):        
    def __getitem__(self, key): return self.__webelements[key]      
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __init__(self, driver, *args, **kwargs): 
        self.__webelements = {key:webelement(driver) for key, webelement in self.WebElements.items()}
        self.__driver = driver
        
    def load(self, *args, timeout, **kwargs):  
        url = kwargs.get('url', self.url)
        assert url is not None
        self.__driver.get(str(url))
        print('URL Request Success: {}'.format(str(url)))
        for webelement in self.loadWebElements: self.__webelements[webelement].load(timeout)
        print("WebPage Loaded: {}".format(self.__class__.__name__))
        
    @abstractmethod
    def execute(self, *args, **kwargs): pass        
        
    @classmethod
    def create(cls, webelements, *args, url=None, load=[], **kwargs):
        assert isinstance(webelements, dict)
        def wrapper(subclass): 
            attrs = {'url':url, 'loadWebElements':tuple(load), 'WebElements':webelements}
            return type(subclass.__name__, (subclass, cls), attrs)
        return wrapper  









