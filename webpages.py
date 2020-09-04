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


class EmptyWebPageError(Exception): pass
class CaptchaWebPageError(Exception): pass
class EmptyURLError(Exception): pass


class PageCondition(object):
    def __bool__(self): return True
    def __new__(cls, webpage): 
        assert isinstance(webpage, WebPage)
        try: element = WebDriverWait(webpage.driver, cls.timeout).until(EC.presence_of_element_located((By.XPATH, cls.xpath)))    
        except (NoSuchElementException, TimeoutException, WebDriverException): return False
        condition = super().__new__(cls)
        setattr(condition, 'element', element)
        return condition
        
    @classmethod
    def create(cls, xpath, timeout):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'xpath':xpath, 'timeout':timeout})
        return wrapper
        
@PageCondition.create(xpath=failure_xpath, timeout=10)
class Failure: 
    def __str__(self): return str(self.element.text)
               
@PageCondition.create(xpath=captcha_xpath, timeout=10)
class Captcha: pass      
        

class WebPage(ABC):         
    def __getitem__(self, key): return self.__webcontrols[key]      
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__webcontrols = {key:webcontrol(driver, timeout) for key, webcontrol in self.WebControls.items()}       
        self.__url = kwargs.get('url', self.URL)
        if self.__url is None: raise EmptyURLError()        
    
    @property
    def loaded(self): 
        try: return WebDriverWait(self.driver, self.timeout).until(lambda driver: driver.current_url != notloaded_url)   
        except (NoSuchElementException, TimeoutException, WebDriverException): return False
    
    def failure(self): return Failure(self)
    def captcha(self): return Captcha(self)
        
    def load(self, *args, **kwargs): 
        print("WebPage Loading: {}".format(self.__class__.__name__))
        print(str(self.url))
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








