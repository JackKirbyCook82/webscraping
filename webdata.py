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

from webscraping.webdom import Captcha, Refusal, BadRequest, Clickable, Input, Selection, Link, Text, Table, EmptyWebDOMError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebClickable', 'WebButton', 'WebRadioButton', 'WebCheckBox', 'WebInput', 'WebSelection', 'WebLink', 'WebText', 'WebTable', 'WebClickableList', 'WebClickableDict', 'WebRefusal', 'WebCaptcha', 'WebBadRequest']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


REGISTRY = {}


def getelements(driver, timeout, xpath): 
    assert timeout is not None
    try: driver_elements = WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): driver_elements = []  
    return driver_elements

def getelement(driver, timeout, xpath):
    assert timeout is not None
    try: driver_element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): driver_element = None        
    return driver_element    

def gettrees(htmltree, xpath): return htmltree.xpath(xpath)
def gettree(htmltree, xpath):
    html_subtrees = htmltree.xpath(xpath)
    if len(html_subtrees) == 0: return None
    elif len(html_subtrees) == 1: return html_subtrees[0]
    else: raise ValueError(len(html_subtrees))        


class EmptyWebDataError(Exception):
    def __str__(self): return "{}|{}".format(self.__class__.__name__, self.args[0])
    

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
        elif 'WebDOM' in kwargs.keys() and 'xpath' not in kwargs.keys() and not 'xpaths' in kwargs.keys(): cls.factory(kwargs.pop('WebDOM'))
        elif 'WebDOM' not in kwargs.keys() and ('xpath' in kwargs.keys() or 'xpaths' in kwargs.keys()): cls.create(xpath=kwargs.pop('xpath', None), xpaths=kwargs.pop('xpaths', []), **kwargs)
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
    def create(cls, xpath=None, xpaths=[], timeout=10, parent=None, key=None, **kwargs):
        assert hasattr(cls, 'WebDOM') and not hasattr(cls, 'xpath') and not hasattr(cls, 'timeout')
        setattr(cls, 'xpath', '|'.join([item for item in (xpath, *xpaths) if item]))
        setattr(cls, 'timeout', timeout)
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
    def __bool__(self): return bool(self.parent)     
    def __init__(self, parent, children={}): self.__parent, self.__children = parent, children 
    def __getitem__(self, locator): 
        if isinstance(locator, str): return self.children[locator]
        elif isinstance(locator, WebLocator): return self.loc(locator)
        else: raise TypeError(type(locator).__name__)
        
    def __getattr__(self, attr): 
        try: return getattr(self.parent, attr)    
        except EmptyWebDOMError: raise EmptyWebDataError(self)    

    def __call__(self, *args, **kwargs):
        if not bool(self): raise EmptyWebDataError(str(self))
        else: return self.execute(*args, **kwargs)

    @property
    def parent(self): return self.__parent
    @property
    def children(self): return self.__children      
   
    def execute(self, *args, **kwargs): pass
    def find(self, pathstring): return self.loc(WebLocator.fromstr(pathstring))
    def findall(self, **pathstrings): return {key:self.loc(WebLocator.fromstr(pathstring)) for key, pathstring in pathstrings.items()}     
    def loc(self, weblocator):
        if not isinstance(weblocator, WebLocator): raise TypeError(type(weblocator).__name__)
        else: return weblocator(self)       
    
  
class WebData(WebContent, WebAdapter): 
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self.parent)))    
    def __iter__(self): 
        WebItem = type('_'.join([self.__class__.__name__, 'Item']), (WebContent,), {})
        return iter([WebItem(self.parent, self.children)])  
    
    def __init__(self, source, root=True):
        if root: print("WebData Loading: {}".format(self.__class__.__name__))  
        parent = self.WebDOM(self.load(source))
        if not bool(parent) and root: print("WebData Missing: {}".format(self.__class__.__name__))  
        if bool(parent): children = ODict([(key, WebDOMChild(parent.DOM, root=False)) for key, WebDOMChild in self.WebDOMChildren.items()])
        else: children = ODict([(key, None) for key, WebDOMchild in self.WebDOMChildren.items()])            
        super().__init__(parent, children)  
          
    def load(self, source):          
        if self.scrape == 'dynamic':  return getelement(source, self.timeout, self.xpath)     
        elif self.scrape == 'static': return gettree(source, self.xpath)
        else: raise ValueError(self.scrape) 


class WebCollection(WebAdapter): 
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(all([bool(parent) for parent, children in self.__collection])))    
    def __iter__(self): 
        WebItem = type('_'.join([self.__class__.__name__, 'Item']), (WebContent,), {})
        return iter([WebItem(parent, children) for parent, children in self.__collection]) 
    
    def __init__(self, source, root=True):
        if root: print("WebCollection Loading: {}".format(self.__class__.__name__))
        parents = [self.WebDOM(dom) for dom in self.load(source)]
        if not bool(parents) and root: print("WebCollection Missing: {}".format(self.__class__.__name__))  
        childrens = [ODict([(key, WebDOMChild(parent.DOM, root=False)) for key, WebDOMChild in self.WebDOMChildren.items()]) for parent in parents]
        self.__collection = [(parent, children) for parent, children in zip(parents, childrens)]                           

    def load(self, source):        
        if self.scrape == 'dynamic': return getelements(source, self.timeout, self.xpath)     
        elif self.scrape == 'static': return gettrees(source, self.xpath)
        else: raise ValueError(self.scrape)         


class WebClickable(WebData, WebDOM=Clickable): pass
class WebButton(WebData, WebDOM=Clickable): pass
class WebRadioButton(WebData, WebDOM=Clickable): pass
class WebCheckBox(WebData, WebDOM=Clickable): pass
class WebInput(WebData, WebDOM=Input): pass
class WebSelection(WebData, WebDOM=Selection): pass
class WebLink(WebData, WebDOM=Link): pass
class WebText(WebData, WebDOM=Text): pass
class WebTable(WebData, WebDOM=Table): pass


class WebClickableList(WebCollection, WebDOM=Clickable): 
    def values(self): return [webitem for webitem in iter(self)]

class WebClickableDict(WebCollection, WebDOM=Clickable):
    def keys(self): return [webitem.data for webitem in iter(self)]    
    def values(self): return [webitem for webitem in iter(self)]
    def items(self): return [(webitem.data, webitem) for webitem in iter(self)]
    def asdict(self): return {webitem.data:webitem for webitem in iter(self)}


class WebBadRequest(WebData, WebDOM=BadRequest): pass
class WebRefusal(WebData, WebDOM=Refusal):
    def __init__(self, htmltree):
        super().__init__(htmltree)
        if bool(self): print("WebRefusal Blocking: {}".format(self.__class__.__name__))

class WebCaptcha(WebData, WebDOM=Captcha): 
    def __init__(self, driver):
        super().__init__(driver)
        if bool(self): print("WebCaptcha Blocking: {}".format(self.__class__.__name__))

    def execute(self, driver, *args, **kwargs): return self.solve(driver)
    def solve(self, driver):
        print("WebCaptcha Clearing: {}".format(self.__class__.__name__))
        wait = WebDriverWait(driver, 60*10, poll_frequency=15)         
        try: success = wait.until(EC.staleness_of(self.DOMElement))
        except TimeoutException: success = False           
        if success: print("WebCaptcha Cleared: {}".format(self.__class__.__name__))
        else: print("WebCaptcha Not Cleared: {}".format(self.__class__.__name__))       
        return success  





    














