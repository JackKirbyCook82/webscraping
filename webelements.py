# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

import re
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebElement', 'WebButton', 'WebRadioButton', 'WebRadioButton', 'WebLink', 'WebInput', 'WebSelect', 'WebElementDict', 'WebElementList', 'WebData', 'WebTable']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebElement(object): 
    def __getattr__(self, attr): return self.element.get_attribute(attr)
    def __getitem__(self, key): return self.element.get_attribute(key)
    def __bool__(self): return self.element.is_enabled() if self.element is not None else False
    def __init__(self, element): self.__element = element
    
    @property
    def element(self): return self.__element    
    @property
    def text(self): return self.element.text if self.element is not None else None
    @property
    def html(self): return self.element.get_attribute('outerHTML') if self.element is not None else None       
        
    @classmethod
    def fromdriver(cls, driver): 
        try: return cls(driver.find_element(By.XPATH, cls.xpath))
        except NoSuchElementException: return cls(None)   
    @classmethod
    def create(cls, xpath, **attrs):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath, **attrs))
        return wrapper 
  

class WebElementDict(dict):
    def __getitem__(self, key): return super().__getitem__(key.lower().replace(' ', ''))
    def __init__(self, elements):
        assert isinstance(elements, dict)
        super().__init__(elements)
    
    @classmethod
    def fromdriver(cls, driver):
        elements = {str(key):value for key, value in zip(driver.find_elements(By.XPATH, cls.keys), driver.find_elements(By.XPATH, cls.values))}
        elements = {key.lower().replace(' ', ''):cls.WebElement.fromdriver(element) for key, element in elements.items()}
        return cls(elements)               
    @classmethod
    def create(cls, keys, values, webelement, **attrs):
        assert issubclass(webelement, WebElement)
        for name, attr in attrs.items(): setattr(webelement, name, attr)
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'keys':keys, 'values':values, 'WebElement':webelement})
        return wrapper 


class WebElementList(list):
    def __init__(self, elements):
        assert isinstance(elements, list)
        super().__init__(elements)

    @classmethod
    def fromdriver(cls, driver):
        elements = [item for item in driver.find_elements(By.XPATH, cls.items)]
        elements = [cls.WebElement.fromdriver(element) for element in elements.items()]
        return cls(elements)       
    @classmethod
    def create(cls, items, webelement, **attrs):
        assert issubclass(webelement, WebElement)
        for name, attr in attrs.items(): setattr(webelement, name, attr)
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'items':items, 'WebElement':webelement})
        return wrapper 


class WebLink(WebElement):
    @property
    def url(self): return str(self.element.href)
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
    def fromdriver(cls, driver):
        try: return cls(Select(driver.find_element(By.XPATH, cls.xpath)))
        except NoSuchElementException: return cls(None)


class WebText(WebElement):
    def data(self): return self.parser(self.text)
    
    @classmethod
    def create(cls, xpath, parser=lambda x: str(x), **attrs):
        assert hasattr(parser, '__call__')
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath, parser=parser, **attrs))
        return wrapper


class WebData(WebElement):
    def data(self): 
        if isinstance(self.content, str): return [self.parser(x) for x in re.findall(self.content, self.text)]
        elif isinstance(self.content, dict): return {key:[self.parsers.get(key, self.parser)(x) for x in re.findall(pattern, self.text)] for key, pattern in self.content.items()}
        else: raise TypeError(type(self.content))

    @classmethod
    def create(cls, xpath, content, parser=lambda x: str(x), parsers={}, **attrs):
        assert isinstance(parsers, dict) and hasattr(parser, '__call__')
        assert all([hasattr(item, '__call__') for item in parsers.values()])
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath, content=content, parser=parser, parsers=parsers, **attrs))
        return wrapper         


class WebTable(WebElement): 
    def parser(self, dataframe, *args, **kwargs): return dataframe
    def table(self, *args, **kwargs): return self.parser(self.dataframe(), *args, **kwargs)    
    def dataframe(self): 
        table = pd.read_html(self.html, header=self.headerrow, index_col=self.indexcolumn)[0]
        return table.to_frame() if not isinstance(table, pd.DataFrame) else table

    @classmethod
    def create(cls, xpath, headerrow=None, indexcolumn=None, **attrs):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), dict(xpath=xpath, headerrow=headerrow, indexcolumn=indexcolumn, **attrs))
        return wrapper         
























