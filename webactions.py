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
__all__ = ['WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebDragDrop', 'WebMoveTo', 'WebKeyDown', 'WebKeyUp']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebActionError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])

class WebActionFailure(Exception):
    def __str__(self): return "\n{}".format(self.args[0])


#class WebActionChain(object):
#    def __iter__(self): return (webactionsegment for webactionsegment in self.__webactionsegments)
#    def __len__(self): return len(self.__webactionsegments)
#    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
#    def __str__(self):  return "{}({})".format(self.__class__.__name__, ', '.join([str(webelement) for webelement in self.webelements]))
#    def __init__(self, driver, timeout, *args, **kwargs):
#        self.__driver, self.__timeout = driver, timeout
#        self.__webactionsegments = [webactionsegment(driver, timeout, *args, **kwargs) for webactionsegment in self.WebActionSegments]
#
#    @property
#    def webactionsegments(self): return self.__webactionsegments
#    @property
#    def webactionlinks(self): return [webactionsegment for webactionsegment in self.webactionsegments for webactionlink in webactionsegment.webactionlinks]
#    @property
#    def webelements(self): return list(set([webelement for webactionlink in self.webactionlinks for webelement in webactionlink.webelements]))
#           
#    def __call__(self, *args, **kwargs): 
#        for webactionsegment in iter(self):
#            webactionsegment.load()
#            webactionsegment(*args, **kwargs)
#
#    @classmethod
#    def create(cls, *webactionlinks):
#        assert cls == WebActionChain
#        assert all([isinstance(collection, tuple) for collection in webactionlinks]) 
#        for collection in webactionlinks: 
#            for webactionlink in collection:
#                assert any([issubclass(webactionlink, subsubclass) for subclass in WebActionLink.registry().values() for subsubclass in subclass.__subclasses__()])
#        function = lambda index: type('_'.join([cls.__name__, 'Segment{}'.format(index)]), (WebActionSegment,), {})
#        webactionsegments = [WebActionSegment.create(*collection)(function(index)) for index, collection in enumerate(webactionlinks, start=1)]
#        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebActionSegments':webactionsegments})
#        return wrapper
#
#
#class WebActionSegment(ABC):
#    def __iter__(self): return (webactionlink for webactionlink in self.webactionlinks)
#    def __len__(self): return len(self.webactionlinks)
#    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
##    def __str__(self):  return "{}({})".format(self.__class__.__name__, ', '.join([str(webelement) for webelement in self.webelements]))    
#    def __init__(self, driver, timeout, *args, **kwargs):
#        self.__driver, self.__timeout = driver, timeout
#        self.__webactionlinks = [webactionlink(driver, timeout, *args, **kwargs) for webactionlink in self.WebActionLinks]
#    
#    @property
#    def webactionlinks(self): return self.__webactionlinks
##    @property
##    def webelements(self): return list(set([webelement for webactionlink in self.webactionlinks for webelement in webactionlink.webelements]))
#    
#    @property
#    def driver(self): return self.__driver
#    @property
#    def loaded(self): return all([webactionlink.loaded for webactionlink in iter(self)])  
#    def load(self): 
#        for webactionlink in iter(self): webactionlink.load()
#        return self
#    
#    @abstractmethod
#    def execute(self, *args, **kwargs): pass
#    def __call__(self, *args, **kwargs): 
#        if not self.loaded: raise EmptyWebActionError(str(self))
#        self.execute(*args, **kwargs)   
#        
#    __registry = {}
#    @classmethod
#    def registry(cls): return cls.__registry
#    @classmethod
#    def register(cls, webactiontype):
#        def wrapper(subclass): 
#            newsubclass = type(subclass.__name__, (subclass, cls), {'webactiontype':webactiontype})
#            cls.__registry[webactiontype] = newsubclass
#            return newsubclass
#        return wrapper
#    
#    @classmethod
#    def create(cls, *webactionlinks):
#        assert cls == WebActionSegment
#        for webactionlink in webactionlinks:
#            assert any([issubclass(webactionlink, subsubclass) for subclass in WebActionLink.registry().values() for subsubclass in subclass.__subclasses__()])
#        webactiontypes = set([webactionlink.webactiontype for webactionlink in webactionlinks])
#        assert len(webactiontypes) == 1
#        webactiontype = list(webactiontypes)[0]                        
#        base = cls.registry()[webactiontype]        
#        attrs = {'WebActionLinks':list(webactionlinks)}
#        def wrapper(subclass): return type(subclass.__name__, (subclass, base), attrs)
#        return wrapper
#
#
#@WebActionSegment.register('process')
#class WebProcessSegment(WebActionSegment):
#    def execute(self, *args, **kwargs):
#        x = ActionChains(self.driver)
#        for link in iter(self): link(x)
#        x.perform()
#
#@WebActionSegment.register('operation')
#class WebOperationSegment(WebActionSegment):
#    def execute(self, *args, **kwargs):
#        for link in iter(self): link(*args, **kwargs)


