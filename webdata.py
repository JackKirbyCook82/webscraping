# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebData Objects
@author: Jack Kirby Cook

"""

import time
from collections import namedtuple as ntuple
from collections import OrderedDict as ODict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from webscraping.webdom import Captcha, Clickable, Input, Selection, Link, Text, Table, EmptyWebDOMError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebClickable', 'WebButton', 'WebRadioButton', 'WebCheckBox', 'WebInput', 'WebSelection', 'WebLink', 'WebText', 'WebTable', 'WebCaptcha', 'WebClickables']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


REGISTRY = {}
CAPTCHA_WAIT = 30
CAPTCHA_TIMEOUT = 15 * 60


#def getelement(driver, timeout, xpath):
#    try: domelement = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
#    except (NoSuchElementException, TimeoutException, WebDriverException): domelement = None        
#    return domelement    
#
#def getelements(driver, timeout, xpath): 
#    try: domelements = WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
#    except (NoSuchElementException, TimeoutException, WebDriverException): domelements = []  
#    return domelements
#
#def gettree(html, xpath):
#    domtrees = html.xpath(xpath)
#    if len(domtrees) == 0: return None
#    elif len(domtrees) == 1: return domtrees[0]
#    else: raise ValueError(len(domtrees))        
#
#def gettrees(html, xpath):
#    domtrees = html.xpath(xpath)
#    if len(domtrees) == 0: return []
#    else: return domtrees[0]


class WebContentError(Exception):
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])

class EmptyWebContentError(WebContentError): pass
class EmptyWebDataError(WebContentError): pass
class EmptyWebCollectionError(WebContentError): pass 
class CaptchaError(WebContentError): pass  
 

class WebLocator(ntuple('Locator', 'filtration attribute')):
    attrchar, filterchar = ".", "/"  
    
    def __init__(self, *args, **kwargs): pass
    def __call__(self, webcontent):
        assert isinstance(webcontent, (WebContent, WebData))
        located = webcontent
        for key in self.filtration: located = located.children[key]
        return getattr(located, self.attribute)        
    
    @classmethod
    def fromstr(cls, string):
        try: filtration, attribute = string.split(cls.attrchar)
        except ValueError: return cls([], string)
        return cls(filtration.split(cls.filterchar), attribute)

    
class WebContent(object):
    def __init__(self, parent, children={}): self.__parent, self.__children = parent, children
    def __call__(self, **kwargs): return {key:self.loc(WebLocator.fromstr(value)) for key, value in kwargs.items()}     
    def __bool__(self): return bool(self.__parent)
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self.__parent)))      
 
    def __getitem__(self, locator): 
        if isinstance(locator, str): return self.__children[locator]
        elif isinstance(locator, WebLocator): return self.loc(locator)
        else: raise TypeError(type(locator).__name__)
        
    def __getattr__(self, attr): 
        try: return getattr(self.__parent, attr)    
        except EmptyWebDOMError: raise EmptyWebContentError(self)    

    @property
    def parent(self): return self.__parent
    @property
    def children(self): return self.__children      

    def loc(self, weblocator):
        if not isinstance(weblocator, WebLocator): raise TypeError(type(weblocator).__name__)
        else: return weblocator(self)   
 
    
class WebAdapter(object):
    def __init_subclass__(cls, **kwargs):
        if 'WebDOM' in kwargs.keys() and 'xpath' not in kwargs.keys() and 'scrape' not in kwargs.keys(): cls.factory(kwargs.pop('WebDOM'))
        elif 'WebDOM' not in kwargs.keys() and 'xpath' not in kwargs.keys() and 'scrape' in kwargs.keys(): cls.variant(kwargs.pop('scrape'))        
        elif 'WebDOM' not in kwargs.keys() and 'xpath' not in kwargs.keys() and 'scrape' not in kwargs.keys(): cls.customize(**kwargs)  
        elif 'WebDOM' not in kwargs.keys() and 'xpath' in kwargs.keys() and 'scrape' not in kwargs.keys(): cls.create(kwargs.pop('xpath'), **kwargs)
        else: raise ValueError(kwargs)
       
    @classmethod
    def factory(cls, WebDOM): 
        assert not hasattr(cls, 'WebDOM') and not hasattr(cls, 'xpath')
        setattr(cls, 'WebDOM', WebDOM)
       
    @classmethod
    def variant(cls, scrape):
        if scrape == 'dynamic': newDOM = cls.WebDOM.dynamic()
        elif scrape == 'static': newDOM = cls.WebDOM.static()
        else: raise ValueError(scrape)
        return type(cls.__name__, (cls,), {'DOM':newDOM})
 
    @classmethod
    def dynamic(cls): return cls.variant('dynamic')
    @classmethod
    def static(cls): return cls.variant('static')       
 
    @classmethod
    def customize(cls, **attrs):
        assert hasattr(cls, 'WebDOM') and not hasattr(cls, 'xpath')
        assert 'scrape' not in attrs.keys()
        newDOM = type(cls.WebDOM.__name__, (cls.WebDOM,), {}, **attrs)
        return type(cls.__name__, (cls,), {'DOM':newDOM})          
       
    @classmethod
    def create(cls, xpath, parent=None, key=None, **kwargs):
        assert hasattr(cls, 'WebDOM') and not hasattr(cls, 'xpath')
        assert 'scrape' not in kwargs.keys()
        setattr(cls, 'xpath', xpath)
        setattr(cls, 'Children', {})
        if parent is not None: REGISTRY[parent.__name__].addchild(key, cls)
        REGISTRY[cls.__name__] = cls        
        
    @classmethod
    def addchild(cls, key, child):
        assert key is not None
        cls.Children[key] = child      
        
    def __init__(self, source, timeout=None): self.__source, self.__timeout = source, timeout
    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'WebDOM') and hasattr(cls, 'xpath')
        assert hasattr(cls.WebDOM, 'scrape')
        assert getattr(cls.WebDOM, 'scrape') is not None
        assert cls.__name__ in REGISTRY.keys() and cls in REGISTRY.values()  
        return super().__new__(cls)       
    
    @property
    def scrape(self): return self.WebDOM.scrape
  
    
class WebData(WebContent, WebAdapter):
    pass

#    def __init__(self, driver, timeout): 
#        self.__driver, self.__timeout = driver, timeout
#        element = self.Element(self.get())
#        if bool(element): children = ODict([(key, child(self.__element.DOMElement, self.timeout)) for key, child in self.Children.items()])
#        else: children = ODict([(key, None) for key, child in self.Children.items()])      
#        super().__init__(element, children)
        
#    def __iter__(self): 
#        webitemtype = type('_'.join([self.__class__.__name__, 'Item']), (WebItem,), {})
#        return (webitem for webitem in [webitemtype(self.element, self.children)]) 
    
#    @property
#    def driver(self): return self.__driver
#    @property
#    def timeout(self): return self.__timeout

#    def get(self):
#        print("WebElement Loading: {}".format(self.__class__.__name__))    
#        domelement = getelement(self.driver, self.timeout, self.xpath)
#        if domelement is None: print("WebElement Missing: {}".format(self.__class__.__name__))         
#        return domelement  


class WebCollection(WebAdapter): 
    pass
        
#    def __init__(self, source, timeout=None):
#        pass

#    @property
#    def scrape(self): return self.DOM.scrape    
    
#    def __init__(self, driver, timeout): 
#        self.__driver, self.__timeout = driver, timeout    
#        elements = [self.Element(domelement) for domelement in self.get()]
#        childrens = [ODict([(key, child(element.DOMElement, self.timeout)) for key, child in self.Children.items()]) for element in elements]
#        webitemtype = type('_'.join([self.__class__.__name__, 'Item']), (WebItem,), {})
#        self.__webitems = [webitemtype(element, children) for element, children in zip(elements, childrens)]      

#    def __bool__(self): return bool(self.__webitems)
#    def __len__(self): return len(self.__webitems)
#    def __str__(self): return "{}|{}".format(self.__class__.__name__, str([str(webitem) for webitem in self.__webitems]))
#    def __getitem__(self, index): return self.__webitems[index]
#    def __iter__(self): return (webitem for webitem in self.__webitems)

#    @property
#    def driver(self): return self.__driver
#    @property
#    def timeout(self): return self.__timeout     
#    @property
#    def items(self): return self.__webitems
    
#    def get(self):
#        print("WebElementList Loading: {}".format(self.__class__.__name__))
#        domelements = getelements(self.driver, self.timeout, self.xpath)
#        if not domelements: print("WebElementList Missing: {}".format(self.__class__.__name__))  
#        return domelements


class WebClickables(WebCollection, WebDOM=Clickable): pass
class WebClickable(WebData, WebDOM=Clickable): pass
class WebButton(WebData, WebDOM=Clickable): pass
class WebRadioButton(WebData, WebDOM=Clickable): pass
class WebCheckBox(WebData, WebDOM=Clickable): pass
class WebInput(WebData, WebDOM=Input): pass
class WebSelection(WebData, WebDOM=Selection): pass
class WebLink(WebData, WebDOM=Link): pass
class WebText(WebData, WebDOM=Text): pass
class WebTable(WebData, WebDOM=Table): pass
class WebCaptcha(WebData, WebDOM=Captcha): 
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
















