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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


NOTLOADED_URL = 'data:,'
FAILURE_XPATH = "//div[@id='main-message']//span[@jsselect='heading']"
CAPTCHA_XPATH = "//div[@class='captcha-container']" 
TIMEOUT = 10

class WebPageError(Exception):
    def __str__(self):  
        string = "{}: {}".format(self.__class__.__name__, self.args[0])
        return string if not self.args[1:] else "\n".join([string, *self.args[1:]])

class EmptyWebPageError(WebPageError): pass
class EmptyWebPageURLError(WebPageError): pass
class FailureWebPageError(WebPageError): pass
class CaptchaWebPageError(WebPageError): pass


def checkLoadFailure(webpage, terminate):
    try: 
        WebDriverWait(webpage.driver, TIMEOUT).until(lambda driver: driver.current_url == NOTLOADED_URL)   
        if terminate: raise EmptyWebPageError(str(webpage))
        else: return True
    except (NoSuchElementException, TimeoutException, WebDriverException): return False   
    
def checkPageFailure(webpage, terminate):
    try: 
        element = WebDriverWait(webpage.driver, TIMEOUT).until(EC.presence_of_element_located((By.XPATH, FAILURE_XPATH)))    
        if terminate: raise FailureWebPageError(str(webpage), str(element.text))
        else: return True
    except (NoSuchElementException, TimeoutException, WebDriverException): return False
    
def checkCaptcha(webpage, terminate):
    try: 
        WebDriverWait(webpage.driver, TIMEOUT).until(EC.presence_of_element_located((By.XPATH, CAPTCHA_XPATH)))    
        if terminate: raise CaptchaWebPageError(str(webpage))
        else: return True
    except (NoSuchElementException, TimeoutException, WebDriverException): return False
    
    
class WebPage(ABC):    
    def __init_subclass__(cls, *args, url=None, actions={}, **kwargs):
        assert isinstance(actions, dict)
        setattr(cls, 'URL', url)
        setattr(cls, 'WebActions', actions)
    
    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
    def __str__(self): return "|".join([str(self.__class__.__name__), str(self.__url)])    
    def __getitem__(self, key): return self.__webactions[key]          
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)    
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__webactions = {key:value(driver, timeout) for key, value in self.WebActions.items()}       
        self.__url = kwargs.get('url', self.URL)
        if self.__url is None: raise EmptyWebPageURLError(self)        

    def load(self, *args, **kwargs): 
        print("WebPage Loading: {}".format(str(self)))
        self.driver.get(str(self.url))      
     
    def isLoaded(self, terminate=False): return not checkLoadFailure(self, terminate)
    def isFailure(self, terminate=False): return checkPageFailure(self, terminate)
    def isCaptcha(self, terminate=False): return checkCaptcha(self, terminate)
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
    @property
    def url(self): return self.__url
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    








