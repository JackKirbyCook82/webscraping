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
class WebOperationSubscriptionError(Exception): pass


class WebChain(object):
    def __bool__(self): return self.loaded
    def __getitem__(self, key): return self.__webelements[key]
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__weboperations = tuple([weboperation(driver, timeout) for weboperation in self.WebOperations])
    
    @property
    def loaded(self): return all([webaction.loaded for webaction in self.__webactions]) 
    def load(self): 
        print("WebActionChain Loading: {}".format(self.__class__.__name__))
        for webaction in self.__webactions: webaction.load()
        return self
    
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout

    def __call__(self, *args, **kwargs):
        weboperations = []
        for weboperation in self.__weboperations: 
            try: weboperations[-1] += weboperation
            except (IndexError, WebOperationSubscriptionError): weboperation.append(weboperation)
        print("WebActionChain Executing: {}".format(self.__class__.__name__))
        for actionchain in weboperations: actionchain(*args, **kwargs)

    @classmethod
    def create(cls, weboperations, *args, **attrs):
        assert isinstance(weboperations, (tuple, list))
        assert all([issubclass(weboperation, WebOperation) for weboperation in weboperations])
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebOperations':tuple(weboperations), **attrs})
        return wrapper


class WebOperation(ABC):
    def __bool__(self): return self.loaded    
    def __init__(self, driver, timeout, *args, **kwargs):
        self.__driver, self.__timeout = driver, timeout
        self.__webelements = [item(driver, timeout) for item in self.WebElements] 
      
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs):
        pass
 
    @abstractmethod
    def subscribe(self, weboperation): pass
    def __iadd__(self, weboperation):    
        if not isinstance(weboperation, type(self)): raise WebOperationSubscriptionError('{} += {}'.format(type(weboperation).__name__, type(self).__name__))
        else: self.subscribe(weboperation)
        return self
       
    @property
    def webelements(self): return self.__webelements        
    @property
    def loaded(self): return all([webelement.loaded for webelement in self.webelements])      
    def load(self): 
        print("WebAction Loading: {}".format(self.__class__.__name__))
        for webelement in self.webelements: webelement.load()
        return self
    
    @classmethod
    def create(cls, webelements, wait=None, **attrs):
        assert issubclass(cls, (WebAction, WebProcess))
        webelements = [webelements] if not isinstance(webelements, (tuple, list)) else webelements
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebElements':webelements, 'wait':wait, **attrs})
        return wrapper


class WebAction(WebOperation): 
    def execute(self, *args, **kwargs): pass
    def subscribe(self, weboperation): pass

        
#    @abstractmethod
#    def registerTo(self, actionchain): pass    
#    def subscribeTo(self, actionchain):
#        if not self.loaded: raise EmptyWebActionError()
#        self.registerTo(actionchain)
#        if self.wait: actionchain.pause(self.wait)
    
    
class WebProcess(WebOperation): 
    def execute(self, *args, **kwargs): pass
    def subscribe(self, webprocess): pass

#    @abstractmethod
#    def actions(self, *args, **kwargs): pass
#    def __call__(self, *args, **kwargs): 
#        self.actions(self, *args, **kwargs)  
#        if self.wait: time.sleep(self.__wait)


class WebClick(WebAction): pass
#    def registerTo(self, actionchain): actionchain.click(self.webelements[0].element)    
    
class WebDoubleClick(WebAction): pass
#    def registerTo(self, actionchain): actionchain.double_click(self.webelements[0].element)
    
class WebClickDown(WebAction): pass
#    def registerTo(self, actionchain): actionchain.click_and_hold(self.webelements[0].element)

class WebClickRelease(WebAction): pass 
#    def registerTo(self, actionchain): actionchain.release(self.webelements[0].element)

class WebMoveTo(WebAction): pass
#    def registerTo(self, actionchain): actionchain.move_to_element(self.webelements[0].element)
 
class WebKeyDown(WebAction): pass
#    def registerTo(self, actionchain): actionchain.key_down(self.value, self.webelements[0].element)
    
class WebKeyUp(WebAction): pass
#    def registerTo(self, actionchain): actionchain.key_up(self.value, self.webelements[0].element)

class WebDragDrop(WebAction): pass  
#    def registerTo(self, actionchain): actionchain.drag_and_drop(self.webelements[0].element, self.webelements[1].element)

class WebSelect(WebProcess): pass
#    def actions(self, *args, select, **kwargs): 
#        if isinstance(select, str): self.webelements[0].sel(select) 
#        elif isinstance(select, int): self.webelements[0].isel(select)
#        else: raise TypeError(type(select))












