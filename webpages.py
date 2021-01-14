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
        setattr(cls, 'PageContents', pageContents)
        if pageNext is not None: setattr(cls, 'PageNext', pageNext)
        if pageIteration is not None: setattr(cls, 'PageIteration', pageIteration)
        if pageCaptcha is not None: setattr(cls, 'PageCaptcha', pageCaptcha)
           
    def __repr__(self): return "{}(driver={}, timeout={})".format(self.__class__.__name__, repr(self.__driver), self.__timeout)     
    def __str__(self): return self.__class__.__name__        
    def __init__(self, driver, timeout):
        assert timeout is not None
        self.__driver, self.__timeout, self.__pagecontents = driver, timeout, {}     
    
    def __call__(self, *args, **kwargs): 
        try: yield from self.execute(*args, **kwargs)    
        except (EmptyWebContentError, EmptyWebActionsError) as error: 
            try: captcha = self.PageCaptcha(self.driver, self.timeout)
            except AttributeError: raise error
            if not captcha: raise error
            else: captcha.solve(self.driver)
            yield from self.execute(*args, **kwargs)
    
    def __getitem__(self, key): 
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.__pagecontents[key] = self.PageContents[key](self.driver, self.timeout)
        return self.__pagecontents[key]

    def __iter__(self): 
        if not hasattr(self, 'PageIteration'): return iter([])
        else: return iter(self.PageIteration(self.driver, self.timeout))
        
    def __next__(self): 
        if not hasattr(self, 'PageNext'): return False
        try: return self.PageNext(self.driver, self.timeout)()
        except (EmptyWebContentError, EmptyWebActionsError): return False

    def load(self, url, *args, **kwargs): 
        print("WebBrowserPage Loading: {}\n{}".format(str(self), str(url)))
        self.driver.get(str(url))      
        captcha = self.PageCaptcha(self.driver, self.timeout)
        if captcha: captcha.solve(self.driver)
        
    @property
    def driver(self): return self.__driver  
    @property
    def timeout(self): return self.__timeout 
    @property    
    def url(self): return self.driver.current_url
    @property
    def html(self): return self.driver.page_source
    
    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def refresh(self): self.driver.refresh
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    

class WebHTMLPage(ABC):
    def __init_subclass__(cls, *args, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        setattr(cls, 'PageContents', pageContents)        

    def __repr__(self): return "{}(url={}, html={})".format(self.__class__.__name__, str(self.__url), repr(self.__html))
    def __str__(self): return self.__class__.__name__   
    def __init__(self, url, html): self.__url, self.__html, self.__pagecontents = html, {}     
    def __call__(self, *args, **kwargs): yield from self.execute(*args, **kwargs)  

    def __getitem__(self, key): 
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.__pagecontents[key] = self.PageContents[key](self.__html)
        return self.__pagecontents[key]

    @property
    def html(self): return self.__html   
    @property
    def url(self): return self.__url
 
    @abstractmethod
    def execute(self, *args, **kwargs): pass
        
        

        
        
        
        
        
        
        
        
        
        
        
        
        



