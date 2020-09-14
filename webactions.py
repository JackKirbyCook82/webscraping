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


class EmptyWebActionError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])

class WebActionFailure(Exception):
    def __str__(self): return "\n{}".format(self.args[0])


class WebActionChain(object):
    def __init__(self, driver, timeout, *args, **kwargs):
        self.__driver, self.__timeout = driver, timeout
        self.__webactionsegments = [webactionsegment(driver, timeout, *args, **kwargs) for webactionsegment in self.WebActionSegments]
    
    def __len__(self): return len(self.__webactionsegments)
    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
    def __str__(self): return "\n".join([self.__class__.__name__]+[str(webactionsegment) for webactionsegment in iter(self)])
    def __iter__(self): return (webactionsegment for webactionsegment in self.__webactionsegments)
     
    def __call__(self, *args, **kwargs): 
        for webactionsegment in iter(self):
            webactionsegment.load()
            webactionsegment(*args, **kwargs)

    @classmethod
    def create(cls, *webactionlinks):
        assert all([isinstance(collection, tuple) for collection in webactionlinks]) 
        for collection in webactionlinks: assert all([cls in value.__subclasses__() for value in WebActionLink.registry().values()])
        if cls == WebActionChain: pass
        else: raise TypeError(type(cls))
        name = lambda index: '_'.join([cls.__name__, 'Segment{}'.format(str(index))])
        webactionsegments = [WebActionSegment(*collection)(type(name(index), (object,), {})) for index, collection in enumerate(webactionlinks, start=1)]
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebActionSegments':webactionsegments})
        return wrapper


class WebActionSegment(ABC):
    def __init__(self, driver, timeout, *args, **kwargs):
        self.__driver, self.__timeout = driver, timeout
        self.__webactionlinks = [webactionlink(driver, timeout, *args, **kwargs) for webactionlink in self.WebActionLinks]
    
    def __len__(self): return len(self.__webactionlinks)
    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
    def __str__(self): return "\n".join([self.__class__.__name__]+[str(webactionlink) for webactionlink in iter(self)])
    def __iter__(self): return (webactionlink for webactionlink in self.__webactionlinks)
    
    @property
    def driver(self): return self.__driver
    @property
    def loaded(self): return all([webactionlink.loaded for webactionlink in iter(self)])  
    def load(self): 
        for webactionlink in iter(self): webactionlink.load()
        return self
    
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): 
        if not self.loaded: raise EmptyWebActionError(str(self))
        self.execute(*args, **kwargs)   
        
    __registry = {}
    @classmethod
    def registry(cls): return cls.__registry
    @classmethod
    def register(cls, webactiontype):
        def wrapper(subclass): 
            newsubclass = type(subclass.__name__, (subclass, cls), {'webactiontype':webactiontype})
            cls.__registry[webactiontype] = newsubclass
            return newsubclass
        return wrapper
    
    @classmethod
    def create(cls, *webactionlinks):
        assert all([any([cls in value.__subclasses__() for value in WebActionLink.registry().values()]) for webactionlink in webactionlinks])
        if cls == WebActionSegment: 
            webactiontype = set([webactionlink.webactiontype for webactionlink in webactionlinks])[0]
            assert len(set([webactionlink.webactiontype for webactionlink in webactionlinks])) == 1                        
            base = cls.registry()[webactiontype]
        elif cls in WebActionSegment.registry().values():
            webactiontype = cls.webactiontype
            assert len(set([webactionlink.webactiontype for webactionlink in webactionlinks])) == 1 
            assert set([webactionlink.webactiontype for webactionlink in webactionlinks]) == webactiontype
            base = cls
        elif any([cls in value.__subclasses__() for value in WebActionSegment.registry().values()]): raise TypeError(type(cls))
        else: raise TypeError(type(cls))
        attrs = {'WebActionLinks':list(webactionlinks)}
        def wrapper(subclass): return type(subclass.__name__, (subclass, base), attrs)
        return wrapper


@WebActionSegment.register('process')
class WebProcessSegment(WebActionSegment):
    def execute(self, *args, **kwargs):
        x = ActionChains(self.driver)
        for link in iter(self): link(x)
        x.perform()

@WebActionSegment.register('operation')
class WebOperationSegment(WebActionSegment):
    def execute(self, *args, **kwargs):
        for link in iter(self): link(*args, **kwargs)


class WebActionLink(ABC):
    def __init__(self, driver, timeout, *args, **kwargs):
        self.__driver, self.__timeout = driver, timeout
        self.__webelements = [webelement(driver, timeout, *args, **kwargs) for webelement in self.WebElements] 

    def __len__(self): return len(self.__webelements)
    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
    def __str__(self): return "\n".join([self.__class__.__name__]+[str(webelement) for webelement in iter(self)])
    def __iter__(self): return (webelement for webelement in self.__webelements)
    def __getitem__(self, index): return self.__webelements[index] 
    
    @property
    def loaded(self): return all([webelement.loaded for webelement in iter(self)])  
    def load(self): 
        for webelement in iter(self): webelement.load()
        return self
    
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): 
        if not self.loaded: raise EmptyWebActionError(str(self))        
        self.execute(*args, **kwargs)

    __registry = {}
    @classmethod
    def registry(cls): return cls.__registry
    @classmethod
    def register(cls, webactiontype):
        def wrapper(subclass): 
            newsubclass = type(subclass.__name__, (subclass, cls), {'webactiontype':webactiontype})
            cls.__registry[webactiontype] = newsubclass
            return newsubclass
        return wrapper
    
    @classmethod
    def create(cls, webelement, *others, wait=None, **attrs):
        if cls == WebActionLink: raise TypeError(type(cls)) 
        elif cls in WebActionLink.registry().values(): raise TypeError(type(cls))
        elif any([cls in value.__subclasses__() for value in WebActionLink.registry().values()]): pass
        else: raise TypeError(type(cls))
        attrs = {'WebElements':[webelement, *others], 'wait':wait, **attrs}   
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), attrs)
        return wrapper


@WebActionLink.register('process')
class WebProcessLink(WebActionLink):
    @abstractmethod
    def process(self, x): pass
    def pause(self, x): 
        try: x.pause(self.wait)
        except AttributeError: pass
    
    def execute(self, x):
        self.process(x)
        self.pause(x)

@WebActionLink.register('operation')
class WebOperationLink(WebActionLink):
    @abstractmethod
    def operation(self, *args, **kwargs): pass
    def pause(self, *args, **kwargs): 
        try: time.sleep(self.wait)
        except AttributeError: pass

    def execute(self, *args, **kwargs):
        self.operation(*args, **kwargs)
        self.pause(*args, **kwargs)


# WEBACTIONLINKS
class WebClick(WebProcessLink): 
    def process(self, x): x.click(self[0].element)    

class WebDoubleClick(WebProcessLink): 
    def process(self, x): x.double_click(self[0].element)

class WebClickDown(WebProcessLink): 
    def process(self, x): x.click_and_hold(self[0].element)

class WebClickRelease(WebProcessLink):   
    def process(self, x): x.release(self[0].element)

class WebMoveTo(WebProcessLink): 
    def process(self, x): x.move_to_element(self[0].element)
 
class WebKeyDown(WebProcessLink): 
    def process(self, x): x.key_down(self.value, self[0].element)
    
class WebKeyUp(WebProcessLink): 
    def process(self, x): x.key_up(self.value, self[0].element)

class WebDragDrop(WebProcessLink): 
    def process(self, x): x.drag_and_drop(self[0].element, self[1].element)

class WebSelect(WebOperationLink): 
    def operation(self, *args, select, **kwargs): self[0].sel(select)








