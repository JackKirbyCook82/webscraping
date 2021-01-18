# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDOM Objects
@author: Jack Kirby Cook

"""

import pandas as pd
from abc import ABC, abstractmethod
from functools import update_wrapper
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Refusal', 'Captcha', 'Clickable', 'Input', 'Selection', 'Link', 'Text', 'Table']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


def asAttribute(mainattr): return mainattr
def asFunction(mainfunc):
    def wrapper(self, *args, **kwargs): return mainfunc(*args, **kwargs)
    update_wrapper(wrapper, mainfunc)
    return wrapper


class EmptyWebDOMError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])
  
class EmptyWebElementError(EmptyWebDOMError): pass
class EmptyWebTreeError(EmptyWebDOMError): pass
      
    
class WebDOM(ABC):     
    def __init_subclass__(cls, **kwargs): 
        if 'scrape' in kwargs.keys():
            assert not hasattr(cls, 'scrape')
            setattr(cls, 'scrape', kwargs.pop('scrape'))
        for name, attr in kwargs.items(): 
            if hasattr(attr, '__call__'): setattr(cls, name, asFunction(attr))            
            else: setattr(cls, name, asAttribute(attr))      
                        
    def __new__(cls, DOM):
        assert hasattr(cls, 'scrape')
        assert getattr(cls, 'scrape') is not None
        return super().__new__(cls)    
        
    def __init__(self, DOM): self.__DOM = DOM
    def __bool__(self): return self.__DOM is not None    
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self)))  
    
    @property
    def DOM(self): return self.__DOM        

    @property
    @abstractmethod
    def text(self): pass  
    @property
    @abstractmethod
    def link(self): pass
    
    
class WebElement(WebDOM, scrape='dynamic'):
    @property
    def DOMElement(self): 
        if not self: raise EmptyWebElementError(str(self)) 
        else: return self.DOM
        
    @property
    def text(self): return self.DOMElement.text 
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


class WebTree(WebDOM, scrape='static'):
    @property
    def DOMTree(self):
        if not self: raise EmptyWebTreeError(str(self))
        else: return self.DOM
          
    @property
    def text(self): return str(self.DOMTree.text_content())   
    @property
    def link(self): return str(self.DOMTree.attrib['href'])


class WebVariant(WebDOM, scrape=None):
    @classmethod
    def asDynamic(cls): return type(cls.__name__, (WebElement,), dict(cls.__dict__))
    @classmethod
    def asStatic(cls): return type(cls.__name__, (WebTree,), dict(cls.__dict__))       


class Refusal(WebTree): pass
class Captcha(WebElement): pass

    
class Clickable(WebElement): 
    def click(self): self.DOMElement.click()


class Selection(WebElement, mapping={}):
    def __len__(self): return len(self.select.options())   
    def __init__(self, domelement):
        super().__init__(domelement)
        self.__select = Select(domelement)
    
    @property
    def select(self):
        if not self: raise EmptyWebElementError(str(self))
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


class Input(WebElement):
    def clear(self): self.DOMElement.clear()
    def fill(self, text): 
        self.clear()
        self.DOMElement.send_keys(text)       


class Link(WebVariant, parser=lambda x: x):
    @property
    def url(self): return str(self.link) 
    @property
    def data(self): return self.parser(self.link)


class Text(WebVariant, parser=lambda x: x): 
    @property
    def data(self): return self.parser(self.text)
    

class Table(WebVariant, tableindex=0, headerrow=0, indexcolumn=None, parser=lambda x: x):
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
        
        



    
