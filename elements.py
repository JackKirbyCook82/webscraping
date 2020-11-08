# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

import pandas as pd
from functools import update_wrapper
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Clickable', 'Link', 'Text', 'ID', 'Table', 'Input', 'Selection', 'Captcha']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


REGISTRY = []


class EmptyElementError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])
  
    
def elementAttribute(mainattr): return mainattr
def elementFunction(mainfunc):
    def wrapper(self, *args, **kwargs): return mainfunc(*args, **kwargs)
    update_wrapper(wrapper, mainfunc)
    return wrapper
    
    
class Element(object):
    def __init_subclass__(cls, **attrs):
        for name, attr in attrs.items(): 
            if hasattr(attr, '__call__'): setattr(cls, name, elementFunction(attr))            
            else: setattr(cls, name, elementAttribute(attr))
        REGISTRY.append(cls)
 
    def __init__(self, domelement): self.__domelement = domelement
    def __bool__(self): return self.__domelement is not None
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self)))    
    
    @property
    def DOMElement(self): 
        if not self: raise EmptyElementError(str(self)) 
        else: return self.__domelement

    @property
    def text(self): return self.DOMElement.text 
    @property
    def ID(self): return self.DOMElement.get_attribute('id')
    @property
    def html(self): return self.DOMElement.get_attribute('outerHTML')   
    @property
    def link(self): return self.DOMElement.get_attribute('href')
    @property
    def enabled(self): return self.DOMElement.is_enabled()
    @property
    def visible(self): return self.DOMElement.is_displayed()    
    @property
    def stale(self):
        try: self.DOMElement.is_enabled()
        except StaleElementReferenceException: return True
        return False


class Clickable(Element): 
    def click(self): self.DOMElement.click()


class Selection(Element, mapping={}):
    def __len__(self): return len(self.select.options())   
    def __init__(self, domelement):
        super().__init__(domelement)
        self.__select = Select(domelement)
    
    @property
    def select(self):
        if not self: raise EmptyElementError(str(self))
        else: return self.__select
    
    def keys(self): return [item.text for item in self.select.options()]
    def click(self): self.select.click()      
    def clear(self): self.select.deselect_all()    
    def isel(self, index): self.select.select_by_index(index)
    def tsel(self, text): self.select.select_by_visible_text(text)
    def vsel(self, value): self.select.select_by_value(value)
    def sel(self, x):
        if isinstance(x, int): self.isel(x)
        elif isinstance(x, str): 
            y = self.mapping.get(x, x)
            try: self.vsel(y)
            except NoSuchElementException: self.tsel(y)
        else: raise TypeError(type(x).__name__)


class Input(Element):
    def clear(self): self.DOMElement.clear()
    def fill(self, text): 
        self.clear()
        self.DOMElement.sendKeys(text)       


class Link(Element):
    @property
    def data(self): return str(self.link)
    @property
    def url(self): return str(self.link) 


class Text(Element, parser=lambda x: str(x)):
    @property
    def data(self): return self.parser(self.text)
    

class ID(Element):
    @property
    def data(self): return str(self.ID)


class Table(Element, tableindex=0, headerrow=None, indexcolumn=None, parser=lambda x: x):
    @property
    def dataframe(self): 
        tables = pd.read_html(self.html, header=self.headerrow, index_col=self.indexcolumn)
        if not tables: return None
        return tables[self.tableindex].to_frame() if not isinstance(tables[self.tableindex], pd.DataFrame) else tables[self.tableindex]   
    @property
    def table(self):
        dataframe = self.dataframe
        if dataframe is not None: return self.parser(dataframe)   
        else: return None    
        
        
class Captcha(Element): pass








    
