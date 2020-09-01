# -*- coding: utf-8 -*-
"""
Created on Tues Sept 1 2020
@name:   WebAction Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
#from selenium.webdriver.common.action_chains import ActionChains

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebClick', 'WebDoubleClick', 'WebClickDown', 'WebClickRelease', 'WebDragDrop', 'WebMoveTo', 'WebKeyDown', 'WebKeyUp']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class EmptyWebActionError(Exception): pass


#class WebActionChain(list):
#    def __bool__(self): return self.loaded
#    def __init__(self, driver, timeout, *args, **kwargs): 
#        self.__driver, self.__timeout, self.__chain = driver, timeout, ActionChains(driver)
#    
#    def __call__(self):  
#        if not self: raise EmptyWebActionError()
#        actionchain = ActionChains(self.driver)
#        for webaction in self: webaction(actionchain)
#
#    @property
#    def loaded(self): return all([bool(webaction) for webaction in self.values()])
#    def load(self): 
#        for webaction in self: webaction.load()
#
#    @property
#    def driver(self): return self.__driver
#    @property
#    def timeout(self): return self.__timeout
#    
#    @classmethod
#    def register(self, key):
#        def wrapper(webaction):
#            assert isinstance(webaction, WebAction)
#            self[key] = webaction
#            return webaction
#        return wrapper


class WebAction(ABC): 
    def __bool__(self): return self.loaded
    def __init__(self, driver, timeout, *args, wait=None, **kwargs): 
        self.__driver, self.__timeout, self.__wait = driver, timeout, wait
        self.__webelement = self.WebElement(driver, timeout)       
       
#    def __call__(self, actionchain):
#        assert isinstance(actionchain, ActionChains) 
#        if not self: raise EmptyWebActionError()
#        self.execute(actionchain)
#        if self.wait: actionchain.pause(self.wait)

    @property
    def loaded(self): return self.__webelement.loaded
    def load(self): self.__webelement.load()
       
    @abstractmethod
    def execute(self, actionchain): pass
                
    @classmethod
    def create(cls, webelement): 
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebElement':webelement})
        return wrapper 


class WebClick(WebAction): 
    pass
#    def execute(self, actionchain): actionchain.click(self.__webelement)    
    
class WebDoubleClick(WebAction): 
    pass 
#    def execute(self, actionchain): actionchain.double_click(self.__webelement)
    
class WebClickDown(WebAction): 
    pass
#    def execute(self, actionchain): actionchain.click_and_hold(self.__webelement)

class WebClickRelease(WebAction): 
    pass
#    def execute(self, actionchain): actionchain.release(self.__webelement)

class WebMoveTo(WebAction): 
    pass
#    def execute(self, actionchain): actionchain.move_to_element(self.__webelement)
 


class WebKeyAction(WebAction):
    @classmethod
    def create(cls, webelement, keyvalue): 
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebElement':webelement, 'keyvalue':keyvalue})
        return wrapper   

class WebKeyDown(WebKeyAction): 
    pass
#    def execute(self, actionchain): actionchain.key_down(self.keyvalue, self.__webelement)
    
class WebKeyUp(WebKeyAction): 
    pass
#    def execute(self, actionchain): actionchain.key_up(self.keyvalue, self.__webelement)



class WebDragDrop(WebAction):   
#    def execute(self, actionchain): actionchain.drag_and_drop(self.__sourcewebelement, self.__destinationwebelement)
    
    def __init__(self, driver, timeout, *args, wait=None, **kwargs):    
        self.__driver, self.__timeout, self.__wait = driver, timeout, wait
        self.__sourcewebelement = self.SourceWebElement(driver, timeout)    
        self.__destinationwebelement = self.DestinationWebElement(driver, timeout)
        
    @property
    def loaded(self): return self.__sourcewebelement.loaded and self.__destinationwebelement.loaded
    def load(self): 
        self.__sourcewebelement.load()
        self.__destinationwebelement.load()
      
    @classmethod
    def create(cls, source, destination):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'SourceWebElement':source, 'DestinationWebElement':destination})
        return wrapper 


  



















