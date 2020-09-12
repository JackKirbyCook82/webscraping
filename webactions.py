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


class EmptyWebActionError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])

class WebActionFailure(Exception):
    def __str__(self): return "\n{}".format(self.args[0])


class WebChain(object):
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

    def __call__(self, *args, **kwargs):
        for link in self.__links: 
            if not link.loaded: raise EmptyWebActionError(str(link))
        for segment in self.build():
            try: segment.perform()
            except AttributeError: segment(*args, **kwargs)

    def build(self):
        try: chain = [self.links[0].subscribe(ActionChains(self.driver))]
        except AttributeError: chain = [self.links[0]]
        for link in self.links[1:]:
            if isinstance(chain[-1], ActionChains) and isinstance(link, WebProcess): chain[-1] = link.subscribe(chain[-1])
            elif isinstance(chain[-1], ActionChains) and isinstance(link, WebOperation): chain.append(link)
            elif isinstance(chain[-1], WebOperation) and isinstance(link, WebProcess): chain.append(link.subscribe(ActionChains(self.driver)))
            elif isinstance(chain[-1], WebOperation) and isinstance(link, WebOperation): chain.append(link)
            else: raise TypeError(type(chain[-1]).__name__, type(link).__name__)
        return chain

    @classmethod
    def create(cls, webactions, *args, **attrs):
        assert isinstance(webactions, list)
        assert all([issubclass(webaction, WebAction) for webaction in webactions])
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'Links':webactions, **attrs})
        return wrapper


class WebAction(ABC):
    def __init__(self, driver, timeout, *args, **kwargs):
        self.__driver, self.__timeout = driver, timeout
        self.__webelements = [item(driver, timeout) for item in self.WebElements] 

    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
    def __str__(self): return "\n".join([self.__class__.__name__]+[str(webelement) for webelement in self.webelements])
         
    @property
    def loaded(self): return all([webelement.loaded for webelement in self.webelements])  
    def load(self): 
        for webelement in self.webelements: webelement.load()
        return self

    @abstractmethod
    def execute(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): 
        if not self.loaded: raise EmptyWebActionError(str(self))
        self.execute(*args, **kwargs)   

    @property
    def webelements(self): return self.__webelements  
    @property
    def driver(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
   
    @classmethod
    def create(cls, *webelements, wait=None, **attrs):
        assert len(webelements) >= 1
        attrs = {'WebElements':list(webelements), 'wait':wait, **attrs}     
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), attrs)
        return wrapper


class WebProcess(WebAction): 
    @abstractmethod
    def process(self, x): pass
    def subscribe(self, x): 
        if not self.loaded: raise EmptyWebActionError(str(self))
        try: self.process(x)
        except AttributeError: raise WebActionFailure(str(self))
        if self.wait: x.pause(self.wait)
        return x

    def execute(self, *args, **kwargs):
        x = ActionChains(self.driver)
        try: self.process(x)
        except AttributeError: raise WebActionFailure(str(self))
        x.perform()


class WebOperation(WebAction):
    @abstractmethod
    def operation(self, *args, **kwargs): pass

    def execute(self, *args, **kwargs): 
        self.operation(*args, **kwargs)
        if self.wait: time.sleep(self.wait)

    
class WebClick(WebProcess): 
    def process(self, x): x.click(self.webelements[0].element)    
    
class WebDoubleClick(WebProcess): 
    def process(self, x): x.double_click(self.webelements[0].element)

class WebClickDown(WebProcess): 
    def process(self, x): x.click_and_hold(self.webelements[0].element)

class WebClickRelease(WebProcess):   
    def process(self, x): x.release(self.webelements[0].element)

class WebMoveTo(WebProcess): 
    def process(self, x): x.move_to_element(self.webelements[0].element)
 
class WebKeyDown(WebProcess): 
    def process(self, x): x.key_down(self.value, self.webelements[0].element)
    
class WebKeyUp(WebProcess): 
    def process(self, x): x.key_up(self.value, self.webelements[0].element)

class WebDragDrop(WebProcess): 
    def process(self, x): x.drag_and_drop(self.webelements[0].element, self.webelements[1].element)

class WebSelect(WebOperation): 
    def operation(self, *args, select, **kwargs): self.webelements[0].sel(select)




