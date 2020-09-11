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


#class EmptyWebActionError(Exception): pass


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
            if not link.loaded: raise EmptyWebActionError(link.__class__.__name__)
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
        if len(self.__webelements) < 1: raise EmptyWebActionError(self.__class__.__name__)
          
    @property
    def loaded(self): return all([webelement.loaded for webelement in self.webelements])  
    def load(self): 
        for webelement in self.webelements: webelement.load()
        return self

    @abstractmethod
    def execute(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): 
        if not self.loaded: raise EmptyWebActionError(self.__class__.__name__)
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
        if not self.loaded: raise EmptyWebActionError(self.__class__.__name__)
        try: self.process(x)
        except AttributeError: raise ???
        if self.wait: x.pause(self.wait)
        return x

    def execute(self, *args, **kwargs):
        x = ActionChains(self.driver)
        try: self.process(x)
        except AttributeError: raise ???
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
    def operation(self, *args, select, **kwargs):
        if isinstance(select, int): self.webelements[0].isel(select)
        elif isinstance(select, str): self.webelements[0].sel(select)
        else: raise TypeError(select)










