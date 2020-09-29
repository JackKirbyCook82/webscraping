# -*- coding: utf-8 -*-
"""
Created on Tues Sept 1 2020
@name:   WebAction Objects
@author: Jack Kirby Cook

"""

import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys 

from webscraping.webelements import WebElement

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebMoveTo', 'WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebKeyDown', 'WebKeyUp', 'WebDragDrop', 'WebFill', 'WebSelect']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebActionChain(object): pass    
  
      
class WebAction(object): 
    __registry = []
    def __init_subclass__(cls, *webelements, wait=None, **attrs): 
        if cls in WebAction.__subclasses__: return
        assert all([isinstance(webelement, WebElement) for webelement in webelements])
        for name, attr in attrs.items(): setattr(cls, name, staticmethod(attr) if hasattr(attr, '__call__') else attr)
        setattr(cls, 'wait', wait)
        setattr(cls, 'WebElements', list(webelements))
        WebAction.__registry.append(cls)

    def __str__(self): return "{}|({})".format(self.__class__.__name__, ', '.join([str(webelement) for webelement in self.__webelements]))
    def __getitem__(self, index): return self.__webelements[index]    
    def __init__(self, driver, timeout, *args, **kwargs): self.__webelements = [webelement(driver, timeout, *args, **kwargs) for webelement in self.WebElements]
    def __new__(cls, *args, **kwargs):
        assert cls in WebAction.__registry and hasattr(cls, 'wait') and hasattr(cls, 'WebElements')
        return super().__new__(cls)
               

class WebMoveTo(WebAction): 
    def extend(self, x): x.move_to_element(self[0].element)
    
class WebClick(WebAction): 
    def extend(self, x): x.click(self[0].element)    
    
class WebDoubleClick(WebAction): 
    def extend(self, x): x.double_click(self[0].element)
    
class WebClickDown(WebAction): 
    def extend(self, x): x.click_and_hold(self[0].element)
    
class WebClickRelease(WebAction): 
    def extend(self, x): x.release(self[0].element)
    
class WebKeyDown(WebAction): 
    def extend(self, x): x.key_down(getattr(Keys, self.key.upper()), self[0].element)
    
class WebKeyUp(WebAction): 
    def extend(self, x): x.key_up(getattr(Keys, self.key.upper()), self[0].element)
    
class WebDragDrop(WebAction): 
    def extend(self, x): x.drag_and_drop(self[0].element, self[1].element)
    
class WebFill(WebAction): 
    def execute(self, *args, **kwargs): self[0].fill(self.text.format(**kwargs))

class WebSelect(WebAction): 
    def execute(self, *args, select, **kwargs): self[0].sel(select)






