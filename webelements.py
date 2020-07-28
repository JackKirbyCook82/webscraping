# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebElement', 'WebButton', 'WebLink', 'WebLinkDict', 'WebLinkList', 'WebInput']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebElement(object): 
    def __init__(self, element, *args, **kwargs): self.__element = element
    @property
    def element(self): return self.__element    
    @property
    def text(self): return self.__element.text
    @property
    def html(self): return self.__element.get_attribute('outerHTML')   
        
    @classmethod
    def fromdriver(cls, driver, *args, **kwargs): return cls(driver.find_element(By.XPATH, cls.xpath))
    @classmethod
    def fromelement(cls, element, *args, **kwargs): return cls(element)    
    
    @classmethod
    def create(cls, xpath, **xpaths):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath, **xpaths))
        return wrapper 
    
    
class WebClickable(WebElement):    
    def click(self): self.element.click()

class WebButton(WebClickable): pass
class WebRadioButton(WebClickable): pass
class WebCheckBox(WebClickable): pass

    
class WebInput(WebElement):
    def click(self): self.element.click()
    def clear(self): self.element.clear()
    def fill(self, content): self.element.sendKeys(content)       
    

class WebLink(WebElement):
    def click(self): self.element.click()  
    

class WebLinkDict(WebElement):
    def __new__(cls, elements, *args, **kwargs): return {key:WebLink.fromelement(value, *args, **kwargs) for key, value in elements.items()}
    @classmethod
    def fromdriver(cls, driver, *args, **kwargs):
        elements = {str(key):value for key, value in zip(driver.find_elements(By.XPATH, cls.keys), driver.find_elements(By.XPATH, cls.xpath))}
        return cls(elements, *args, **kwargs)

class WebLinkList(WebElement):
    def __new__(cls, elements, *args, **kwargs): return [WebLink.fromelement(value, *args, **kwargs) for key, value in elements.items()]
    @classmethod
    def fromdriver(cls, driver, *args, **kwargs):
        elements = [value for key, value in zip(driver.find_elements(By.XPATH, cls.keys), driver.find_elements(By.XPATH, cls.xpath))]
        return cls(elements, *args, **kwargs)
    
    
class WebSelect(WebElement):
    @classmethod
    def fromdriver(cls, driver, *args, **kwargs):
        element = Select(driver.driver.find_element(By.XPATH, cls.xpath))
        return cls(element, *args, **kwargs)

    @property
    def options(self): return self.element.options()
    def clear(self): self.element.deselect_all()
    def select(self, value): self.element.select_by_value(value)
     
    
class WebTable(WebElement):
    pass





























