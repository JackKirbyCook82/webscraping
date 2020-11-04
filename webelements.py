# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

import time
from collections import OrderedDict as ODict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from webscraping.elements import Clickable, Link, Text, ID, Table, Input, Selection, Captcha, EmptyElementError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebClickable', 'WebButton', 'WebRadioButton', 'WebCheckBox', 'WebText', 'WebID', 'WebTable', 'WebInput', 'WebSelection', 'WebLink', 'WebCaptcha', 'WebClickableList']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


REGISTRY = {}
CAPTCHA_WAIT = 30
CAPTCHA_TIMEOUT = 15 * 60


def getelement(driver, timeout, xpath):
    try: domelement = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): domelement = None        
    return domelement    

def getelements(driver, timeout, xpath): 
    try: domelements = WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): domelements = []  
    return domelements


class WebElementError(Exception):
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])

class EmptyWebElementError(WebElementError): pass
class EmptyWebItemError(WebElementError): pass 
class CaptchaError(WebElementError): pass  

    
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
        self.__driver, self.__timeout = driver, timeout
        self.__element = self.Element(self.get())
        if self: self.__children = ODict([(key, child(self.__element.DOMElement, self.timeout)) for key, child in self.Children.items()])
        else: self.__children = ODict([(key, None) for key, child in self.Children.items()])         

    def __call__(self, *elementAttrs, **childrenAttrs): return {key:value for key, value in self.execute(*elementAttrs, **childrenAttrs)}    
    def __bool__(self): return bool(self.__element)
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self.__element)))      
    def __getitem__(self, key): return self.__children[key] 
    def __getattr__(self, attr): 
        try: return getattr(self.__element, attr)    
        except EmptyElementError: raise EmptyWebElementError(self)    
    
    def __iter__(self): 
        webitemtype = type('_'.join([self.__class__.__name__, 'Item']), (WebItem,), {})
        return (webitem for webitem in [webitemtype(self.__element, self.__children)]) 
    
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
    @property
    def element(self): return self.__element
    @property
    def children(self): return self.__children    

    def get(self):
        print("WebElement Loading: {}".format(self.__class__.__name__))    
        domelement = getelement(self.driver, self.timeout, self.xpath)
        if domelement is None: print("WebElement Missing: {}".format(self.__class__.__name__))         
        return domelement  

    def execute(self, *elementAttrs, **childrenAttrs):
        for attr in elementAttrs: yield getattr(self.element, attr)
        for key, attr in childrenAttrs.items(): yield getattr(self.children[key], attr)   
 
    
class WebItem(object):
    def __init__(self, element, children): self.__element, self.__children = element, children
    def __call__(self, *elementAttrs, **childrenAttrs): return {key:value for key, value in self.execute(*elementAttrs, **childrenAttrs)}        
    def __bool__(self): return bool(self.__element)
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self.__element)))      
    def __getitem__(self, key): return self.__children[key] 
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
        self.__driver, self.__timeout = driver, timeout    
        elements = [self.Element(domelement) for domelement in self.get()]
        childrens = [ODict([(key, child(element.DOMElement, self.timeout)) for key, child in self.Children.items()]) for element in elements]
        webitemtype = type('_'.join([self.__class__.__name__, 'Item']), (WebItem,), {})
        self.__webitems = [webitemtype(element, children) for element, children in zip(elements, childrens)]      
    
    def __bool__(self): return bool(self.__webitems)
    def __len__(self): return len(self.__webitems)
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str([str(webitem) for webitem in self.__webitems]))
    def __getitem__(self, index): return self.__webitems[index]
    def __iter__(self): return (webitem for webitem in self.__webitems)
    
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout        
    @property
    def items(self): return self.__webitems
    
    def get(self):
        print("WebElementList Loading: {}".format(self.__class__.__name__))
        domelements = getelements(self.driver, self.timeout, self.xpath)
        if not domelements: print("WebElementList Missing: {}".format(self.__class__.__name__))  
        return domelements


class WebClickableList(WebElementList, element=Clickable): pass

class WebClickable(WebElement, element=Clickable): pass
class WebButton(WebElement, element=Clickable): pass
class WebRadioButton(WebElement, element=Clickable): pass
class WebCheckBox(WebElement, element=Clickable): pass
class WebText(WebElement, element=Text): pass
class WebID(WebElement, element=ID): pass
class WebTable(WebElement, element=Table): pass
class WebInput(WebElement, element=Input): pass
class WebSelection(WebElement, element=Selection): pass
class WebLink(WebElement, element=Link): pass
class WebCaptcha(WebElement, element=Captcha): 
    def clear(self):
        print("WebCaptcha Blocking: {}".format(self.__class__.__name__))
        timeout = lambda dt: int(dt) > CAPTCHA_TIMEOUT
        currenttime = lambda: time.time()
        captcha, starttime = bool(self), currenttime()
        while captcha and not timeout(currenttime() - starttime):
            captcha = not WebDriverWait(self.driver, self.timeout).until(EC.staleness_of((By.XPATH, self.xpath)))
            time.sleep(CAPTCHA_WAIT)
        if captcha: raise CaptchaError(self)
        else: print("WebCaptcha Cleared: {}".format(self.__class__.__name__))






















