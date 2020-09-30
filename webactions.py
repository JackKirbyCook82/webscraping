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
__all__ = ['WebMoveTo', 'WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebKeyDown', 'WebKeyUp', 'WebDragDrop', 'WebFill', 'WebSelect']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebActionChain(object): 
    def __init_subclass__(cls, webactions):
        assert isinstance(webactions, tuple)
        assert all([issubclass(webaction, WebAction) for webaction in webactions])
        setattr(cls, 'WebActions', webactions)
        
    def __getitem__(self, index): return self.__webactions[index]
    def __init__(self, driver, timeout, *args, **kwargs): self.__webactions = [webaction(driver, timeout, *args, **kwargs) for webaction in self.WebActions]
    def __iter__(self): return self.generator
    def __call__(self, *args, **kwargs):
        pass
    
    # def generator(self):
    #     actionchain = ActionChains(self.__driver)
    #     for webaction in self.__webactions:
    #         try: webaction.chain(actionchain)
    #         except WebActionNotChainableError: 
    #             if len(actionchain._actions) > 0: 
    #                 yield actionchain
    #                 actionchain = ActionChains(self.__driver)
    #                 yield webaction
    #             else: yield webaction
    #     if len(actionchain._actions) > 0: yield actionchain
    #     else: pass

        
class WebActionNotExecutableError(Exception): pass 
class WebActionNotChainableError(Exception): pass  


def webactionwait(method, wait=None):
    if not wait: return method
    if method.__name__ == 'chain': 
        def wrapper(self, actionchain): 
            method(self, actionchain)
            actionchain.pause(wait)
    elif method.__name__ == 'function': 
        def wrapper(self, *args, **kwargs):
            method(self, *args, **kwargs)
            time.sleep(wait)
    else: raise ValueError(method.__name__)
    update_wrapper(wrapper, method)
    return wrapper


class WebAction(object): 
    __registry = []
    def __init_subclass__(cls, *webelements, wait=None, **attrs): 
        if cls in WebAction.__subclasses__(): return
        assert all([issubclass(webelement, WebElement) for webelement in webelements])
        for name, attr in attrs.items(): setattr(cls, name, staticmethod(attr) if hasattr(attr, '__call__') else attr)
        setattr(cls, 'WebElements', list(webelements))
        setattr(cls, 'chain', webactionwait(cls.chain, wait))
        setattr(cls, 'function', webactionwait(cls.function, wait))        
        WebAction.__registry.append(cls)

    def __str__(self): return "{}|({})".format(self.__class__.__name__, ', '.join([str(webelement) for webelement in self.__webelements]))
    def __getitem__(self, index): return self.__webelements[index]    
    def __init__(self, driver, timeout, *args, **kwargs): self.__webelements = [webelement(driver, timeout, *args, **kwargs) for webelement in self.WebElements]
    def __new__(cls, *args, **kwargs):
        assert cls in WebAction.__registry and hasattr(cls, 'wait') and hasattr(cls, 'WebElements')
        return super().__new__(cls)
    
    def chain(self, actionchain): raise WebActionNotChainableError()
    def function(self, *args, **kwargs): raise WebActionNotExecutableError()

         
class WebMoveTo(WebAction): 
    def chain(self, actionchain): actionchain.move_to_element(self[0].element)
    
class WebClick(WebAction): 
    def chain(self, actionchain): actionchain.click(self[0].element)    
    
class WebDoubleClick(WebAction): 
    def chain(self, actionchain): actionchain.double_click(self[0].element)
    
class WebClickDown(WebAction): 
    def chain(self, actionchain): actionchain.click_and_hold(self[0].element)
    
class WebClickRelease(WebAction): 
    def chain(self, actionchain): actionchain.release(self[0].element)
    
class WebKeyDown(WebAction): 
    def chain(self, actionchain): actionchain.key_down(getattr(Keys, self.key.upper()), self[0].element)
    
class WebKeyUp(WebAction): 
    def chain(self, actionchain): actionchain.key_up(getattr(Keys, self.key.upper()), self[0].element)
    
class WebDragDrop(WebAction): 
    def chain(self, actionchain): actionchain.drag_and_drop(self[0].element, self[1].element)
    
class WebFill(WebAction): 
    def function(self, *args, **kwargs): self[0].fill(self.text.format(**kwargs))

class WebSelect(WebAction): 
    def function(self, *args, select, **kwargs): self[0].sel(select)






