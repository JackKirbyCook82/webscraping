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
__all__ = ['WebElement', 'WebButton', 'WebRadioButton', 'WebRadioButton', 'WebLink', 'WebInput', 'WebSelect', 'WebElementDict', 'WebElementList']
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
    def create(cls, xpath):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath))
        return wrapper 
  

class WebElementDict(dict):
    def __getitem__(self, key): super().__getitem__(key.lower().replace(' ', ''))
    def __init__(self, **elements):
        super().__init__({key.lower().replace(' ', ''):self.webelement.fromelement(element) for key, element in elements.items()})
    
    @classmethod
    def fromdriver(cls, driver, *args, **kwargs):
        elements = {str(key):value for key, value in zip(driver.find_elements(By.XPATH, cls.keys), driver.find_elements(By.XPATH, cls.values))}
        return cls(**elements)
           
    @classmethod
    def create(cls, keys, values, webelement):
        assert issubclass(webelement, WebElement)
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(keys=keys, values=values, webelement=webelement))
        return wrapper 


class WebElementList(list):
    def __init__(self, *elements):
        super().__init__([self.webelement.fromelement(element) for element in elements.items()])

    @classmethod
    def fromdriver(cls, driver, *args, **kwargs):
        elements = [item for item in driver.find_elements(By.XPATH, cls.items)]
        return cls(*elements)
    
    @classmethod
    def create(cls, items, webelement):
        assert issubclass(webelement, WebElement)
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(items=items, webelement=webelement))
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
    

class WebSelect(WebElement):
    @classmethod
    def fromdriver(cls, driver, *args, **kwargs):
        element = Select(driver.driver.find_element(By.XPATH, cls.xpath))
        return cls(element, *args, **kwargs)

    @property
    def options(self): return self.element.options()
    def clear(self): self.element.deselect_all()
    def select(self, value): self.element.select_by_value(value)



























