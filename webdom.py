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
from lxml.html import tostring

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Captcha', 'Clickable', 'Input', 'Selection', 'Link', 'Text', 'Table']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyDOMError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])
  
class EmptyElementError(EmptyDOMError): pass
class EmptyTreeError(EmptyDOMError): pass
    
    
def asAttribute(mainattr): return mainattr
def asFunction(mainfunc):
    def wrapper(self, *args, **kwargs): return mainfunc(*args, **kwargs)
    update_wrapper(wrapper, mainfunc)
    return wrapper
  
    
class DOM(ABC):     
    def __init_subclass__(cls, scrape=None, **attrs): 
        if scrape is not None: 
            assert not hasattr(cls, 'scrape')
            setattr(cls, 'scrape', scrape)
        for name, attr in attrs.items(): 
            if hasattr(attr, '__call__'): setattr(cls, name, asAttribute(attr))            
            else: setattr(cls, name, asFunction(attr))      

    @classmethod
    def create(cls, **attrs): return type(cls.__name__, (cls,), {}, **attrs)    
    
    def __new__(cls, domcontent):
        assert hasattr(cls, 'scrape')
        return super().__new__(cls)
    
    def __init__(self, domcontent): self.__DOMContent = domcontent
    def __bool__(self): return self.__domcontent is not None
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self)))  
    
    @property
    def DOMContent(self): return self.__domcontent        

    @property
    @abstractmethod
    def html(self): pass    
    @property
    @abstractmethod
    def text(self): pass  
    @property
    @abstractmethod
    def link(self): pass
    
    
class Element(DOM, scrape='dynamic'):
    @property
    def DOMElement(self): 
        if not self: raise EmptyElementError(str(self)) 
        else: return self.DOMContent
        
    @property
    def html(self): return self.DOMElement.get_attribute('outerHTML')   
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


class Tree(DOM, scrape='static'):
    @property
    def DOMTree(self):
        if not self: raise EmptyTreeError(str(self))
        else: return self.DOMContent
        
    @property
    def html(self): return tostring(self.DOMTree)     
    @property
    def text(self): return str(self.DOMTree.text_content())   
    @property
    def link(self): return str(self.DOMTree.attrib['href'])


class Captcha(Element): pass


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


class Link(DOM, parser=lambda x: x):
    @classmethod
    def dynamic(cls, **attrs): return type(cls.__name__, (Element,), Link.__dict__, **attrs)
    @classmethod
    def static(cls, **attrs): return type(cls.__name__, (Tree,), Link.__dict__, **attrs)    
    
    @property
    def url(self): return str(self.link) 
    @property
    def data(self): return self.parser(self.link)


class Text(DOM, parser=lambda x: x): 
    @classmethod
    def dynamic(cls, **attrs): return type(cls.__name__, (Element,), Text.__dict__, **attrs)
    @classmethod
    def static(cls, **attrs): return type(cls.__name__, (Tree,), Text.__dict__, **attrs)  
    
    @property
    def data(self): return self.parser(self.text)
    

class Table(DOM, tableindex=0, headerrow=None, indexcolumn=None, parser=lambda x: x):
    @classmethod
    def dynamic(cls, **attrs): return type(cls.__name__, (Element,), Table.__dict__, **attrs)
    @classmethod
    def static(cls, **attrs): return type(cls.__name__, (Tree,), Table.__dict__, **attrs)  
    
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
        
        



    
