# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


FAILURE_TIMEOUT = 10
FAILURE_XPATH = "//div[@id='main-message']//span[@jsselect='heading']"
CAPTCHA_TIMEOUT = 10
CAPTCHA_XPATH = "//div[@class='captcha-container']" 


class WebPageError(Exception):
    def __str__(self):  
        string = "{}: {}".format(self.__class__.__name__, self.args[0])
        return string if not self.args[1:] else "\n".join([string, *self.args[1:]])

class EmptyWebPageError(WebPageError): pass
class EmptyWebPageURLError(WebPageError): pass
class FailureWebPageError(WebPageError): pass
class CaptchaWebPageError(WebPageError): pass
    
    
class WebPage(ABC):    
    def __init_subclass__(cls, *args, url=None, actions={}, **kwargs):
        assert isinstance(actions, dict)
        setattr(cls, 'WebURL', url)
        setattr(cls, 'WebActions', actions)
    
    def __repr__(self): return "{}(driver={}, timeout={})".format(self.__class__.__name__, repr(self.__driver), self.__timeout)     
    def __str__(self): return "|".join([str(self.__class__.__name__), str(self.__url)])    
    def __getitem__(self, key): return self.__webactions[key]          
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)    
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__webactions = {key:value(driver, timeout) for key, value in self.WebActions.items()}       
        self.__url = kwargs.get('url', self.WebURL)
        if self.__url is None: raise EmptyWebPageURLError(self)        

    def load(self, *args, **kwargs): 
        print("WebPage Loading: {}".format(str(self)))
        self.driver.get(str(self.url))      
        confirm = WebDriverWait(self.driver, self.timeout).until(lambda driver: driver.current_url == str(self.url))
        if not confirm: raise EmptyWebPageError(self)
        failure = WebDriverWait(self.driver, FAILURE_TIMEOUT).until(EC.presence_of_all_elements_located((By.XPATH, FAILURE_XPATH)))
        if failure: raise FailureWebPageError(self)
        captcha = WebDriverWait(self.driver, CAPTCHA_TIMEOUT).until(EC.presence_of_all_elements_located((By.XPATH, CAPTCHA_XPATH)))
        if captcha: raise CaptchaWebPageError(self)
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
    @property
    def url(self): return self.__url
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    








