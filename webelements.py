# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

import re
import pandas as pd
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebButton', 'WebRadioButton', 'WebRadioButton', 'WebLink', 'WebInput', 'WebSelect', 'WebElementDict', 'WebElementList', 'WebData', 'WebTable']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebElementError(Exception): pass


class WebElement(object): 
    def __bool__(self): return self.__element is not None
    def __getattr__(self, attr): return self.element.get_attribute(attr)
    def __getitem__(self, key): return self.element.get_attribute(key)  
    def __init__(self, driver, timeout): self.__driver, self.__timeout, self.__element = driver, timeout, None    
    def __new__(cls, driver, timeout):
        assert hasattr(cls, 'xpath') and isinstance(driver, Chrome)
        return super().__new__(cls)
       
    def load(self): 
        print("WebElement Loading: {}".format(self.__class__.__name__))
        try: element = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located((By.XPATH, self.xpath)))
        except NoSuchElementException: element = None
        self.update(element)
        return self
        
    def update(self, element): 
        self.__element = element 
        if element is not None: print("WebElement Loaded: {}".format(self.__class__.__name__))
        else: print("WebElement Missing: {}".format(self.__class__.__name__))         
        
    @property
    def text(self): return self.element.text 
    @property
    def html(self): return self.element.get_attribute('outerHTML')   
    @property
    def enabled(self): return self.element.is_enabled()
    @property
    def displayed(self): return self.element.is_displayed()   
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
    @property
    def element(self): 
        if self.__element is not None: return self.__element
        else: raise EmptyWebElementError() 
        
    @classmethod
    def create(cls, xpath, **attrs):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'xpath':xpath, **attrs})
        return wrapper 
  

class WebElementDict(dict):
    keyformat = lambda key: str(key.lower().replace(' ', ''))
    def __getitem__(self, key): return super().__getitem__(self.keyformat(key))
    def __init__(self, driver, timeout): self.__driver, self.__timeout = driver, timeout 

    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout

    def update(self, webelements): super().__init__(webelements)
    def load(self, timeout):
        print("WebElements Loading: {}".format(self.__class__.__name__))
        keys = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_all_elements_located((By.XPATH, self.keyXPath)))
        elements = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_all_elements_located((By.XPATH, self.valueXPath)))
        elements = {self.keyfunction(key):element for key, element in zip(keys, elements)} 
        webelements = {key:WebElement(self.driver) for key in elements.keys()}
        for element, webelement in zip(elements.values(), webelements.values()): webelement.update(element)
        self.update(webelements)
        return self
        
    @classmethod
    def create(cls, keys, values, webelement, **attrs):
        assert issubclass(webelement, WebElement)
        for name, attr in attrs.items(): setattr(webelement, name, attr)
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'keyXPath':keys, 'valueXPath':values, 'WebElement':webelement})
        return wrapper 


class WebElementList(list):
    indexformat = lambda index: int(index)
    def __getitem__(self, index): return super().__getitem__(self.indexformat(index))
    def __init__(self, driver, timeout): self.__driver, self.__timeout = driver, timeout   

    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout

    def update(self, webelements): super().__init__(webelements)
    def load(self, timeout):
        print("WebElements Loading: {}".format(self.__class__.__name__))
        elements = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_all_elements_located((By.XPATH, self.itemXPath)))
        webelements = [WebElement(self.driver) for i in range(len(elements))]
        for element, webelement in zip(elements, webelements): webelement.update(element)
        self.update(webelements)
        return self

    @classmethod
    def create(cls, items, webelement, **attrs):
        assert issubclass(webelement, WebElement)
        for name, attr in attrs.items(): setattr(webelement, name, attr)
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'itemXPath':items, 'WebElement':webelement})
        return wrapper 


class WebSelect(WebElement):
    def __len__(self): return len(self.element.options())    
    def keys(self): return [element.text for element in self.element.options()]
    def clear(self): self.element.deselect_all()
    def isel(self, index): self.element.select_by_index(index)
    def sel(self, value): self.element.select_by_visible_text(value)
    def load(self): 
        print("WebElement Loading: {}".format(self.__class__.__name__))
        try: element = WebDriverWait(self.driver, self.timeout).until(EC.presence_of_element_located((By.XPATH, self.xpath)))
        except NoSuchElementException: pass
        self.update(Select(element) if element is not None else None)
        return self
    
    
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


class WebText(WebElement):
    def data(self): 
        try: return self.parser(self.text)
        except EmptyWebElementError: return None
    
    @classmethod
    def create(cls, xpath, parser=lambda x: str(x), **attrs):
        assert hasattr(parser, '__call__')
        def wrapper(self, x): return parser(x)
        return super().create(xpath, parser=wrapper, **attrs)


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





















