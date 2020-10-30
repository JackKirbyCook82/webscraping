# -*- coding: utf-8 -*-
"""
Created on Tues Sept 1 2020
@name:   WebAction Objects
@author: Jack Kirby Cook

"""

import time
from abc import ABC, abstractmethod
from functools import update_wrapper
from collections import OrderedDict as ODict
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys 

from webscraping.webelements import WebElement

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebActionProcess', 'WebMoveTo', 'WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebKeyDown', 'WebKeyUp', 'WebDragDrop', 'WebFill', 'WebSelect']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


REGISTRY = []


class EmptyWebActionsError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])


class WebActionProcess(object): 
    def __init_subclass__(cls, *args, steps, **kwargs):
        for ID, contents in steps:
            if isinstance(contents, tuple): assert all([issubclass(webaction, WebAction) for webaction in contents])
            elif isinstance(contents, dict): assert all([issubclass(webaction, WebAction) for values in contents.values() for webaction in values])
            else: raise TypeError(type(contents).__name__)
        for ID, contents in steps:
            if isinstance(contents, tuple): assert len(set([webaction.type for webaction in contents])) == 1
            elif isinstance(contents, dict): assert all([len(set([webaction.type for webaction in values])) == 1 for values in contents.values()])
            else: raise TypeError(type(contents).__name__)
        setattr(cls, 'WebActions', ODict([(ID, contents) for ID, contents in steps]))
    
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout  
               
    def __init__(self, driver, timeout, *args, **kwargs): self.__driver, self.__timeout = driver, timeout
    def __call__(self, *args, **kwargs): return all([self.execute(webactionID, webactions, *args, **kwargs) for webactionID, webactions in self.WebActions.items()])
    
    def execute(self, webactionID, webactions, *args, **kwargs):
        webactions = webactions[kwargs[webactionID]] if isinstance(webactions, dict) else webactions
        webcollection = WebCollection.create(self.driver, self.timeout, *webactions)  
        return webcollection(*args, **kwargs)


class WebCollection(ABC):
    __registry = {}
    @classmethod
    def registry(cls): return cls.__registry
    @classmethod
    def register(cls, key, value): cls.__registry[key] = value
 
    @classmethod
    def create(cls, driver, timeout, *webactions): 
        astype = set([webaction.type for webaction in webactions])
        assert len(astype) == 1
        astype = list(astype)[0]
        return cls.registry()[astype](driver, timeout, *webactions)           
 
    def __init_subclass__(cls, astype): cls.register(astype, cls)   
    def __new__(cls, driver, timeout, *webactions):
        assert cls in WebCollection.registry().values()
        return super().__new__(cls)
    
    def __bool__(self): return all([bool(webaction) for webaction in self.__webactions])
    def __str__(self): return "{}\n{}".format(self.__class__.__name__, '\n'.join([str(webaction) for webaction in self.__webactions]))
    def __init__(self, driver, timeout, *webactions): 
        self.__webactions = [webaction(driver, timeout) for webaction in webactions]
        self.setup(driver)
            
    def __call__(self, *args, **kwargs): 
        if not self: raise EmptyWebActionsError(self)   
        for webaction in self.__webactions: self.append(webaction)   
        return self.execute(*args, **kwargs)

    @abstractmethod
    def setup(self, driver): pass
    @abstractmethod
    def append(self, webaction, *args): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass


class WebChain(WebCollection, astype='chain'): 
    def setup(self, driver): self.__actionchains = ActionChains(driver)    
    def append(self, webaction): webaction.chain(self.__actionchains)
    def execute(self, *args, **kwargs): 
        self.__actionchains.perform()
        return True
    
    
class WebQueue(WebCollection, astype='queue'): 
    def setup(self, driver): self.__actionqueue = list()
    def append(self, webaction): webaction.queue(self.__actionqueue)
    def execute(self, *args, **kwargs): 
        for function in self.__actionqueue: function(*args, **kwargs)
        return True


def webactionwait(method, wait=None):
    if not wait: return method
    if method.__name__ == 'chain': 
        def wrapper(self, x):
            method(self, x)
            x.pause(wait)
    elif method.__name__ == 'queue': 
        def wrapper(self, x):
            method(self, x)
            x.append(lambda *args, **kwargs: time.sleep(wait))
    else: raise ValueError(method.__name__)
    update_wrapper(wrapper, method)
    return wrapper


class WebAction(ABC): 
    def __init_subclass__(cls, astype=None, on=[], wait=None): 
        if cls in WebAction.__subclasses__(): 
            assert astype is not None
            setattr(cls, 'type', astype)
            return
        webelements = list(on) if isinstance(on, (tuple, list)) else [on]
        assert all([issubclass(webelement, WebElement) for webelement in webelements])
        setattr(cls, 'WebElements', list(webelements))
        if cls.type == 'chain': setattr(cls, 'chain', webactionwait(cls.chain, wait))
        if cls.type == 'queue': setattr(cls, 'queue', webactionwait(cls.queue, wait))
        REGISTRY.append(cls)

    def __bool__(self): return all([bool(webelement) for webelement in self.__webelements])
    def __str__(self): return "{}|({})".format(self.__class__.__name__, ', '.join([str(webelement) for webelement in self.__webelements]))
    def __getitem__(self, index): return self.__webelements[index]    
    def __init__(self, driver, timeout): self.__webelements = [webelement(driver, timeout) for webelement in self.WebElements]
    def __new__(cls, *args, **kwargs):
        assert cls in REGISTRY and hasattr(cls, 'WebElements')
        return super().__new__(cls)

    def chain(self, webactions): raise NotImplementedError('{}.{}()'.format(self.__class__.__name__, 'chain'))
    def queue(self, webactions): raise NotImplementedError('{}.{}()'.format(self.__class__.__name__, 'queue'))


class WebMoveTo(WebAction, astype='chain'): 
    def chain(self, x): x.move_to_element(self[0].element.DOMElement)
    
class WebClick(WebAction, astype='chain'): 
    def chain(self, x): x.click(self[0].element.DOMElement)
    
class WebDoubleClick(WebAction, astype='chain'): 
    def chain(self, x): x.double_click(self[0].element.DOMElement)
    
class WebClickDown(WebAction, astype='chain'): 
    def chain(self, x): x.click_and_hold(self[0].element.DOMElement)
    
class WebClickRelease(WebAction, astype='chain'): 
    def chain(self, x): x.release(self[0].element.DOMElement)
    
class WebKeyDown(WebAction, astype='chain'): 
    def chain(self, x): x.key_down(getattr(Keys, self.key.upper()), self[0].element.DOMElement)
    
class WebKeyUp(WebAction, astype='chain'): 
    def chain(self, x): x.key_up(getattr(Keys, self.key.upper()), self[0].element.DOMElement)
    
class WebDragDrop(WebAction, astype='chain'): 
    def chain(self, x): x.drag_and_drop(self[0].element.domelement, self[1].element.DOMElement)
 
class WebFill(WebAction, astype='queue'):
    def queue(self, x): x.append(lambda *args, **kwargs: self[0].fill(self.text.format(**kwargs)))
 
class WebSelect(WebAction, astype='queue'):
    def queue(self, x): x.append(lambda *args, select, **kwargs: self[0].sel(select))























