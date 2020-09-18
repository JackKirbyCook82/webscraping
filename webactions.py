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
__all__ = ['WebProcess', 'WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebDragDrop', 'WebMoveTo', 'WebKeyDown', 'WebKeyUp']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: items if isinstance(items, (list, tuple)) else [items] 
_flatten = lambda nesteditems: [item for items in nesteditems for item in items]
_filter = lambda items: [item for item in _aslist(items) if item]


class EmptyWebActionError(Exception): 
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])

class WebActionFailure(Exception):
    def __str__(self): return "\n{}".format(self.args[0])


class WebProcess(object):
    def __init_subclass__(cls, *args, actions, **kwargs):
        assert isinstance(actions, list)
        assert all([isinstance(items, tuple) for items in actions])
        assert all([item in WebAction.registry() for items in actions for item in items])
        setattr(cls, 'WebOperations', actions) 
        
    def __iter__(self): return (weboperation for weboperation in self.weboperations)
    def __len__(self): return len(self.weboperations)
    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)   
    def __str__(self): return "{}({})".format(self.__class__.__name__, ', '.join([str(webelement) for webelement in self.webelements]))   
    def __init__(self, driver, timeout, *args, **kwargs):        
        webactiontypes = [set([webaction.type for webaction in webactions]) for webactions in self.WebOperations]
        assert all([len(webactiontype) == 1 for webactiontype in webactiontypes])
        webactiontypes = [webactiontype[0] for webactiontype in webactiontypes]
        self.__driver, self.__timeout = driver, timeout
        self.__weboperations = tuple([WebOperation.registry()[webactiontype](driver, timeout, *args, webactions=webactions, **kwargs) for webactiontype, webactions in zip(webactiontypes, self.WebOperations)])
        
    @property
    def weboperations(self): return self.__weboperations
    @property
    def webelements(self): return list(set([webelement for weboperation in self.__weboperations for webelement in weboperation.webelements]))
    
    def __call__(self, *args, **kwargs): 
        for weboperation in iter(self): 
            weboperation.load()
            weboperation(*args, **kwargs)   
    

class WebOperation(ABC):
    __registry = {}
    @classmethod
    def registry(cls): return cls.__registry
    
    def __init_subclass__(cls, *args, actiontype, **kwargs):
        setattr(cls, 'type', actiontype)
        cls.__registry[actiontype] = cls

    def __iter__(self): return (webaction for webaction in self.webactions)
    def __len__(self): return len(self.webactions)
    def __repr__(self): return "{}(driver={}, timeout={})".format(repr(self.__driver), self.__timeout)     
    def __str__(self): return "{}({})".format(self.__class__.__name__, ', '.join([str(webelement) for webelement in self.webelements]))   
    def __init__(self, driver, timeout, *args, webactions, **kwargs):
        self.__driver, self.__timeout = driver, timeout
        self.__webactions = tuple([webaction(driver, timeout, *args, **kwargs) for webaction in webactions])
    
    @property
    def webactions(self): return self.__webactions
    @property
    def webelements(self): return list(set([webelement for webaction in self.__webactions for webelement in webaction.webelements.values()]))
        
    @property
    def driver(self): return self.__driver
    @property
    def loaded(self): return all([webaction.loaded for webaction in iter(self)])  
    def load(self): 
        for webaction in iter(self): webaction.load()
        return self
    
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): 
        if not self.loaded: raise EmptyWebActionError(str(self))
        self.execute(*args, **kwargs)              


class WebOperationChainable(WebOperation, actiontype='chainable'):
    def execute(self, *args, **kwargs):
        x = ActionChains(self.driver)
        for link in iter(self): link(x)
        x.perform()


class WebOperationOrderable(WebOperation, actiontype='orderable'):
    def execute(self, *args, **kwargs):
        for link in iter(self): link(*args, **kwargs)


class WebAction(object):
    __registry = []
    @classmethod
    def registry(cls): return cls.__registry
    
    def __init_subclass__(cls, *args, attrs={}, wait=None, **kwargs):        
        assert isinstance(attrs, dict)        
        for key, value in attrs.items(): setattr(cls, key, value)
        if not hasattr(cls, 'type'): 
            setattr(cls, 'type', kwargs['actiontype'])
        elif hasattr(cls, 'type') and not hasattr(cls, 'keys'): 
            setattr(cls, 'keys', _filter([kwargs.get('action', None), *kwargs.get('actions', [])]))       
        elif hasattr(cls, 'type') and hasattr(cls, 'keys') and not hasattr(cls, 'values'):
            setattr(cls, 'values', tuple([kwargs[key] for key in cls.keys]))
            setattr(cls, 'wait', wait)
            cls.__registry.append(cls)
        else: raise TypeError(cls)
        
    def __new__(cls, *args, **kwargs):
        assert cls in cls.__registry
        return super().__new__(cls)
        
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
    def webelements(self): return self.__webelements

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


class WebActionChainable(WebAction, actiontype='chainable'):
    @abstractmethod
    def process(self, x): pass
    def pause(self, x): 
        if self.wait is not None: x.pause(self.wait)
        else: pass
    
    def execute(self, x):
        self.process(x)
        self.pause(x)


class WebActionOrderable(WebAction, actiontype='orderable'):
    @abstractmethod
    def operation(self, *args, **kwargs): pass
    def pause(self, *args, **kwargs): 
        if self.wait is not None: time.sleep(self.wait)
        else: pass

    def execute(self, *args, **kwargs):
        self.operation(*args, **kwargs)
        self.pause(*args, **kwargs)


class WebClick(WebActionChainable, action='click'):
    def process(self, x): x.click(self['click'].content)    

class WebDoubleClick(WebActionChainable, action='click'): 
    def process(self, x): x.double_click(self['click'].content)

class WebClickDown(WebActionChainable, action='click'):
    def process(self, x): x.click_and_hold(self['click'].content)

class WebClickRelease(WebActionChainable, action='click'):
    def process(self, x): x.release(self['click'].content)

class WebMoveTo(WebActionChainable, action='move'):
    def process(self, x): x.move_to_element(self['move'].content)
 
class WebKeyDown(WebActionChainable, action='key'): 
    def process(self, x): x.key_down(self.keyboardvalue, self['key'].content)
    
class WebKeyUp(WebActionChainable, action='key'): 
    def process(self, x): x.key_up(self.keyboardvalue, self['key'].content)

class WebDragDrop(WebActionChainable, actions=('drag', 'drop')): 
    def process(self, x): x.drag_and_drop(self['from'].content, self['to'].content)

class WebSelect(WebActionOrderable, action='select'): 
    def operation(self, *args, select, **kwargs): self['select'].sel(select)








