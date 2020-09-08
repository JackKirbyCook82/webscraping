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


class FunctionChain(list):
    def append(self, function):
        assert hasattr(function, '__call__')
        super().append(function)
   
    def __add__(self, other):
        assert isinstance(other, type(self))
        super().__add__(other)
    
    def __call__(self, *args, **kwargs):
        for function in self: function(*args, **kwargs)


class WebChain(object):
    def __bool__(self): return self.loaded
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__driver, self.__timeout = driver, timeout
        self.__chains = [chain(driver, timeout, *args, **kwargs) for chain in self.Chains]
    
    @property
    def loaded(self): return all([chain.loaded for chain in self.__chains]) 
    def load(self): 
        print("WebActionChain Loading: {}".format(self.__class__.__name__))
        for chain in self.__chains: chain.load()
        return self
    
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout

    def __call__(self, *args, **kwargs):
        pass     

    @classmethod
    def create(cls, webactions, *args, **attrs):
        assert isinstance(webactions, list)
        assert all([issubclass(webaction, WebAction) for webaction in webactions])
        chains = []
        for webaction in webactions:
            try: chains[-1].chain(webaction)
            except (IndexError, InconsistentWebActionError): chains.append(webaction)
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'Chains':chains, **attrs})
        return wrapper


class WebAction(ABC):
    def __bool__(self): return True       
    def __init__(self, driver, timeout, *args, **kwargs):
        self.__driver, self.__timeout = driver, timeout
        self.__webelements = [item(driver, timeout) for item in self.WebElements] 
        self.__next = self.Next(driver, timeout, *args, **kwargs) if self.Next is not None else None
      
    @property
    def webelements(self): return self.__webelements        
    @property
    def loaded(self): return all([webelement.loaded for webelement in self.webelements]) and (self.__next.loaded if self.__next else True)      
    def load(self): 
        print("WebAction Loading: {}".format(self.__class__.__name__))
        for webelement in self.webelements: webelement.load()
        if self.__next: self.__next.load()
        return self

    def __call__(self, *args, **kwargs): 
        if not self.loaded: raise EmptyWebActionError()
        actionchain = self.execute(*args, **kwargs)
        actionchain(*args, **kwargs)

    @abstractmethod
    def extend(self, x): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass

    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
    
    @classmethod
    def chain(cls, webaction): 
        assert issubclass(webaction, (WebProcess, WebOperation))
        if cls.__bases__ != webaction.__bases__: raise InconsistentWebActionError()
        if not cls.Next: cls.Next = webaction
        else: cls.Next.chain(webaction)
    
    @classmethod
    def create(cls, webelements, wait=None, **attrs):
        assert issubclass(cls, (WebProcess, WebOperation)) 
        webelements = [webelements] if not isinstance(webelements, (tuple, list)) else webelements
        attrs = {'WebElements':webelements, 'Next':None, 'wait':wait, **attrs}     
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), attrs)
        return wrapper


class WebProcess(WebAction): 
    @abstractmethod
    def build(self, x): pass
    
    def execute(self, *args, **kwargs):
        x = ActionChains(self.driver)
        self.extend(x)
        return lambda *xargs, **xkwargs: x.perform()

    def extend(self, x): 
        self.build(x)
        if self.wait: x.pause(self.wait)
        if self.__webaction: self.__webaction.extend(x)     
    
    
class WebOperation(WebAction): 
    @abstractmethod
    def function(self, *args, **kwargs): pass    
    
    def execute(self, *args, **kwargs):
        x = FunctionChain()
        self.extend(x)
        return x
        
    def extend(self, x):
        x.append(self.function)
        if self.wait: x.append(lambda *args, **kwargs: time.sleep(self.wait))
        if self.__webaction: self.__webaction.extend(x) 
        

class WebClick(WebProcess): 
    def build(self, x): x.click(self.webelements[0].element)    
    
class WebDoubleClick(WebProcess): 
    def build(self, x): x.double_click(self.webelements[0].element)

class WebClickDown(WebProcess): 
    def build(self, x): x.click_and_hold(self.webelements[0].element)

class WebClickRelease(WebProcess):   
    def build(self, x): x.release(self.webelements[0].element)

class WebMoveTo(WebProcess): 
    def build(self, x): x.move_to_element(self.webelements[0].element)
 
class WebKeyDown(WebProcess): 
    def build(self, x): x.key_down(self.value, self.webelements[0].element)
    
class WebKeyUp(WebProcess): 
    def build(self, x): x.key_up(self.value, self.webelements[0].element)

class WebDragDrop(WebProcess): 
    def build(self, x): x.drag_and_drop(self.webelements[0].element, self.webelements[1].element)

class WebSelect(WebOperation): 
    def function(self, *args, select, **kwargs):
        if isinstance(select, int): self.webelements[0].isel(select)
        elif isinstance(select, str): self.webelements[0].sel(select)
        else: raise TypeError(select)













