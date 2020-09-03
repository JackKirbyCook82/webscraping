# -*- coding: utf-8 -*-
"""
Created on Tues Sept 1 2020
@name:   WebAction Objects
@author: Jack Kirby Cook

"""

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
        self.__webelements = {key:webelement(driver, timeout) for key, webelement in self.WebElements.items()}
    
    @property
    def loaded(self): return all([webaction.loaded for webaction in self.__webactions]) and all([webelement.loaded for webelement in self.__webelements])
    def load(self): 
        print("WebActionChain Loading: {}".format(self.__class__.__name__))
        for webaction in self.__webactions: webaction.load()
        for webelement in self.__webelements: webelement.load()
        return self
    
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
  
    def execute(self, *args, **kwargs): return
    def __call__(self, *args, **kwargs):
        actions = ActionChains(self.driver)
        for webaction in self.__webactions: webaction.subscribe(actions)
        print("WebActionChain Executing: {}".format(self.__class__.__name__))
        actions.preform()
        return self.execute(*args, **kwargs)

    @classmethod
    def create(cls, webactions, *args, webelements={}, **attrs):
        assert isinstance(webactions, (tuple, list)) and isinstance(webelements, dict)
        assert all([issubclass(webaction, WebAction) for webaction in webactions])
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebActions':tuple(webactions), 'WebElements':webelements, **attrs})
        return wrapper


class WebAction(ABC): 
    def __bool__(self): return self.loaded
    def __init__(self, driver, timeout, *args,**kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__webelement = self.WebElement(driver, timeout)       
       
    @property
    def loaded(self): return self.__webelement.loaded
    def load(self): 
        print("WebAction Loading: {}".format(self.__class__.__name__))
        self.__webelement.load()
        return self
        
    def subscribe(self, actions):
        if not self.loaded: raise EmptyWebActionError()
        self.register(actions)
        if self.wait: actions.pause(self.wait)
    
    @abstractmethod
    def register(self, actions): pass
        
    @classmethod
    def create(cls, webelement, wait=None, **attrs): 
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebElement':webelement, 'wait':wait, **attrs})
        return wrapper             


class WebClick(WebAction): 
    def register(self, actions): actions.click(self.__webelement)    
    
class WebDoubleClick(WebAction): 
    def register(self, actions): actions.double_click(self.__webelement)
    
class WebClickDown(WebAction): 
    def register(self, actions): actions.click_and_hold(self.__webelement)

class WebClickRelease(WebAction): 
    def register(self, actions): actions.release(self.__webelement)

class WebMoveTo(WebAction): 
    def register(self, actions): actions.move_to_element(self.__webelement)
 

class WebKeyAction(WebAction):
    @classmethod
    def create(cls, webelement, value, **attrs): return super().create(webelement, value=value, **attrs)

class WebKeyDown(WebKeyAction): 
    def register(self, actions): actions.key_down(self.value, self.__webelement)
    
class WebKeyUp(WebKeyAction): 
    def register(self, actions): actions.key_up(self.value, self.__webelement)


class WebDragDrop(WebAction):   
    def register(self, actions): actions.drag_and_drop(self.__sourcewebelement, self.__destinationwebelement)
    
    def __init__(self, driver, timeout, *args, **kwargs):    
        self.__driver, self.__timeout = driver, timeout
        self.__sourcewebelement = self.SourceWebElement(driver, timeout)    
        self.__destinationwebelement = self.DestinationWebElement(driver, timeout)
        
    @property
    def loaded(self): return self.__sourcewebelement.loaded and self.__destinationwebelement.loaded
    def load(self): 
        self.__sourcewebelement.load()
        self.__destinationwebelement.load()
        return self
      
    @classmethod
    def create(cls, source, destination, wait=None, **attrs):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'SourceWebElement':source, 'DestinationWebElement':destination, 'wait':wait, **attrs})
        return wrapper 


















