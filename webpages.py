# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
from abc import ABC, abstractmethod

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
    def __init__(self, driver, timeout, *args, wait=None, failure_timeout=10, captcha_timeout=20, **kwargs): 
        self.__driver, self.__timeout, self.__wait = driver, timeout, wait
        try: self.__failure = self.Failure(driver, failure_timeout)
        except AttributeError: pass
        try: self.__captcha = self.Captcha(driver, captcha_timeout)
        except AttributeError: pass
        self.__webelements = {key:webelement(driver, timeout) for key, webelement in self.WebElements.items()}       
        self.__url = kwargs.get('url', self.URL)
        if self.__url is None: raise EmptyURLError()
   
    def sleep(self): time.sleep(self.wait)
    def load(self, *args, **kwargs): 
        print("WebPage Loading: {}".format(self.__class__.__name__))
        print(str(self.url))
        self.driver.get(str(self.url))
        self.sleep()
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
        if captcha: print('WebPage Captcha: {}'.format(self.__class__.__name__))
        else: pass
        if captcha: captcha.wait(self.wait)
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
    @property
    def wait(self): return self.__wait
    @property
    def url(self): return self.__url
    
    @abstractmethod
    def setup(self, *args, **kwargs): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    
    @classmethod
    def create(cls, webelements, *args, url=None, **kwargs):
        assert isinstance(webelements, dict)
        def wrapper(subclass): 
            attrs = {'URL':url}
            if 'failure' in webelements.keys(): attrs['Failure'] = webelements.pop('failure')
            if 'captcha' in webelements.keys(): attrs['Captcha'] = webelements.pop('captcha')         
            attrs['WebElements'] = webelements
            return type(subclass.__name__, (subclass, cls), attrs)
        return wrapper  








