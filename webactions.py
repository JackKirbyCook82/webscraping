# -*- coding: utf-8 -*-
"""
Created on Tues Sept 1 2020
@name:   WebAction Objects
@author: Jack Kirby Cook

"""

import time
from functools import update_wrapper
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys 

from webscraping.webelements import WebElement

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebActionProcess', 'WebMoveTo', 'WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebKeyDown', 'WebKeyUp', 'WebDragDrop', 'WebFill', 'WebSelect']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebActionChain(object): 
    def chain(self, action, *args): getattr(self.__actionchain, action)(*args)
    def __init__(self, driver): self.__actionchain = ActionChains(driver)
    def __len__(self): return len(self.__actionchain._actions)
    def __call__(self, *args, **kwargs): 
        self.__actionchain.perform() 


class WebActionFunctions(list):
    def __call__(self, *args, **kwargs):
        for function in self: function(*args, **kwargs)


class WebActionProcess(object): 
    def __init_subclass__(cls, *args, webactions, **kwargs):
        assert isinstance(webactions, tuple)
        assert all([issubclass(webaction, WebAction) for webaction in webactions])
        setattr(cls, 'WebActions', webactions)
                
    def __init__(self, driver, timeout, *args, **kwargs): 
        self.__webactions = [webaction(driver, timeout, *args, **kwargs) for webaction in self.WebActions]
        self.__driver = driver 
        
    def __iter__(self): return self.generator
    def __call__(self, *args, **kwargs):
        for webactions in iter(self): webactions(*args, **kwargs)

    def generator(self): 
        webactionchain = WebActionChain(self.__driver)
        webactionfunctions = WebActionFunctions()
        for webaction in self.__webactions: 
            if webaction.webactiontype == 'chain': webaction.chain(webactionchain)
            elif webaction.webactiontype == 'function': webaction.function(webactionfunctions)
            else: raise ValueError(webaction.webactiontype)
            if webaction.webactiontype == 'chain' and len(webactionfunctions) == 1: yield webactionfunctions 
            elif webaction.webactiontype == 'function' and len(webactionchain) == 1: yield webactionchain 
            elif len(webactionchain) > 0 and len(webactionfunctions) > 0: raise ValueError(len(webactionchain), len(webactionfunctions))
            else: pass     
            if webaction.webactiontype == 'chain' and len(webactionfunctions) == 1: webactionfunctions = WebActionFunctions()
            elif webaction.webactiontype == 'function' and len(webactionchain) == 1: webactionchain = WebActionChain(self.__driver)
            else: pass
        if len(webactionchain) == len(webactionfunctions) == 0: pass
        else: raise ValueError(len(webactionchain), len(webactionfunctions))

        
def webactionwait(method, wait=None):
    if not wait: return method
    if method.__name__ == 'chain': 
        def wrapper(self, webactionchain):
            assert isinstance(webactionchain, WebActionChain)
            method(self, webactionchain)
            webactionchain.chain('pause', wait)
    elif method.__name__ == 'append': 
        def wrapper(self, webactionfunctions):
            assert isinstance(webactionfunctions, WebActionFunctions)
            method(self, webactionfunctions)
            webactionfunctions.append(lambda *args, **kwargs: time.sleep(wait))
    else: raise ValueError(method.__name__)
    update_wrapper(wrapper, method)
    return wrapper


class WebAction(object): 
    __registry = []
    def __init_subclass__(cls, *webelements, wait=None, webactiontype=None, **attrs): 
        if cls in WebAction.__subclasses__(): 
            assert webactiontype is not None
            setattr(cls, 'webactiontype', webactiontype)
            return
        assert all([issubclass(webelement, WebElement) for webelement in webelements]) and hasattr(cls, 'webactiontype')
        for name, attr in attrs.items(): setattr(cls, name, staticmethod(attr) if hasattr(attr, '__call__') else attr)
        setattr(cls, 'WebElements', list(webelements))
        if cls.webactiontype == 'chain': setattr(cls, 'chain', webactionwait(cls.chain, wait))
        elif cls.webactiontype == 'function': setattr(cls, 'append', webactionwait(cls.append, wait))    
        else: raise ValueError(webactiontype)
        WebAction.__registry.append(cls)

    def __str__(self): return "{}|({})".format(self.__class__.__name__, ', '.join([str(webelement) for webelement in self.__webelements]))
    def __getitem__(self, index): return self.__webelements[index]    
    def __init__(self, driver, timeout, *args, **kwargs): self.__webelements = [webelement(driver, timeout, *args, **kwargs) for webelement in self.WebElements]
    def __new__(cls, *args, **kwargs):
        assert cls in WebAction.__registry and hasattr(cls, 'wait') and hasattr(cls, 'WebElements')
        return super().__new__(cls)
    
    def chain(self, webactionchain): raise NotImplementedError('{}.{}()'.format(self.__class__.__name__, 'chain'))
    def append(self, webactionfunctions): raise NotImplementedError('{}.{}()'.format(self.__class__.__name__, 'append'))

         
class WebMoveTo(WebAction, webactiontype='chain'): 
    def chain(self, webactionchain): webactionchain.chain('move_to_element', self[0].element)
    
class WebClick(WebAction, webactiontype='chain'): 
    def chain(self, webactionchain): webactionchain.chain('click', self[0].element)
    
class WebDoubleClick(WebAction, webactiontype='chain'): 
    def chain(self, webactionchain): webactionchain.chain('double_click', self[0].element)
    
class WebClickDown(WebAction, webactiontype='chain'): 
    def chain(self, webactionchain): webactionchain.chain('click_and_hold', self[0].element)
    
class WebClickRelease(WebAction, webactiontype='chain'): 
    def chain(self, webactionchain): webactionchain.chain('release', self[0].element)
    
class WebKeyDown(WebAction, webactiontype='chain'): 
    def chain(self, webactionchain): webactionchain.chain('key_down', getattr(Keys, self.key.upper()), self[0].element)
    
class WebKeyUp(WebAction, webactiontype='chain'): 
    def chain(self, webactionchain): webactionchain.chain('key_up', getattr(Keys, self.key.upper()), self[0].element)
    
class WebDragDrop(WebAction, webactiontype='chain'): 
    def chain(self, webactionchain): webactionchain.chain('drag_and_drop', self[0].element, self[1].element)
 
class WebFill(WebAction, webactiontype='function'):
    def append(self, webactionfunctions): webactionfunctions.append(lambda *args, **kwargs: self[0].fill(self.text.format(**kwargs)))
 
class WebSelect(WebAction, webactiontype='function'):
    def append(self, webactionfunctions): webactionfunctions.append(lambda *args, select, **kwargs: self[0].sel(select))
 
























