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


notloaded_url = 'data:,'
failure_xpath = "//div[@id='main-message']//span[@jsselect='heading']"
captcha_xpath = "//div[@class='captcha-container']"


class WebPageError(Exception):
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, '\n'.join(list(self.args))) 


class EmptyWebPageError(WebPageError): pass
class EmptyWebPageURLError(WebPageError): pass
class FailureWebPageError(WebPageError): pass
class CaptchaWebPageError(WebPageError): pass
    

class WebPageCondition(ABC):    
    def raiseException(self): raise self.Exception(str(self.webpage), str(self)) 
    
    def __bool__(self): return True
    def __init__(self, webpage): self.webpage = webpage
    def __str__(self): return "|".join([self.__class__.__name__, str(self.element.text)])
    def __new__(cls, webpage): 
        assert isinstance(webpage, WebPage)
        try: element = WebDriverWait(webpage.driver, cls.timeout).until(EC.presence_of_element_located((By.XPATH, cls.xpath)))    
        except (NoSuchElementException, TimeoutException, WebDriverException): return False
        condition = super().__new__(cls)
        setattr(condition, 'element', element)
        return condition    

    @classmethod
    def create(cls, xpath, timeout, exception):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'xpath':xpath, 'timeout':timeout, 'Exception':exception})
        return wrapper
        
    
@WebPageCondition.create(xpath=failure_xpath, timeout=10, exception=FailureWebPageError)
class Failure: pass
@WebPageCondition.create(xpath=captcha_xpath, timeout=10, exception=CaptchaWebPageError)
class Captcha: pass   
        

class WebPage(ABC):         
    def __getitem__(self, key): return self.__webcontrols[key]          
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__webcontrols = {key:webcontrol(driver, timeout) for key, webcontrol in self.WebControls.items()}       
        self.__url = kwargs.get('url', self.URL)
        if self.__url is None: raise EmptyWebPageURLError(self)        
 
    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
    def __str__(self): return "|".join([str(self.__class__.__name__), str(self.__url)])
    
    @property
    def loaded(self): 
        try: return WebDriverWait(self.driver, self.timeout).until(lambda driver: driver.current_url != notloaded_url)   
        except (NoSuchElementException, TimeoutException, WebDriverException): return False
    
    def load(self, *args, **kwargs): 
        print("WebPage Loading: {}".format(str(self)))
        self.driver.get(str(self.url))      
       
    def verify(self):
        try: Failure(self).raiseException()
        except AttributeError: pass
        try: Captcha(self).raiseException()
        except AttributeError: pass
    
    def __call__(self, *args, **kwargs): 
        if not self.loaded: raise EmptyWebPageError(self)
        return self.execute(*args, **kwargs)     
        
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








