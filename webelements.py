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
    @classmethod
    def fromdriver(cls, driver, *args, **kwargs):
        element = Select(driver.driver.find_element(By.XPATH, cls.xpath))
        return cls(element, *args, **kwargs)

    @property
    def options(self): return self.element.options()
    def clear(self): self.element.deselect_all()
    def select(self, value): self.element.select_by_value(value)


class WebData(WebElement):
    def __getitem__(self, key): return self.data[key]
    @property
    def text(self): return self.__element.text
    @property
    def data(self): 
        if isinstance(self.regex, str): data = [self.parser(x) for x in re.findall(self.regex, self.text)]
        elif isinstance(self.regex, dict): data = {key:[self.parsers.get(key, self.parser)(x) for x in re.findall(pattern, self.text)] for key, pattern in self.regex.items()}
        else: raise TypeError(type(self.regex))
        return data[0] if isinstance(data, list) and len(data) == 1 else data

    @classmethod
    def create(cls, xpath, regex, parser=lambda x: str(x), parsers={}, **kwargs):
        assert isinstance(parsers, dict) and hasattr(parser, '__call__')
        assert all([hasattr(item, '__call__') for item in parsers.values()])
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath, regex=regex, parser=parser, parsers=parsers))
        return wrapper         


class WebTable(WebElement): 
    def dataframe(self): 
        table = pd.read_html(self.html, header=self.headerrow, index_col=self.indexcolumn)
        return table.to_frame() if not isinstance(table, pd.DataFrame) else table
























