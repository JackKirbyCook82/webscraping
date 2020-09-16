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
__all__ = ['WebButton', 'WebRadioButton', 'WebRadioButton', 'WebLink', 'WebInput', 'WebSelection', 'WebData', 'WebTable']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebElementError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])


class WebElementBase(ABC):
#    def __init_subclass__(cls, *args, xpath, **kwargs):
#        setattr(cls, 'xpath', xpath)

    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None: cls.__instance = super().__new__(cls) 
        return cls.__instance  

    def __repr__(self): return "{}(driver={}, timeout={})".format(self.__class__.__name__, repr(self.__driver), self.__timeout)    
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(self.loaded))    
    def __init__(self, driver, timeout, *args, **kwargs): self.__driver, self.__timeout, self.__content = driver, timeout, None    

    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
    @property
    def content(self): 
        if self.loaded: return self.__content
        else: raise EmptyWebElementError(str(self))

    @property
    def loaded(self): return self.__content is not None
    def update(self, content): self.__content = content
    def load(self):
        if self.loaded: return self
        print("WebElement Loading: {}".format(self.__class__.__name__))
        content = self.get()
        if content is None: print("WebElement Missing: {}".format(self.__class__.__name__))    
        else: self.update(content)
        return self
        
    @abstractmethod
    def get(self): pass


class WebElement(WebElementBase):
    @property
    def text(self): return self.content.text 
    @property
    def html(self): return self.content.get_attribute('outerHTML')   
    @property
    def enabled(self): return self.content.is_enabled()
    @property
    def displayed(self): return self.content.is_displayed()      
    
    def get(self): 
        try: element = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located((By.XPATH, self.xpath)))
        except (NoSuchElementException, TimeoutException, WebDriverException): element = None        
        return element


class WebElements(WebElementBase):
    @property
    def text(self): return [item.text for item in self.content]
    @property
    def enabled(self): return all([item.is_enabled() for item in self.content])
    @property
    def displayed(self): return all([item.is_displayed() for item in self.content])
    @property
    def empty(self): return not self.content     

    def get(self): 
        try: elements = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_all_elements_located((By.XPATH, self.xpath)))
        except (NoSuchElementException, TimeoutException, WebDriverException): elements = None        
        return elements


class WebClickable(WebElement):    
    def click(self): self.element.click()

class WebButton(WebClickable): pass
class WebRadioButton(WebClickable): pass
class WebCheckBox(WebClickable): pass    
class WebInput(WebClickable):
    def clear(self): self.element.clear()
    def fill(self, content): self.element.sendKeys(content)       


class WebText(WebElement):
#    def __init_subclass__(cls, *args, parser=lambda x: str(x), **kwargs):
#        assert hasattr(parser, '__call__')
#        super().__init_subclass__(*args, **kwargs)
#        setattr(cls, 'parser', staticmethod(parser))
    
    def data(self): 
        try: return self.parser(self.text)
        except EmptyWebElementError: return None
    
    
class WebData(WebElement):
#    def __init_subclass__(cls, *args, parser=lambda x: str(x), parsers={}, **kwargs):
#        assert isinstance(parsers, dict) and hasattr(parser, '__call__')
#        assert all([hasattr(item, '__call__') for item in parsers.values()])        
#        super().__init_subclass__(*args, **kwargs)
#        setattr(cls, 'parser', staticmethod(parser))
#        setattr(cls, 'parsers', parsers)
            
    def data(self): 
        if isinstance(self.content, str): 
            try: return [self.parser(x) for x in re.findall(self.content, self.text)]
            except EmptyWebElementError: return None
        elif isinstance(self.content, dict): 
            try: return {key:[self.parsers.get(key, self.parser)(x) for x in re.findall(pattern, self.text)] for key, pattern in self.content.items()}
            except EmptyWebElementError: return {}
        else: raise TypeError(type(self.content))


class WebTable(WebElement): 
#    def __init_subclass__(cls, *args, headerrow=None, indexcolumn=None, **kwargs):
#        super().__init_subclass__(*args, **kwargs)
#        setattr(cls, 'headerrow', headerrow)
#        setattr(cls, 'indexcolumn', indexcolumn)        
    
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


class WebSelection(WebElement):
#    def __init_subclass__(cls, *args, mapping={}, **kwargs):
#        assert isinstance(mapping, dict)
#        super().__init_subclass__(*args, **kwargs)
#        setattr(cls, 'mapping', {key.replace(' ', ''):value for key, value in mapping.items()})
    
    def __len__(self): return len(self.select.options())    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__select = None

    @property
    def select(self): 
        if self.loaded: return self.__select
        else: raise EmptyWebElementError(str(self)) 

    def update(self, content): 
        super().update(content)
        self.__select = Select(content) if content is not None else content

    def click(self): self.select.click()      
    def clear(self): self.select.deselect_all()    
    def keys(self): return [item.text for item in self.select.options()]
    def isel(self, index): self.select.select_by_index(index)
    def tsel(self, text): self.select.select_by_visible_text(text)
    def vsel(self, value): self.select.select_by_value(value)
    def sel(self, x):
        x = x.replace(' ', '')
        if isinstance(x, int): self.isel(x)
        elif isinstance(x, str): 
            try: self.vsel(self.mapping.get(x, x))
            except NoSuchElementException: self.tsel(x)
        else: raise TypeError(type(x).__name__)
    
    
class WebLink(WebElement):
    @property
    def url(self): return str(self.element.href)
    def click(self): self.element.click()  


class WebLinks(WebElements):
    @property
    def urls(self): return [str(self.item.href) for item in self.content]
    def click(self, index): self.content[index].click()






            



















