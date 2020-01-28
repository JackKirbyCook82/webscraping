# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   Webdriver Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver', 'WebElement', 'WebElements']
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


class WebElement(ABC):
    def __init__(self, driver): self.__element = driver.find_element(By.XPATH, self.xpath)
    
    def click(self): self.__element.click()
    def clear(self): self.__element.clear()
    
    @property
    def enabled(self): return self.__element.is_enabled()
    @property
    def selected(self): return self.__element.is_selected()
    @property
    def text(self): return self.__element.text
    
    @classmethod
    def create(cls, xpath):  
        def wrapper(subclass):
            name = subclass.__name__
            bases = (subclass, cls)
            newsubclass = type(name, bases, dict(xpath=xpath))
            return newsubclass
        return wrapper 


class WebElements(ABC):
    def __init__(self, driver): self.__elements = driver.find_elements(By.XPATH, self.xpath) 
    def __getitem__(self, index): return WebElement(self.__elements[index])
    def __iter__(self): 
        for element in self.__elements: yield WebElement(element) 
    
    @classmethod
    def create(cls, xpath):  
        def wrapper(subclass):
            name = subclass.__name__
            bases = (subclass, cls)
            newsubclass = type(name, bases, dict(xpath=xpath))
            return newsubclass
        return wrapper 

























    