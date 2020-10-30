# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

from collections import OrderedDict as ODict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from webscraping.elements import Clickable, Link, Text, Table, Input, Selection, EmptyElementError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebClickable', 'WebButton', 'WebRadioButton', 'WebCheckBox', 'WebText', 'WebTable', 'WebInput', 'WebSelection', 'WebLink', 'WebClickableList']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


REGISTRY = {}


def getelement(driver, timeout, xpath):
    try: domelement = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): domelement = None        
    return domelement    

def getelements(driver, timeout, xpath): 
    try: domelements = WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): domelements = []  
    return domelements


class EmptyWebElementError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])
    
class EmptyWebItemError(Exception):
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])


class WebElement(object):
    @classmethod
    def customize(cls, **attrs):
        newElement = type(cls.Element.__name__, (cls.Element,), {}, **attrs)
        newWebElement = type(cls.__name__, (cls,), {'Element':newElement})
        return newWebElement
    
    @classmethod
    def addchild(cls, key, child):
        assert key is not None
        cls.Children[key] = child
        
    def __init_subclass__(cls, *args, element=None, xpath=None, parent=None, key=None, **kwargs):
        if element is not None: setattr(cls, 'Element', element)
        if xpath is not None: 
            setattr(cls, 'xpath', xpath)
            setattr(cls, 'Children', {})
            if parent is not None: REGISTRY[parent.__name__].addchild(key, cls)
            REGISTRY[cls.__name__] = cls

    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'xpath') and hasattr(cls, 'Element')
        assert cls.__name__ in REGISTRY.keys() and cls in REGISTRY.values()  
        return super().__new__(cls)                      
    
    def __init__(self, driver, timeout):
        self.__element = self.Element(self.get(driver, timeout))
        self.__children = ODict([(key, child(self.__element, timeout)) for key, child in self.Children.items()])
    
    @property
    def element(self): return self.__element
    @property
    def children(self): return self.__children
    
    def __bool__(self): return bool(self.__element)
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self.__element)))      
    def __getitem__(self, key): return self.__children[key] 
    def __iter__(self): 
        webitemtype = type('_'.join([self.__class__.__name__, 'Item']), (WebItem,), {})
        return (webitem for webitem in [webitemtype(self.element, self.children)]) 
    
    def __getattr__(self, attr): 
        try: return getattr(self.__element, attr)    
        except EmptyElementError: raise EmptyWebElementError(self)
    
    def get(self, driver, timeout):
        print("WebElement Loading: {}".format(self.__class__.__name__))    
        domelement = getelement(driver, timeout, self.xpath)
        if domelement is None: print("WebElement Missing: {}".format(self.__class__.__name__))         
        return domelement  
 
    
class WebItem(object):
    def __init__(self, element, children): self.__element, self.__children = element, children
    def __bool__(self): return bool(self.__element)
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self.__element)))      
    def __getitem__(self, key): return self.__children[key] 
    def __call__(self, *elementAttrs, **childrenAttrs): return {key:value for key, value in self.execute(*elementAttrs, **childrenAttrs)}    
    def __getattr__(self, attr): 
        try: return getattr(self.__element, attr)    
        except EmptyElementError: raise EmptyWebItemError(self)    
    
    def execute(self, *elementAttrs, **childrenAttrs):
        for attr in elementAttrs: yield getattr(self.element, attr)
        for key, attr in childrenAttrs.items(): yield getattr(self.children[key], attr)
        
    
class WebElementList(object): 
    @classmethod
    def customize(cls, **attrs):
        newElement = type(cls.Element.__name__, (cls.Element,), {}, **attrs)
        newWebElement = type(cls.__name__, (cls,), {'Element':newElement})
        return newWebElement
    
    @classmethod
    def addchild(cls, key, child):
        assert key is not None
        cls.Children[key] = child
    
    def __init_subclass__(cls, *args, element=None, xpath=None, parent=None, key=None, **kwargs):
        if element is not None: setattr(cls, 'Element', element)
        if xpath is not None: 
            setattr(cls, 'xpath', xpath)
            setattr(cls, 'Children', {})
            if parent is not None: REGISTRY[parent.__name__].addchild(key, cls)
            REGISTRY[cls.__name__] = cls
    
    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'xpath') and hasattr(cls, 'Element')
        assert cls.__name__ in REGISTRY.keys() and cls in REGISTRY.values()  
        return super().__new__(cls)
        
    def __init__(self, driver, timeout):
        elements = [self.Element(domelement) for domelement in self.get(driver, timeout)]
        childrens = [ODict([(key, child(element.domelement, timeout)) for key, child in self.Children.items()]) for element in elements]
        webitemtype = type('_'.join([self.__class__.__name__, 'Item']), (WebItem,), {})
        self.__webitems = [webitemtype(elements, children) for element, children in zip(elements, childrens)]
        
    def __bool__(self): return bool(self.__items)
    def __len__(self): return len(self.__items)
    def __getitem__(self, index): return self.__items[index]
    def __iter__(self): return (webitem for webitem in self.__webitems)
        
    def get(self, driver, timeout):
        print("WebElements Loading: {}".format(self.__class__.__name__))
        domelements = getelements(driver, timeout, self.xpath)
        if not domelements: print("WebElements Missing: {}".format(self.__class__.__name__))  
        return domelements


class WebClickable(WebElement, element=Clickable): pass
class WebButton(WebElement, element=Clickable): pass
class WebRadioButton(WebElement, element=Clickable): pass
class WebCheckBox(WebElement, element=Clickable): pass
class WebText(WebElement, element=Text): pass
class WebTable(WebElement, element=Table): pass
class WebInput(WebElement, element=Input): pass
class WebSelection(WebElement, element=Selection): pass
class WebLink(WebElement, element=Link): pass

class WebClickableList(WebElementList, element=Clickable): pass




















