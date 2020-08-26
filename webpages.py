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
        try: url = str(self.url(*args, **kwargs))
        except TypeError: url = str(self.url)        
        print('URL WebDriver Request: {}'.format(url))
        self.__driver.get(url)
        print('WebPage Loading Success')
        for key, webelement in self.__webelements.items(): webelement(webelement.load(timeout))  
        print('WebElement Loading Success')
        
    @abstractmethod
    def execute(self, *args, **kwargs): pass        
        
    @classmethod
    def create(cls, webelements, *args, url, **kwargs):
        assert isinstance(webelements, dict)
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'url':url, 'WebElements':webelements})
        return wrapper  









