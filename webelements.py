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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebButton', 'WebRadioButton', 'WebRadioButton', 'WebLink', 'WebInput', 'WebSelection', 'WebData', 'WebTable']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebElementError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])


class WebElement(object): 
    def __getattr__(self, attr): return self.element.get_attribute(attr)
    def __getitem__(self, key): return self.element.get_attribute(key) 
    def __repr__(self): return "{}(driver={}, timeout={})".format(self.__class__.__name__, repr(self.__driver), self.__timeout)     
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(self.loaded))    
    def __init__(self, driver, timeout, *args, **kwargs): self.__driver, self.__timeout, self.__element = driver, timeout, None    

    __instance = None
    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'xpath')
        if cls.__instance is not None: pass 
        else: cls.__instance = super().__new__(cls)
        return cls.__instance        
    
    def get(self):
        try: element = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located((By.XPATH, self.xpath)))
        except (NoSuchElementException, TimeoutException, WebDriverException): element = None        
        self.update(element)
        
    def load(self):
        if self.loaded: return self
        print("WebElement Loading: {}".format(self.__class__.__name__))
        self.get()            
        return self

    def update(self, element): 
        self.__element = element 
        if element is None: print("WebElement Missing: {}".format(self.__class__.__name__))         
       
    @property
    def text(self): return self.element.text 
    @property
    def html(self): return self.element.get_attribute('outerHTML')   
    @property
    def enabled(self): return self.element.is_enabled()
    @property
    def displayed(self): return self.element.is_displayed()   
    @property
    def loaded(self): return self.__element is not None 
    
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
    @property
    def element(self): 
        if self.loaded: return self.__element
        else: raise EmptyWebElementError(str(self)) 
    
    @classmethod
    def create(cls, xpath, **attrs):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'xpath':xpath, **attrs})
        return wrapper 
  
    
#class WebElements(list): pass    
    
    
class WebClickable(WebElement):    
    def click(self): self.element.click()

class WebButton(WebClickable): pass
class WebRadioButton(WebClickable): pass
class WebCheckBox(WebClickable): pass

    
class WebInput(WebElement):
    def click(self): self.element.click()
    def clear(self): self.element.clear()
    def fill(self, content): self.element.sendKeys(content)       


class WebText(WebElement):
    def data(self): 
        try: return self.parser(self.text)
        except EmptyWebElementError: return None
    
    @classmethod
    def create(cls, xpath, parser=lambda x: str(x), **attrs):
        assert hasattr(parser, '__call__')
        def wrapper(self, x): return parser(x)
        return super().create(xpath, parser=wrapper, **attrs)


class WebSelection(WebElement):
    def __len__(self): return len(self.element.options())    
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
            try: self.vsel({key.replace(' ', ''):value for key, value in self.mapping.items()}[x.replace(' ', '')])
            except AttributeError: 
                try: self.vsel(x)
                except NoSuchElementException: self.tsel(x)
        else: raise TypeError(type(x).__name__)
    
    
class WebData(WebElement):
    def data(self): 
        if isinstance(self.content, str): 
            try: return [self.parser(x) for x in re.findall(self.content, self.text)]
            except EmptyWebElementError: return None
        elif isinstance(self.content, dict): 
            try: return {key:[self.parsers.get(key, self.parser)(x) for x in re.findall(pattern, self.text)] for key, pattern in self.content.items()}
            except EmptyWebElementError: return {}
        else: raise TypeError(type(self.content))

    @classmethod
    def create(cls, xpath, content, parser=lambda x: str(x), parsers={}, **attrs):
        assert isinstance(parsers, dict) and hasattr(parser, '__call__')
        assert all([hasattr(item, '__call__') for item in parsers.values()])
        def wrapper(self, x): return parser(x)
        return super().create(xpath, content=content, parser=wrapper, parsers=parsers, **attrs)       


class WebTable(WebElement): 
    def parser(self, dataframe, *args, **kwargs): return dataframe
    def dataframe(self): 
        try: 
            table = pd.read_html(self.html, header=self.headerrow, index_col=self.indexcolumn)[0]
            return table.to_frame() if not isinstance(table, pd.DataFrame) else table    
        except IndexError: return None

    def table(self, *args, **kwargs): 
        dataframe = self.dataframe()
        if dataframe is not None: return self.parser(dataframe, *args, **kwargs)   
        else: return None    

    @classmethod
    def create(cls, xpath, headerrow=None, indexcolumn=None, **attrs):
        return super().create(xpath,  headerrow=headerrow, indexcolumn=indexcolumn, **attrs)    
    
    
class WebLink(WebElement):
    @property
    def url(self): return str(self.element.href)
    def click(self): self.element.click()  









            



