class WebActionLink(object):
    def __init_subclass__(cls, *args, attrs={}, **kwargs):
        assert isinstance(attrs, dict)
        if cls in WebActionLink.__subclasses__(): setattr(cls, 'type', kwargs['type'])
        elif cls in [subsubclass for subclass in WebActionLink.__subclasses__() for subsubclass in subclass.__subclasses__()]: setattr(cls, 'keys', tuple(kwargs['keys']))
        else: setattr(cls, 'values', tuple([kwargs[key] for key in cls.keys]))
        for key, value in attrs.items(): setattr(cls, key, value)
        
    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)    
    def __str__(self): return "{}({})".format(self.__class__.__name__, ', '.join(['='.join([key, str(webelement)]) for key, webelement in self.webelements.items()]))   
    def __init__(self, driver, timeout, *args, **kwargs):
        self.__driver, self.__timeout = driver, timeout
        self.__webelements = {key:value(driver, timeout, *args, **kwargs) for key, value in zip(self.keys, self.values)}         
        
    def __len__(self): return len(self.webelements)
    def __iter__(self): return (webelement for webelement in self.webelements.values())
    def __getitem__(self, key): 
        if isinstance(key, str): return {key:value for key, value in zip(self.keys, self.values)}[key]
        elif isinstance(key, int): return self.values[key]
        else: raise TypeError(type(key))

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


class WebProcessLink(WebActionLink, **{'type':'process'}):
    @abstractmethod
    def process(self, x): pass
    def pause(self, x): 
        if self.wait is not None: x.pause(self.wait)
        else: pass
    
    def execute(self, x):
        self.process(x)
        self.pause(x)


class WebOperationLink(WebActionLink, **{'type':'operation'}):
    @abstractmethod
    def operation(self, *args, **kwargs): pass
    def pause(self, *args, **kwargs): 
        if self.wait is not None: time.sleep(self.wait)
        else: pass

    def execute(self, *args, **kwargs):
        self.operation(*args, **kwargs)
        self.pause(*args, **kwargs)


# WEBACTIONLINKS
class WebClick(WebProcessLink, keys=('click',)):
    def process(self, x): x.click(self['click'].content)    

class WebDoubleClick(WebProcessLink, keys=('click',)): 
    def process(self, x): x.double_click(self['click'].content)

class WebClickDown(WebProcessLink, keys=('click',)):
    def process(self, x): x.click_and_hold(self['click'].content)

class WebClickRelease(WebProcessLink, keys=('click',)):
    def process(self, x): x.release(self['click'].content)

class WebMoveTo(WebProcessLink, keys=('move',)):
    def process(self, x): x.move_to_element(self['move'].content)
 
class WebKeyDown(WebProcessLink, keys=('key',)): 
    def process(self, x): x.key_down(self.keyboardvalue, self['key'].content)
    
class WebKeyUp(WebProcessLink, keys=('key',)): 
    def process(self, x): x.key_up(self.keyboardvalue, self['key'].content)

class WebDragDrop(WebProcessLink, keys=('from', 'to',)): 
    def process(self, x): x.drag_and_drop(self['from'].content, self['to'].content)

class WebSelect(WebOperationLink, keys=('select',)): 
    def operation(self, *args, select, **kwargs): self['select'].sel(select)








