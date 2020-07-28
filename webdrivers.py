# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   Webdriver Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
import time
import random
from selenium import webdriver

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebDriver(ABC):
    webdrivers = {'chrome':webdriver.Chrome, 'firefox':webdriver.Firefox}
    weboptions = {'chrome':webdriver.ChromeOptions, 'firefox':webdriver.FirefoxOptions}

    def __init__(self, file, browser, *args, mindelay=5, maxdelay=20, patience=100, **kwargs): 
        self.__file, self.__browser =  file, browser
        self.__patience = patience
        self.__mindelay, self.__maxdelay = mindelay, maxdelay
    
    def __call__(self, url, *args, **kwargs): 
        self.__driver = self.webdrivers[self.__browser.lower()](executable_path=self.__file, options=self.weboptions[self.__browser]()) 
        self.__driver.set_page_load_timeout(self.__patience)
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
    def sleep(self): time.sleep(random.randint(self.__mindelay, self.__maxdelay))
    def refresh(self): self.__driver.refresh





    