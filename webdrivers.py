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
__all__ = ['WebDriver', 'WebCrawler', 'WebElement', 'WebElements']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebDriver(ABC):
    webdrivers = {'chrome':webdriver.Chrome, 'firefox':webdriver.Firefox}
    weboptions = {'chrome':webdriver.ChromeOptions, 'firefox':webdriver.FirefoxOptions}

    def __new__(cls, *args, delay=None, **kwargs):
        instance = super().__new__(cls)
        instance.factory(Sleeper(delay))
        return instance

    @classmethod
    def factory(cls, sleeper):
        cls.sleeper = sleeper
        for function_name in ['click', 'forward', 'back']: setattr(cls, function_name, cls.sleeper(getattr(cls, function_name)))

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
    def forward(self): self.driver.forward()
    def back(self): self.driver.back()


class WebCrawler(WebDriver):
    keyformat = lambda crawlnum, pagenum: "{}|{}".format(crawlnum, pagenum)

    def execute(self, *args, crawlxpath, pagexpath, crawlnum=0, pagenum=0, **kwargs):
        for weblink in WebElements.fromxpath(self.driver, pagexpath):
            self.click(weblink)
            yield self.keyformat(crawlnum=crawlnum, pagenum=pagenum), self.driver.getpage()
            pagenum = pagenum + 1
            self.back()
        nextweblink = WebElement.fromxpath(self.driver, crawlxpath)
        if nextweblink:
            self.click(nextweblink)
            self.execute(*args, crawlxpath=crawlxpath, pagexpath=pagexpath, crawlnum=crawlnum+1, pagenum=pagenum, **kwargs)    


class WebElement(object):
    def __init__(self, element): self.__element = element
    def __call__(self): self.__element.click()
    def click(self): self.__element.click()
    @classmethod
    def fromxpath(cls, driver, xpath): return cls(driver.find_element(By.XPATH, xpath))


class WebElements(object):
    def __init__(self, *elements): self.__elements = elements
    def __getitem__(self, index): return WebElement(self.__elements[index])
    def __iter__(self): 
        for element in self.__elements: yield WebElement(element) 
    @classmethod
    def fromxpath(cls, driver, xpath): return cls(*driver.find_element(By.XPATH, xpath))



























    