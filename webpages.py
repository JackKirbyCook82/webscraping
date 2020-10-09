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

class EmptyPageError(WebPageError): pass
class EmptyPageURLError(WebPageError): pass
class FailurePageError(WebPageError): pass
class CaptchaPageError(WebPageError): pass
    
    
class WebPage(ABC):    
    def __init_subclass__(cls, *args, url=None, contents={}, **kwargs):
        assert isinstance(contents, dict)
        setattr(cls, 'URL', url)
        setattr(cls, 'Contents', contents)
    
    def __repr__(self): return "{}(driver={}, timeout={})".format(self.__class__.__name__, repr(self.__driver), self.__timeout)     
    def __str__(self): return "|".join([str(self.__class__.__name__), str(self.__url)])         
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)    
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout, self.__contents = driver, timeout, {}
        self.__url = kwargs.get('url', self.URL)
        if self.__url is None: raise EmptyPageURLError(self)        

    def __getitem__(self, key): 
        try: return self.__contents[key]
        except KeyError:
            self.__contents[key] = self.Contents[key](self.__driver, self.__timeout)
            return self.__contents[key]

    def load(self, *args, **kwargs): 
        print("WebPage Loading: {}".format(str(self)))
        try: self.driver.get(str(self.url))      
        except (WebDriverException, TimeoutException) as error: 
            self.checkFailure()
            raise error
        
    def checkFailure(self):
        try: failure = WebDriverWait(self.driver, FAILURE_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, FAILURE_XPATH)))
        except TimeoutException: failure = None
        if failure: raise FailurePageError(self, str(failure.text)) 
        else: pass
    
    def checkCaptcha(self):
        try: captcha = WebDriverWait(self.driver, CAPTCHA_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, CAPTCHA_XPATH)))
        except TimeoutException: captcha = None
        if captcha: raise CaptchaPageError(self) 
        else: pass
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
    @property
    def url(self): return self.__url
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    








