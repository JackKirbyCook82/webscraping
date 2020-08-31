# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebPageError(Exception): pass
class EmptyURLError(Exception): pass


class WebPage(ABC):        
    def __getitem__(self, key): return self.__webelements[key]      
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __init__(self, driver, timeout, *args, failure_timeout=10, captcha_timeout=20, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        try: self.__failure = self.WebElements.pop('failure')(driver, failure_timeout)
        except KeyError: print('No Failure Check: {}'.format(self.__class__.__name__))
        try: self.__captcha = self.WebElements.pop('captcha')(driver, captcha_timeout)        
        except KeyError: print('No Captcha Check: {}'.format(self.__class__.__name__))
        self.__webelements = {key:webelement(driver, timeout) for key, webelement in self.WebElements.items()}       
        self.__url = kwargs.get('url', self.URL)
        if self.__url is None: raise EmptyURLError()
   
    def load(self, *args, **kwargs): 
        print("WebPage Loading: {}".format(self.__class__.__name__))
        print(str(self.url))
        self.driver.get(str(self.url))
        try: self.check_for_failure()
        except AttributeError: pass
        try: self.check_for_captcha()
        except AttributeError: pass


    def check_for_failure(self):
        failure = self.__failure.load()
        if failure: print('WebPage Failure: {}'.format(self.__class__.__name__))
        else: print('WebPage Success: {}'.format(self.__class__.__name__))  
        if failure: raise EmptyWebPageError(str(failure.text)) 
    
    
    def check_for_captcha(self):
        captcha = self.__captcha.load()




        
    def loads(self, *keys): 
        for key in keys: self[key].load()
 
    def clicks(self, *keys): 
        for key in keys: self[key].click()
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
    @property
    def url(self): return self.__url
    
    @abstractmethod
    def setup(self, *args, **kwargs): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    
    @classmethod
    def create(cls, webelements, *args, url=None, **kwargs):
        assert isinstance(webelements, dict)
        assert 'failure' in webelements.keys() and 'captcha' in webelements.keys()
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'URL':url, 'WebElements':webelements})
        return wrapper  









