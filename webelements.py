# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

import re
import pandas as pd
from abc import ABC, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebClickable', 'WebButton', 'WebRadioButton', 'WebCheckBox', 'WebLink', 'WebInput', 'WebSelection', 'WebData', 'WebTable']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebElementError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])


class WebElementBase(ABC):
    __registry = []
    def __init_subclass__(cls, *args, **kwargs):
        for key, value in kwargs.items(): 
            if not hasattr(value, '__call__'): setattr(cls, key, value)
            else: setattr(cls, key, staticmethod(value))        
        try: 
            setattr(cls, 'xpath', kwargs['xpath'])
            cls.__registry.append(cls)
        except KeyError: pass

    __instance = None
    def __new__(cls, *args, **kwargs):
        assert cls in cls.__registry and hasattr(cls, 'xpath')
        if cls.__instance is None: 
            cls.__instance = super().__new__(cls) 
            cls.__initialized = False
        return cls.__instance  

    def __repr__(self): return "{}(driver={}, timeout={})".format(self.__class__.__name__, repr(self.__driver), self.__timeout)    
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(self.loaded))    
    def __init__(self, driver, timeout, *args, **kwargs): 
        if self.__initialized: return
        self.__driver, self.__timeout, self.__element = driver, timeout, None    
        self.__initialized = True

    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
    @property
    def element(self): 
        if self.loaded: return self.__element
        else: raise EmptyWebElementError(str(self))

    @property
    def loaded(self): return self.__element is not None
    def update(self, element): self.__element = element
    def load(self):
        if self.loaded: return self
        print("WebElement Loading: {}".format(self.__class__.__name__))
        element = self.get()
        if element is None: print("WebElement Missing: {}".format(self.__class__.__name__))    
        else: self.update(element)
        return self
        
    @abstractmethod
    def get(self): pass


class WebElement(WebElementBase):
    @property
    def text(self): return self.element.text 
    @property
    def html(self): return self.element.get_attribute('outerHTML')   
    @property
    def enabled(self): return self.element.is_enabled()
    @property
    def displayed(self): return self.element.is_displayed()      
    
    def get(self): 
        try: element = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located((By.XPATH, self.xpath)))
        except (NoSuchElementException, TimeoutException, WebDriverException): element = None        
        return element


# class WebElements(WebElementBase):
#     def __iter__(self): (item for item in self.elements)
#     def __getitem__(self, index): return self.elements[index]
    
#     @property
#     def elements(self): return self.element
#     @property
#     def text(self): return [item.text for item in self.elements]
#     @property
#     def enabled(self): return all([item.is_enabled() for item in self.elements])
#     @property
#     def displayed(self): return all([item.is_displayed() for item in self.elements])
#     @property
#     def empty(self): return not self.elements

#     def get(self): 
#         try: elements = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_all_elements_located((By.XPATH, self.xpath)))
#         except (NoSuchElementException, TimeoutException, WebDriverException): elements = None        
#         return elements


class WebClickable(WebElement):    
    def click(self): self.element.click()

class WebButton(WebClickable): pass
class WebRadioButton(WebClickable): pass
class WebCheckBox(WebClickable): pass    
class WebInput(WebClickable):
    def clear(self): self.element.clear()
    def fill(self, text): self.element.sendKeys(text)       


class WebText(WebElement, parser=lambda x: str(x)):
    def data(self): 
        try: return self.parser(self.text)
        except EmptyWebElementError: return None
    
    
class WebLink(WebElement):
    @property
    def url(self): return str(self.element.href)
    def click(self): self.element.click()      
    
    
class WebData(WebElement, parser=lambda x: str(x), parsers={}):
    def data(self): 
        if isinstance(self.element, str): 
            try: return [self.parser(x) for x in re.findall(self.element, self.text)]
            except EmptyWebElementError: return None
        elif isinstance(self.element, dict): 
            try: return {key:[self.parsers.get(key, self.parser)(x) for x in re.findall(pattern, self.text)] for key, pattern in self.element.items()}
            except EmptyWebElementError: return {}
        else: raise TypeError(type(self.element).__name__)


class WebTable(WebElement, tableindex=0, headerrow=None, indexcolumn=None): 
    def parser(self, dataframe, *args, **kwargs): return dataframe
    def dataframe(self): 
        tables = pd.read_html(self.html, header=self.headerrow, index_col=self.indexcolumn)
        if not tables: return None
        return tables[self.tableindex].to_frame() if not isinstance(tables[self.tableindex], pd.DataFrame) else tables[self.tableindex]   

    def table(self, *args, **kwargs): 
        dataframe = self.dataframe()
        if dataframe is not None: return self.parser(dataframe, *args, **kwargs)   
        else: return None    


class WebSelection(WebElement, mapping={}):
    def __len__(self): return len(self.select.options())    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__select = None

    @property
    def select(self): 
        if self.loaded: return self.__select
        else: raise EmptyWebElementError(str(self)) 

    def update(self, element): 
        super().update(element)
        self.__select = Select(element) if element is not None else element

    def click(self): self.select.click()      
    def clear(self): self.select.deselect_all()    
    def keys(self): return [item.text for item in self.select.options()]
    def isel(self, index): self.select.select_by_index(index)
    def tsel(self, text): self.select.select_by_visible_text(text)
    def vsel(self, value): self.select.select_by_value(value)
    def sel(self, x):
        if isinstance(x, int): self.isel(x)
        elif isinstance(x, str): 
            try: self.vsel(self.mapping.get(x, x))
            except : self.tsel(self.mapping.get(x, x))
        else: raise TypeError(type(x).__name__)
    
    






            



















