# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod

from webscraping.webdata import EmptyWebContentError
from webscraping.webactions import EmptyWebActionsError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebBrowserPage', 'WebHTMLPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebBrowserPage(ABC):    
    def __init_subclass__(cls, *args, pageCaptcha=None, pageNext=None, pageIteration=None, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        if pageNext is not None: setattr(cls, 'PageNext', pageNext)
        if pageIteration is not None: setattr(cls, 'PageIteration', pageIteration)
        if pageCaptcha is not None: setattr(cls, 'PageCaptcha', pageCaptcha)
        setattr(cls, 'PageContents', pageContents)
    
    def __repr__(self): return "{}(driver={}, timeout={})".format(self.__class__.__name__, repr(self.__driver), self.__timeout)     
    def __str__(self): return self.__class__.__name__        
    def __init__(self, driver, timeout): self.__driver, self.__timeout, self.__pagecontents = driver, timeout, {}     
    def __call__(self, *args, **kwargs): 
        try: return self.execute(*args, **kwargs)    
        except (EmptyWebContentError, EmptyWebActionsError) as error: 
            captcha = self.PageCaptcha(self.__driver, self.__timeout)
            if not captcha: raise error
            else: captcha.clear()
            return self.execute(*args, **kwargs)
    
    def __getitem__(self, key): 
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.__pagecontents[key] = self.PageContents[key](self.__driver, self.__timeout)
        return self.__pagecontents[key]

    def __iter__(self): 
        try: pageiteration = self.PageIteration(self.__driver, self.__timeout)
        except AttributeError: return iter([])
        if not bool(pageiteration): 
            captcha = self.PageCaptcha(self.__driver, self.__timeout)
            if not captcha: return iter([])
            else: captcha.clear()
        else: return iter(pageiteration)
        return iter(self.PageIteration(self.__driver, self.__timeout))
              
    def __next__(self): 
        try: return self.PageNext(self.__driver, self.__timeout)()
        except (AttributeError, EmptyWebContentError, EmptyWebActionsError): return False

    def load(self, url, *args, **kwargs): 
        print("WebBrowserPage Loading: {}".format(str(self)))
        self.driver.get(str(url))      
        captcha = self.PageCaptcha(self.__driver, self.__timeout)
        if captcha: captcha.clear()
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout      
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    

class WebHTMLPage(ABC):
    def __init_subclass__(cls, *args, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        setattr(cls, 'PageContents', pageContents)        

    def __repr__(self): return "{}(html={})".format(self.__class__.__name__, self.html)
    def __str__(self): return self.__class__.__name__   
    def __init__(self, html): self.__html, self.__pagecontents = html, {}     
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)  

    def __getitem__(self, key): 
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.__pagecontents[key] = self.PageContents[key](self.__html)
        return self.__pagecontents[key]

    @property
    def html(self): return self.__html    
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
        
        

        
        
        
        
        
        
        
        
        
        
        
        
        



