# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

import pandas as pd
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Clickable', 'Link', 'Text', 'Table', 'Input', 'Selection']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyElementError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])
    
    
class Element(object):
    def __init_subclass__(cls, **attrs):
        setattr(cls, 'attrs', attrs)
        
    def __bool__(self): return self.__element is not None
    def __init__(self, element): self.__element = element
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self)))    
    def __getattr__(self, attr):
        try: return self.attrs[attr]
        except KeyError: raise AttributeError(attr)

    @classmethod
    def update(cls, **attrs): cls.attrs.update(attrs)

    @property
    def element(self): 
        if not self: raise EmptyElementError(str(self)) 
        else: return self.__element

    @property
    def text(self): return self.element.text 
    @property
    def html(self): return self.element.get_attribute('outerHTML')   
    @property
    def enabled(self): return self.element.is_enabled()
    @property
    def visible(self): return self.element.is_displayed()    
    @property
    def stale(self):
        try: self.element.is_enabled()
        except StaleElementReferenceException: return True
        return False


class Clickable(Element): 
    def click(self): self.element.click(())


class Selection(Element):
    def __len__(self): return len(self.select.options())   
    def __init__(self, element):
        super().__init__(element)
        self.__select = Select(element)
    
    @property
    def select(self):
        if not self: raise EmptyElementError(str(self))
        else: return self.__select
    
    def click(self): self.select.click()      
    def clear(self): self.select.deselect_all()    
    def keys(self): return [item.text for item in self.select.options()]
    def isel(self, index): self.select.select_by_index(index)
    def tsel(self, text): self.select.select_by_visible_text(text)
    def vsel(self, value): self.select.select_by_value(value)
    def sel(self, x):
        if isinstance(x, int): self.isel(x)
        elif isinstance(x, str): 
            try: y = self.mapping.get(x, x)
            except AttributeError: y = x
            try: self.vsel(y)
            except NoSuchElementException: self.tsel(y)
        else: raise TypeError(type(x).__name__)


class Input(Element):
    def clear(self): self.element.clear()
    def fill(self, text): 
        self.clear()
        self.element.sendKeys(text)       


class Link(Element):
    @property
    def data(self): return str(self.element.href)
    @property
    def url(self): return str(self.element.href) 


class Text(Element, parser=lambda x: str(x)):
    @property
    def data(self): 
        try: return self.parser(self.text)
        except EmptyElementError: return None


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
        

        
        
        
        
        
        