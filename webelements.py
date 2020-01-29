# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

from selenium.webdriver.common.by import By

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebElement', 'WebButton', 'WebLink', 'WebLinks', 'WebSelect', 'WebInput', 'WebData', 'WebTable']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebElement(object): 
    @property
    def element(self): return self.__element
    def __init__(self, *args, **kwargs): 
        try: self.__element = self.fromelement(*args, **kwargs)
        except TypeError: self.__element = self.fromdriver(*args, **kwargs)
    
    def fromdriver(self, *args, driver, **kwargs): return driver.find_element(By.XPATH, self.xpath)
    def fromelement(self, *args, element, **kwargs): return element

    @classmethod
    def create(cls, xpath, **kwargs):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath, **kwargs))
        return wrapper 
    
    
class WebButton(WebElement):    
    def click(self): self.element.click()


class WebLink(WebElement):
    def click(self): self.element.click()
    
    
class WebLinks(WebElement):
    def fromdriver(self, *args, driver, **kwargs): 
        try: return {key:value for key, value in zip(driver.find_elements(By.XPATH, self.keys), driver.find_elements(By.XPATH, self.xpath))}
        except AttributeError: return {index:value for index, value in enumerate(driver.find_elements(By.XPATH, self.xpath), start=0)}
    def click(self, key): self.element[key].click()   
    def __getitem__(self, key): return WebLink(element=self.element[key])
    def __iter__(self): 
        for key, element in self.element.items(): yield key, WebLink(element=element)
    

class WebSelect(WebElement):
    def fromdriver(self, *args, driver, **kwargs): 
        return {key:value for key, value in zip(driver.find_elements(By.XPATH, self.keys), driver.find_elements(By.XPATH, self.xpath))}
    def select(self, key): self.element[key].click()   
    def selections(self): return {key:element.is_selected() for key, element in self.element.items()}
    

class WebInput(WebElement):
    def click(self): self.element.click()
    def clear(self): self.element.clear()


class WebData(WebElement):
    def __call__(self): pass


class WebTable(WebElement):
    def __call__(self): pass




