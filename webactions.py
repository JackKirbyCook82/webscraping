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
__all__ = ['WebActionChain', 'WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebDragDrop', 'WebMoveTo', 'WebKeyDown', 'WebKeyUp']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebActionError(Exception): pass


class WebActionChain(object):
    def __bool__(self): return self.loaded
    def __getitem__(self, key): return self.__webelements[key]
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__webactions = tuple([webaction(driver, timeout) for webaction in self.WebActions])
    
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
        actionchains = []
        for webaction in self.__webactions:
            if issubclass(webaction, WebCustomAction): actionchains.append(webaction)
            elif issubclass(webaction, WebAction):  
                try: webaction.subscribeTo(actionchains[-1])
                except (IndexError, AttributeError): actionchains.append(webaction.subscribeTo(ActionChains(self.driver)))
            else: raise TypeError(type(webaction))
        print("WebActionChain Executing: {}".format(self.__class__.__name__))
        for actionchain in actionchains: 
            try: actionchain.perform()
            except AttributeError: actionchain(*args, **kwargs)

    @classmethod
    def create(cls, webactions, *args, **attrs):
        assert isinstance(webactions, (tuple, list))
        assert all([issubclass(webaction, WebActionBase) for webaction in webactions])
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebActions':tuple(webactions), **attrs})
        return wrapper


class WebActionBase(ABC):
    def __bool__(self): return self.loaded    
    def __init__(self, driver, timeout, *args, webelements, **kwargs):
        assert isinstance(webelements, dict)
        self.__driver, self.__timeout = driver, timeout
        self.__webelements = [item(driver, timeout) for item in self.WebElements] 
        
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
        webelements = [webelements] if not isinstance(webelements, (tuple, list)) else webelements
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebElements':webelements, 'wait':wait, **attrs})


class WebAction(WebActionBase):
    @abstractmethod
    def registerTo(self, actionchain): pass    
    def subscribeTo(self, actionchain):
        if not self.loaded: raise EmptyWebActionError()
        self.registerTo(actionchain)
        if self.wait: actionchain.pause(self.wait)
    
    
class WebCustomAction(WebActionBase): 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): 
        self.execute(self, *args, **kwargs)  
        if self.wait: time.sleep(self.__wait)


class WebClick(WebAction): 
    def registerTo(self, actionchain): actionchain.click(self.webelements[0].element)    
    
class WebDoubleClick(WebAction): 
    def registerTo(self, actionchain): actionchain.double_click(self.webelements[0].element)
    
class WebClickDown(WebAction): 
    def registerTo(self, actionchain): actionchain.click_and_hold(self.webelements[0].element)

class WebClickRelease(WebAction): 
    def registerTo(self, actionchain): actionchain.release(self.webelements[0].element)

class WebMoveTo(WebAction): 
    def registerTo(self, actionchain): actionchain.move_to_element(self.webelements[0].element)
 
class WebKeyDown(WebAction): 
    def registerTo(self, actionchain): actionchain.key_down(self.value, self.webelements[0].element)
    
class WebKeyUp(WebAction): 
    def registerTo(self, actionchain): actionchain.key_up(self.value, self.webelements[0].element)

class WebDragDrop(WebAction):   
    def registerTo(self, actionchain): actionchain.drag_and_drop(self.webelements[0].element, self.webelements[1].element)

class WebSelect(WebCustomAction):
    def execute(self, *args, select, **kwargs): 
        if isinstance(select, str): self.webelements[0].sel(select) 
        elif isinstance(select, int): self.webelements[0].isel(select)
        else: raise TypeError(type(select))












