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


FAILURE_XPATH = r"//div[@id='main-message']//span[@jsselect='heading']"
FAILURE_TIMEOUT = 25

class EmptyWebPageError(Exception): pass
class EmptyURLError(Exception): pass


class WebPage(ABC):        
    def __getitem__(self, key): return self.__webelements[key]      
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__webelements = {key:webelement(driver, timeout) for key, webelement in self.WebElements.items()}
        self.__driver, self.__timeout = driver, timeout
        self.__url = kwargs.get('url', self.URL)
        if self.__url is None: raise EmptyURLError()
               
    def load(self):  
        print("WebPage Loading: {}".format(self.__class__.__name__))
        print(str(self.url))
        self.driver.get(str(self.url))
        try: failure = self.check()
        except TimeoutException: failure = None
        if failure is None: print('WebPage Success: {}'.format(self.__class__.__name__))  
        else: print('WebPage Failure: {}'.format(self.__class__.__name__))
        if failure: raise EmptyWebPageError(failure)          
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
    @property
    def url(self): return self.__url
    def check(self): 
        failure = WebDriverWait(self.driver, FAILURE_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, FAILURE_XPATH)))
        return str(failure.text)
       
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    
    @classmethod
    def create(cls, webelements, *args, url=None, **kwargs):
        assert isinstance(webelements, dict)
        def wrapper(subclass): 
            attrs = {'URL':url, 'WebElements':webelements}
            return type(subclass.__name__, (subclass, cls), attrs)
        return wrapper  









