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
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, '\n'.join(list(self.args))) 


class EmptyWebPageError(WebPageError): pass
class EmptyWebPageURLError(WebPageError): pass
class FailureWebPageError(WebPageError): pass
class CaptchaWebPageError(WebPageError): pass


def checkLoadFailure(webpage):
    try: WebDriverWait(webpage.driver, TIMEOUT).until(lambda driver: driver.current_url != NOTLOADED_URL)   
    except (NoSuchElementException, TimeoutException, WebDriverException): return False   
    raise EmptyWebPageError(str(webpage))
    
def checkPageFailure(webpage):
    try: element = WebDriverWait(webpage.driver, TIMEOUT).until(EC.presence_of_element_located((By.XPATH, FAILURE_XPATH)))    
    except (NoSuchElementException, TimeoutException, WebDriverException): return False
    raise FailureWebPageError(str(webpage), str(element.text))

def checkCaptcha(webpage):
    try: WebDriverWait(webpage.driver, TIMEOUT).until(EC.presence_of_element_located((By.XPATH, CAPTCHA_XPATH)))    
    except (NoSuchElementException, TimeoutException, WebDriverException): return False
    raise CaptchaWebPageError(str(webpage))


class WebPage(ABC):         
    def __getitem__(self, key): return self.__webcontrols[key]          
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)    
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__webcontrols = {key:webcontrol(driver, timeout) for key, webcontrol in self.WebControls.items()}       
        self.__url = kwargs.get('url', self.URL)
        if self.__url is None: raise EmptyWebPageURLError(self)        
 
    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
    def __str__(self): return "|".join([str(self.__class__.__name__), str(self.__url)])

    def load(self, *args, **kwargs): 
        print("WebPage Loading: {}".format(str(self)))
        self.driver.get(str(self.url))      
            
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
    @property
    def url(self): return self.__url
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    
    @classmethod
    def create(cls, url=None, **webcontrols):
        webcontrols = {key:value for key, value in webcontrols.items() if value is not None}
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'URL':url, 'WebControls':webcontrols})
        return wrapper








