# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   Webdriver Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
import time
from selenium import webdriver

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver', 'WebPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebDriver(ABC):
    webdrivers = {'chrome':webdriver.Chrome, 'firefox':webdriver.Firefox}
    weboptions = {'chrome':webdriver.ChromeOptions, 'firefox':webdriver.FirefoxOptions}

    def __init__(self, file, browser, *args, delay=None, patience=None, **kwargs): 
        self.__file, self.__browser =  file, browser
        self.__patience = patience
        self.__sleep = delay
    
    def __call__(self, url, *args, **kwargs): 
        self.__driver = self.webdrivers[self.__browser.lower()](executable_path=self.__file, options=self.weboptions[self.__browser]()) 
        if self.__patience: self.__driver.set_page_load_timeout(self.__patience)
        self.__driver.maximize_window()
        self.__driver.get(str(url))
        yield from self.execute(*args, **kwargs)
        self.__driver.quit()
    
    @abstractmethod
    def execute(self, *args, **kwargs): pass

    @property
    def driver(self): return self.__driver    
    @property
    def url(self): return self.__driver.current_url
    @property
    def html(self): return self.__driver.page_source
    
    def back(self): self.__driver.back
    def forward(self): self.__driver.forward
    def sleep(self): time.sleep(self.__sleep)
    def refresh(self): self.__driver.refresh


class WebPage(ABC):
    def __init__(self, *args, driver, **kwargs): 
        self.__data = {datatype:{datakey:dataelement for datakey, dataelement in datavalue.items()} for datatype, datavalue in self.registry().items()}
    def __call__(self, *args, **kwargs): 
        data = {datatype:{datakey:dataelement(*args, **kwargs) for datakey, dataelement in datavalue.items()} for datatype, datavalue in self.__data.items()}
        return self.execute(*args, **data, **kwargs)
    
    @abstractmethod
    def execute(self, *args, **kwargs): pass    
    
    __registry = {}
    @classmethod
    def registry(cls): return cls.__registry
    @classmethod    
    def register(cls, datatype, datakey):
        def wrapper(dataelement):
            cls.__registry[datatype][datakey] = dataelement
            return dataelement
        return wrapper
    
    




    