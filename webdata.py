# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebData Objects
@author: Jack Kirby Cook

"""

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


def getelement(driver, timeout, xpath):
    assert timeout is not None
    try: domelement = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): domelement = None        
    return domelement    

def getelements(driver, timeout, xpath): 
    assert timeout is not None
    try: domelements = WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): domelements = []  
    return domelements

def gettree(html, xpath):
    domtrees = html.xpath(xpath)
    if len(domtrees) == 0: return None
    elif len(domtrees) == 1: return domtrees[0]
    else: raise ValueError(len(domtrees))        

def gettrees(html, xpath):
    domtrees = html.xpath(xpath)
    if len(domtrees) == 0: return []
    else: return domtrees[0]


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
 
    
class WebAdapter(object):
    def __init_subclass__(cls, **kwargs):
        if not kwargs: pass
        elif 'WebDOM' in kwargs.keys() and 'xpath' not in kwargs.keys(): cls.factory(kwargs.pop('WebDOM'))
        elif 'WebDOM' not in kwargs.keys() and 'xpath' in kwargs.keys(): cls.create(kwargs.pop('xpath'), **kwargs)
        else: raise ValueError(kwargs)
       
    @classmethod
    def factory(cls, WebDOM): 
        assert not hasattr(cls, 'xpath')
        setattr(cls, 'WebDOM', WebDOM)

    @classmethod
    def asDynamic(cls): return type(cls.__name__, (cls,), {}, **{'WebDOM':cls.WebDOM.asDynamic()})
    @classmethod
    def asStatic(cls): return type(cls.__name__, (cls,), {}, **{'WebDOM':cls.WebDOM.asStatic()})     
 
    @classmethod
    def customize(cls, **attrs):
        assert hasattr(cls, 'WebDOM') and not hasattr(cls, 'xpath')
        newWebDOM = type(cls.WebDOM.__name__, (cls.WebDOM,), {}, **attrs)
        return type(cls.__name__, (cls,), {}, **{'WebDOM':newWebDOM})          
       
    @classmethod
    def create(cls, xpath, parent=None, key=None, **kwargs):
        assert hasattr(cls, 'WebDOM') and not hasattr(cls, 'xpath')
        setattr(cls, 'xpath', xpath)
        setattr(cls, 'WebDOMChildren', {})
        if parent is not None: REGISTRY[hash(str(parent))].addchild(key, cls)
        assert not hash(str(cls)) in REGISTRY.keys()
        REGISTRY[hash(str(cls))] = cls        
        
    @classmethod
    def addchild(cls, key, child):
        assert key is not None
        cls.WebDOMChildren[key] = child   
        
    @property
    def scrape(self): return self.WebDOM.scrape   
     
    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'WebDOM') and hasattr(cls, 'xpath')
        assert hasattr(cls.WebDOM, 'scrape')
        assert getattr(cls.WebDOM, 'scrape') is not None
        assert hash(str(cls)) in REGISTRY.keys() and cls in REGISTRY.values()  
        return super().__new__(cls)       
    
        
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
    
  
class WebData(WebContent, WebAdapter): 
    def __iter__(self): 
        WebItem = type('_'.join([self.__class__.__name__, 'Item']), (WebContent,), {})
        return iter([WebItem(self.parent, self.children)])  
    
    def __init__(self, source, timeout=None):
        parent = self.WebDOM(self.load(source, timeout))
        if bool(parent): children = ODict([(key, WebDOMChild(parent.DOM, timeout)) for key, WebDOMChild in self.WebDOMChildren.items()])
        else: children = ODict([(key, None) for key, WebDOMchild in self.WebDOMChildren.items()])            
        super().__init__(parent, children)  
          
    def load(self, source, timeout=None):
        print("WebDOM Loading: {}".format(self.__class__.__name__))    
        if self.scrape == 'dynamic':  dom = getelement(source, timeout, self.xpath)     
        elif self.scrape == 'static': dom = gettree(source, self.xpath)
        else: raise ValueError(self.scrape) 
        if dom is None: print("WebDOM Missing: {}".format(self.__class__.__name__))         
        return dom 


class WebCollection(WebAdapter): 
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str([str(webitem) for webitem in self.__webitems]))    
    def __iter__(self): 
        WebItem = type('_'.join([self.__class__.__name__, 'Item']), (WebContent,), {})
        return iter([WebItem(parent, children) for parent, children in self.__collection]) 
    
    def __init__(self, source, timeout=None):
        parents = [self.WebDOM(dom) for dom in self.load(source, timeout)]
        childrens = [ODict([(key, WebDOMChild(parent.DOM, timeout)) for key, WebDOMChild in self.WebDOMChildren.items()]) for parent in parents]
        self.__collection = [(parent, children) for parent, children in zip(parents, childrens)]                           

    def load(self, source, timeout=None):
        print("WebDOMs Loading: {}".format(self.__class__.__name__))
        if self.scrape == 'dynamic':  doms = getelements(source, timeout, self.xpath)     
        elif self.scrape == 'static': doms = gettrees(source, self.xpath)
        else: raise ValueError(self.scrape)         
        if not doms: print("WebDOMs Missing: {}".format(self.__class__.__name__))  
        return doms


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
    def __init__(self, driver, timeout):
        super().__init__(driver, timeout)
        if bool(self): print("WebCaptcha Blocking: {}".format(self.__class__.__name__))
    
    def solve(self, driver):
        print("WebCaptcha Clearing: {}".format(self.__class__.__name__))
        if not self.parent.solve(driver): raise CaptchaError(self)
        else: print("WebCaptcha Cleared: {}".format(self.__class__.__name__))         











