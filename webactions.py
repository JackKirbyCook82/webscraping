# -*- coding: utf-8 -*-
"""
Created on Tues Sept 1 2020
@name:   WebAction Objects
@author: Jack Kirby Cook

"""

import time
from abc import ABC, abstractmethod
from selenium.webdriver.common.action_chains import ActionChains

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebChain', 'WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebDragDrop', 'WebMoveTo', 'WebKeyDown', 'WebKeyUp']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebActionError(Exception): pass
class InconsistentWebActionError(Exception): pass


class WebChain(object):
    def __bool__(self): return self.loaded
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__links = [link(driver, timeout, *args, **kwargs) for link in self.Links]
    
    @property
    def loaded(self): return all([link.loaded for link in self.links]) 
    def load(self): 
        print("WebActionChain Loading: {}".format(self.__class__.__name__))
        for link in self.links: link.load()
        return self

    @property
    def links(self): return self.__links    
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout

#    def __call__(self, *args, **kwargs):
#        for link in self.links: link(*args, **kwargs)     

#    @classmethod
#    def create(cls, webactions, *args, **attrs):
#        assert isinstance(webactions, list)
#        assert all([issubclass(webaction, WebAction) for webaction in webactions])
#        links = []
#        for webaction in webactions:
#            try: links[-1].link(webaction)
#            except (IndexError, InconsistentWebActionError): links.append(webaction)
#        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'Links':links, **attrs})
#        return wrapper


class WebAction(ABC):
    def __init__(self, driver, timeout, *args, **kwargs):
        self.__driver, self.__timeout = driver, timeout
        self.__webelements = [item(driver, timeout) for item in self.WebElements] 
          
    @property
    def loaded(self): return all([webelement.loaded for webelement in self.webelements])  
    def load(self): 
        for webelement in self.webelements: 
            webelement.load()
            if not webelement.loaded: raise EmptyWebActionError()
        return self

    def __call__(self, *args, **kwargs): 
        if not self.loaded: raise EmptyWebActionError()
        actionchain = self.execute(*args, **kwargs)
        actionchain(*args, **kwargs)

    @property
    def webelements(self): return self.__webelements  
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
   
    @classmethod
    def create(cls, webelements, wait=None, **attrs):
        webelements = [webelements] if not isinstance(webelements, (tuple, list)) else webelements
        attrs = {'WebElements':webelements, 'wait':wait, **attrs}     
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), attrs)
        return wrapper


class WebProcess(WebAction): 
    @abstractmethod
    def extend(self, x): pass


class WebOperation(WebAction):
    @abstractmethod
    def execute(self, *args, **kwargs): pass
        

class WebClick(WebProcess): 
    def extend(self, x): x.click(self.webelements[0].element)    
    
class WebDoubleClick(WebProcess): 
    def extend(self, x): x.double_click(self.webelements[0].element)

class WebClickDown(WebProcess): 
    def extend(self, x): x.click_and_hold(self.webelements[0].element)

class WebClickRelease(WebProcess):   
    def extend(self, x): x.release(self.webelements[0].element)

class WebMoveTo(WebProcess): 
    def extend(self, x): x.move_to_element(self.webelements[0].element)
 
class WebKeyDown(WebProcess): 
    def extend(self, x): x.key_down(self.value, self.webelements[0].element)
    
class WebKeyUp(WebProcess): 
    def extend(self, x): x.key_up(self.value, self.webelements[0].element)

class WebDragDrop(WebProcess): 
    def extend(self, x): x.drag_and_drop(self.webelements[0].element, self.webelements[1].element)

class WebSelect(WebOperation): 
    def execute(self, *args, select, **kwargs):
        if isinstance(select, int): self.webelements[0].isel(select)
        elif isinstance(select, str): self.webelements[0].sel(select)
        else: raise TypeError(select)













