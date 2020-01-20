# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   Webdriver Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By

from webscraping.sleeper import Sleeper

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver', 'WebLink', 'WebLinks']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebDriver(ABC):
    webdrivers = {'chrome':webdriver.Chrome, 'firefox':webdriver.Firefox}
    weboptions = {'chrome':webdriver.ChromeOptions, 'firefox':webdriver.FirefoxOptions}

    def __new__(cls, *args, delay=None, **kwargs):
        instance = super().__new__(cls)
        instance.sleeper = Sleeper(delay)
        instance.click = instance.sleeper(instance.click)
        instance.foward = instance.sleeper(instance.foward)
        instance.back = instance.sleeper(instance.back)
        return instance

    def __init__(self, file, browser, *args, **kwargs): self.__file, self.__browser =  file, browser
    def __call__(self, url, *args, **kwargs): 
        self.__driver = self.webdrivers[self.__browser.lower()](executable_path=self.__file, options=self.weboptions[self.__browser]()) 
        self.__driver.get(str(url))
        yield from self.execute(*args, **kwargs)
        self.__driver.quit()
    
    @abstractmethod
    def execute(self, *args, **kwargs): pass

    @property
    def driver(self): return self.__driver    
    def getpage(self): return self.__driver.page_source    
    
    def click(self, element): element.click()
    def foward(self): self.driver.foward()
    def back(self): self.driver.back()


class WebLink(object):
    def __init__(self, link): self.__link = link
    def __call__(self): self.__link.click()
    def click(self): self.__link.click()
    @classmethod
    def fromxpath(cls, driver, xpath): return cls(driver.find_element(By.XPATH, xpath))


class WebLinks(object):
    def __init__(self, *links): self.__links = links
    def __getitem__(self, index): return WebLink(self.__links[index])
    def __iter__(self): 
        for link in self.__links: yield WebLink(link) 
    @classmethod
    def fromxpath(cls, driver, xpath): return cls(*driver.find_element(By.XPATH, xpath))



























    