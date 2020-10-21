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
from selenium.common.exceptions import WebDriverException, TimeoutException

from webscraping.elements import EmptyElementError

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
        string = "{}: {}".format(self.__class__.__name__, self.args[0].__class__.__name__)
        return string if not self.args[1:] else "\n".join([string, *self.args[1:]])

class EmptyWebPageError(WebPageError): pass
class FailureWebPageError(WebPageError): pass
class CaptchaWebPageError(WebPageError): pass
    
    
class WebPage(ABC):    
    def __init_subclass__(cls, *args, pageNext=None, pageIteration=None, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        if pageNext is not None: setattr(cls, 'PageNext', pageNext)
        if pageIteration is not None: setattr(cls, 'PageIteration', pageIteration)
        setattr(cls, 'PageContent', pageContents)
    
    def __repr__(self): return "{}(driver={}, timeout={})".format(self.__class__.__name__, repr(self.__driver), self.__timeout)     
    def __str__(self): return self.__class__.__name__        
    def __init__(self, driver, timeout, *args, **kwargs): self.__driver, self.__timeout, self.__contents = driver, timeout, {}      
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)    
    
    def __getitem__(self, key): 
        try: return self.__contents[key]
        except KeyError:
            self.__contents[key] = self.Contents[key](self.__driver, self.__timeout)
            return self.__contents[key]
 
    def __iter__(self): 
        try: return (data for data in iter(self['iterpage']))
        except AttributeError: return (data for data in [])
    
    def __next__(self): 
        try: 
            self['pageNext']()
            return True
        except (AttributeError, EmptyElementError): 
            return False

    def load(self, url, *args, **kwargs): 
        print("WebPage Loading: {}".format(str(self)))
        try: self.driver.get(str(url))      
        except (WebDriverException, TimeoutException) as error: 
            self.checkFailure()
            raise error
        
    def checkFailure(self):
        try: failure = WebDriverWait(self.driver, FAILURE_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, FAILURE_XPATH)))
        except TimeoutException: failure = None
        if failure: raise FailureWebPageError(self, str(failure.text)) 
        else: pass
    
    def checkCaptcha(self):
        try: captcha = WebDriverWait(self.driver, CAPTCHA_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, CAPTCHA_XPATH)))
        except TimeoutException: captcha = None
        if captcha: raise CaptchaWebPageError(self) 
        else: pass
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    








