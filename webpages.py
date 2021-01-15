# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod

from webscraping.webdata import EmptyWebDataError
from webscraping.webactions import EmptyWebActionsError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebBrowserPage', 'WebHTMLPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebPageError(Exception):
    def __str__(self): return "{}:\n{}".format(self.__class__.__name__, self.args[0])

class EmptyWebPageError(WebPageError): pass


class WebPage(ABC):
    @classmethod
    def factory(cls, *args, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        setattr(cls, 'PageContents', pageContents)             
    
    def __str__(self): return self.__class__.__name__  
    def __init__(self, source, *args, timeout=None, **kwargs): 
        self.__source, self.__timeout = source, timeout 
        self.__pagecontents = {}
    
    def __getitem__(self, key): 
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.__pagecontents[key] = self.PageContents[key](self.source, timeout=self.timeout)
        return self.__pagecontents[key]

    def __call__(self, *args, **kwargs): 
        self.check(*args, **kwargs)
        yield from self.execute(*args, **kwargs)

    @property
    def source(self): return self.__source  
    @property
    def timeout(self): return self.__timeout 
    @property
    @abstractmethod
    def url(self): pass

    @abstractmethod
    def check(self, *args, **kwargs): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass

#    def load(self, key): self.__pagecontents[key] = self.PageContents[key](self.source, timeout=self.timeout)
#    def loadall(self): self.__pagecontents = {key:value(self.source, timeout=self.timeout) for key, value in self.PageContents.items()}


class WebHTMLPage(WebPage):
    def __init_subclass__(cls, *args, pageRefusal=None, **kwargs):    
        if pageRefusal is not None: setattr(cls, 'PageRefusal', pageRefusal)
        cls.factory(*args, **kwargs)
  
    @property
    def htmltree(self): return self.source
    @property
    def url(self): return self.htmltree.base_url      
    
    def check(self, *args, **kwargs): 
        if not hasattr(self, 'PageRefusal'): return
        refusal = self.PageRefusal(self.htmltree)
        if not refusal: return 
        refusal.log()
        refusal.throw()
       
#    def load(self, url, *args, **kwargs): 
#        print("WebHTMLPage Loading: {}\n{}".format(str(self), str(self.url)))        
       

class WebBrowserPage(WebPage):    
    def __init_subclass__(cls, *args, pageCaptcha=None, pageNext=None, pageIteration=None, **kwargs):
        if pageNext is not None: setattr(cls, 'PageNext', pageNext)
        if pageIteration is not None: setattr(cls, 'PageIteration', pageIteration)
        if pageCaptcha is not None: setattr(cls, 'PageCaptcha', pageCaptcha)
        cls.factory(*args, **kwargs)
          
    @property
    def driver(self): return self.source 
    @property    
    def url(self): return self.driver.current_url
    
    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def refresh(self): self.driver.refresh

    def __iter__(self): 
        if not hasattr(self, 'PageIteration'): return iter([])
        else: return iter(self.PageIteration(self.driver, self.timeout))
        
    def __next__(self): 
        if not hasattr(self, 'PageNext'): return False
        try: return self.PageNext(self.driver, self.timeout)()
        except (EmptyWebDataError, EmptyWebActionsError): return False

    def check(self, *args, **kwargs): 
        if not hasattr(self, 'PageCaptcha'): return
        captcha = self.PageCaptcha(self.driver, self.timeout)
        if not captcha: return
        success = captcha.solve(self.driver)
        if not success: captcha.throw()
        else: return

#    def load(self, url, *args, **kwargs): 
#        print("WebBrowserPage Loading: {}\n{}".format(str(self), str(url)))
#        self.driver.get(str(url))    



             

 

    



        
        
        
        
        
        
        



