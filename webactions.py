# -*- coding: utf-8 -*-
"""
Created on Tues Sept 1 2020
@name:   WebAction Objects
@author: Jack Kirby Cook

"""

import time
from abc import ABC, abstractmethod
from functools import update_wrapper
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys 

from utilities.strings import uppercase
from utilities.dictionarys import SliceOrderedDict as SODict

from webscraping.webdata import WebData

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebActionProcess', 'WebMoveTo', 'WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebKeyDown', 'WebKeyUp', 'WebDragDrop', 'WebFill', 'WebSelect']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


REGISTRY = []


class EmptyWebActionsError(Exception): 
    def __str__(self): return "{}|{}".format(self.__class__.__name__, self.args[0])

class FailureWebActionsError(Exception):
    def __str__(self): return "{}|{}".format(self.__class__.__name__, self.args[0])


class WebActionProcess(object): 
    def __init_subclass__(cls, *args, steps, **kwargs):
        assert len(steps) > 0
        for webactionsID, webactions in steps:
            if isinstance(webactions, tuple): assert all([issubclass(webaction, WebAction) for webaction in webactions])
            elif isinstance(webactions, dict): assert all([issubclass(webaction, WebAction) for values in webactions.values() for webaction in values])
            else: raise TypeError(type(webactions).__name__)
        for webactionsID, webactions in steps:
            if isinstance(webactions, tuple): assert len(set([webaction.type for webaction in webactions])) == 1
            elif isinstance(webactions, dict): assert all([len(set([webaction.type for webaction in values])) == 1 for values in webactions.values()])
            else: raise TypeError(type(webactions).__name__)
        name = lambda ID, key: '_'.join([item for item in [cls.__name__, uppercase(ID), uppercase(key)] if item])
        bases = lambda values: (WebActionStep.registry()[values[0].type],)
        create = lambda ID, key, values: type(name(ID, key), bases(values), {}, webactions=values)
        WebActionSteps = SODict([(ID, {key:create(ID, key, values) for key, values in contents.items()}) if isinstance(contents, dict) else (ID, create(ID, None, contents)) for ID, contents in steps])
        setattr(cls, 'WebActionSteps', WebActionSteps)       

    def __len__(self): return len(self.WebActionSteps)
    def __bool__(self): return bool(self.value)
    def __str__(self): return "{}[{}|{}] = {}".format(self.__class__.__name__, str(self.key), str(self.index), str(bool(self.value)))    
    def __init__(self, driver): self.__driver, (self.__index, self.__key, self.__value) = driver, self.load(driver, 0, *tuple(self.WebActionSteps.items())[0])
    def __call__(self, *args, **kwargs): return self.perform(*args, **kwargs)    
    def __next__(self):
        try: (self.__index, self.__key, self.__value) = self.load(self.__driver, self.index+1, *tuple(self.WebActionSteps.items())[self.index+1])
        except IndexError: return False
        return True
        
    @property
    def index(self): return self.__index
    @property
    def key(self): return self.__key
    @property
    def value(self): return self.__value

    def load(self, driver, index, key, value): return (index, key, {k:v(driver) for k, v in value.items()}) if isinstance(value, dict) else (index, key, value(driver))
    def run(self, *args, **kwargs): return  self.value[kwargs[self.key]](*args, **kwargs) if isinstance(self.value, dict) else self.value(*args, **kwargs)  

    def perform(self, *args, **kwargs):
        if not bool(self): raise EmptyWebActionsError(str(self))
        else: return self.execute(*args, **kwargs)        
        
    def execute(self, *args, **kwargs):
        more = success = True
        while success and more: 
            success = self.run(*args, **kwargs)
            more = next(self)
        if not success: raise FailureWebActionsError(str(self))
        else: return success
        
        
