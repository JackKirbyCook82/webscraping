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


PAGEFAILURE_XPATH = r"//div[@id='main-message']//span[@jsselect='heading']"

class EmptyWebPageError(Exception): pass


class WebPage(ABC):        
    def __getitem__(self, key): return self.__webelements[key]      
    def __call__(self, *args, **kwargs): 
        print("WebPage Executing: {}".format(self.__class__.__name__))
        return self.execute(*args, **kwargs)
    
    def __init__(self, driver, *args, **kwargs): 
        self.__webelements = {key:webelement(driver) for key, webelement in self.WebElements.items()}
        self.__driver = driver
        
    def load(self, *args, timeout, **kwargs):  
        url = kwargs.pop('url', self.url)
        assert url is not None
        print("WebPage Loading: {}".format(self.__class__.__name__))
        print(str(url))
        self.getpage(url, *args, timeout=timeout, **kwargs)      
        self.getelements(*args, timeout=timeout, **kwargs)
        print("WebPage Loaded: {}".format(self.__class__.__name__))     
              
    def getpage(self, url, *args, timeout, **kwargs): 
        self.__driver.get(str(url))       
        try: 
            pagefailure = WebDriverWait(self.__driver, timeout).until(EC.presence_of_element_located((By.XPATH, PAGEFAILURE_XPATH)))
            print('WebPage Failure: {}'.format(self.__class__.__name__))
            print(str(pagefailure.text))
            raise EmptyWebPageError(str(pagefailure.text))        
        except TimeoutException:
            print('WebPage Success: {}'.format(self.__class__.__name__))
            
    def getelements(self, *args, timeout, **kwargs):
        for webelement in self.loadWebElements: 
            self.__webelements[webelement].load(timeout)    
       
    @abstractmethod
    def execute(self, *args, **kwargs): pass        
        
    @classmethod
    def create(cls, webelements, *args, url=None, load=[], **kwargs):
        assert isinstance(webelements, dict)
        def wrapper(subclass): 
            attrs = {'url':url, 'loadWebElements':tuple(load), 'WebElements':webelements}
            return type(subclass.__name__, (subclass, cls), attrs)
        return wrapper  









