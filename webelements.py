# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

import pandas as pd
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver import Element, Chrome

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebElement', 'WebButton', 'WebRadioButton', 'WebRadioButton', 'WebLink', 'WebInput', 'WebSelect', 'WebElementDict', 'WebElementList', 'WebData', 'WebTable']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebElement(object): 
    def __getattr__(self, attr): return self.__element.get_attribute(attr)
    def __bool__(self): return self.element.is_enabled()
    def __init__(self, element): self.__element = element
    def __new__(cls, item):
        if isinstance(item, Element): return super().__new__(cls) 
        elif isinstance(item, Chrome): return cls.fromdriver(item)
        else: raise TypeError(item)

    @property
    def element(self): return self.__element    
    @property
    def html(self): return self.__element.get_attribute('outerHTML')       
        
    @classmethod
    def fromdriver(cls, driver): return cls(driver.find_element(By.XPATH, cls.xpath))
    @classmethod
    def fromelement(cls, element): return cls(element)        
    @classmethod
    def create(cls, xpath):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath))
        return wrapper 
  

class WebElementDict(dict):
    def __getitem__(self, key): return super().__getitem__(key.lower().replace(' ', ''))
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


class WebLink(WebElement):
    @property
    def url(self): return str(self.href)
    def click(self): self.element.click()  


class WebClickable(WebElement):    
    def click(self): self.element.click()

class WebButton(WebClickable): pass
class WebRadioButton(WebClickable): pass
class WebCheckBox(WebClickable): pass

    
class WebInput(WebElement):
    def click(self): self.element.click()
    def clear(self): self.element.clear()
    def fill(self, content): self.element.sendKeys(content)       
    

class WebSelect(WebElement):
    def __len__(self): return len(self.element.options())    
    def keys(self): return [element.text for element in self.element.options()]
    def clear(self): self.element.deselect_all()
    def isel(self, index): self.element.select_by_index(index)
    def sel(self, value): self.element.select_by_visible_text(value)

    @classmethod
    def fromdriver(cls, driver, *args, **kwargs):
        element = Select(driver.driver.find_element(By.XPATH, cls.xpath))
        return cls(element, *args, **kwargs)


class WebData(WebElement):
    def __getitem__(self, key): return self.data[key]    
    def text(self): return self.__element.text
    def data(self): 
        if isinstance(self.data, str): return [self.parser(x) for x in re.findall(self.data, self.text)]
        elif isinstance(self.data, dict): return {key:[self.parsers.get(key, self.parser)(x) for x in re.findall(pattern, self.text)] for key, pattern in self.data.items()}
        else: raise TypeError(type(self.data))

    @classmethod
    def create(cls, xpath, *args, data, parser=lambda x: str(x), parsers={}, **kwargs):
        assert isinstance(parsers, dict) and hasattr(parser, '__call__')
        assert all([hasattr(item, '__call__') for item in parsers.values()])
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath, data=data, parser=parser, parsers=parsers))
        return wrapper         


class WebTable(WebElement): 
    def parser(self, dataframe): return dataframe
    def table(self): return self.parser(self.dataframe)    
    def dataframe(self): 
        table = pd.read_html(self.html, header=self.headerrow, index_col=self.indexcolumn)
        return table.to_frame() if not isinstance(table, pd.DataFrame) else table

    @classmethod
    def create(cls, xpath, *args, headerrow=None, indexcolumn=None, **kwargs):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath, headerrow=headerrow, indexcolumn=indexcolumn))
        return wrapper         
