class WebActionStep(ABC):
    __registry = {}
    @classmethod
    def registry(cls): return cls.__registry
    @classmethod
    def register(cls, key, value): cls.__registry[key] = value

    @classmethod
    def factory(cls, astype): 
        assert not hasattr(cls, 'type') and not hasattr(cls, 'WebActions')
        setattr(cls, 'type', astype)
        cls.register(astype, cls)
        
    @classmethod
    def create(cls, webactions): 
        assert hasattr(cls, 'type') and not hasattr(cls, 'WebActions')
        assert isinstance(webactions, (list, tuple))
        assert len(webactions) > 0
        assert all([webaction.type == cls.type for webaction in webactions])
        setattr(cls, 'WebActions', webactions) 

    def __init_subclass__(cls, **kwargs):
        if not kwargs: pass
        elif 'astype' in kwargs.keys() and 'webactions' not in kwargs.keys(): cls.factory(kwargs.pop('astype'))
        elif 'astype' not in kwargs.keys() and 'webactions' in kwargs.keys(): cls.create(kwargs.pop('webactions'))
        else: raise ValueError(kwargs)
    
    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'type') and hasattr(cls, 'WebActions')
        return super().__new__(cls)            
 
    def __bool__(self): return all([bool(webaction) for webaction in self.__webactions])
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self)))    
    def __init__(self, driver): self.__driver, self.__webactions = driver, self.load(driver)        
    def __call__(self, *args, **kwargs): 
        if not bool(self): raise EmptyWebActionsError(str(self))
        webchain = self.setup(self.__driver)
        for webaction in self.__webactions: self.append(webchain, webaction)
        return self.execute(webchain, *args, **kwargs)

    def load(self, driver):
        print("WebActionStep Loading: {}".format(self.__class__.__name__))
        webactions = [webaction(driver) for webaction in self.WebActions]
        if not all([bool(webaction) for webaction in webactions]): print("WebActionStep Missing: {}".format(self.__class__.__name__))              
        return webactions
            
    @abstractmethod
    def setup(self, driver): pass
    @abstractmethod
    def append(self, webchain, webaction, *args): pass
    @abstractmethod
    def execute(self, webchain, *args, **kwargs): pass


class WebChain(WebActionStep, astype='chain'): 
    def setup(self, driver): return ActionChains(driver)    
    def append(self, webchain, webaction): webaction.chain(webchain)
    def execute(self, webchain, *args, **kwargs): 
        webchain.perform()
        return True
    
    
class WebQueue(WebActionStep, astype='queue'): 
    def setup(self, driver): return list()
    def append(self, webchain, webaction): webaction.queue(webchain)
    def execute(self, webchain, *args, **kwargs): 
        for function in webchain: function(*args, **kwargs)
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
        assert all([issubclass(webelement, WebData) for webelement in webelements])
        setattr(cls, 'WebElements', list(webelements))
        if cls.type == 'chain': setattr(cls, 'chain', webactionwait(cls.chain, wait))
        if cls.type == 'queue': setattr(cls, 'queue', webactionwait(cls.queue, wait))
        REGISTRY.append(cls)

    def __new__(cls, *args, **kwargs):
        assert cls in REGISTRY and hasattr(cls, 'WebElements')
        return super().__new__(cls)

    def __init__(self, driver): self.__webelements = [webelement(driver) for webelement in self.WebElements]    
    def __bool__(self): return all([bool(webelement) for webelement in self.__webelements])
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(all([bool(webelement) for webelement in self.__webelements])))
    def __getitem__(self, index): return self.__webelements[index]    

    def chain(self, webactions): raise NotImplementedError('{}.{}()'.format(self.__class__.__name__, 'chain'))
    def queue(self, webactions): raise NotImplementedError('{}.{}()'.format(self.__class__.__name__, 'queue'))


class WebMoveTo(WebAction, astype='chain'): 
    def chain(self, x): x.move_to_element(self[0].DOMElement)
    
class WebClick(WebAction, astype='chain'): 
    def chain(self, x): x.click(self[0].DOMElement)
    
class WebDoubleClick(WebAction, astype='chain'): 
    def chain(self, x): x.double_click(self[0].DOMElement)
    
class WebClickDown(WebAction, astype='chain'): 
    def chain(self, x): x.click_and_hold(self[0].DOMElement)
    
class WebClickRelease(WebAction, astype='chain'): 
    def chain(self, x): x.release(self[0].DOMElement)
    
class WebKeyDown(WebAction, astype='chain'): 
    def chain(self, x): x.key_down(getattr(Keys, self.key.upper()), self[0].DOMElement)
    
class WebKeyUp(WebAction, astype='chain'): 
    def chain(self, x): x.key_up(getattr(Keys, self.key.upper()), self[0].DOMElement)
    
class WebDragDrop(WebAction, astype='chain'): 
    def chain(self, x): x.drag_and_drop(self[0].element.domelement, self[1].DOMElement)
 
class WebFill(WebAction, astype='queue'):
    def queue(self, x): x.append(lambda *args, fill, **kwargs: self[0].fill(fill))
 
class WebSelect(WebAction, astype='queue'):
    def queue(self, x): x.append(lambda *args, select, **kwargs: self[0].sel(select))























