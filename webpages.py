# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
from lxml import html

from webscraping.webdata import EmptyWebDataError
from webscraping.webactions import EmptyWebActionsError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebBrowserPage', 'WebHTMLPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebPageError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.kwargs = kwargs
    
    def __str__(self): 
        argsstr = '\n'.join([str(arg) for arg in self.args])
        kwargsstr = '\n'.join([': '.join([key, value]) for key, value in self.kwargs.items()])
        return "{}:\n{}\n{}".format(self.__class__.__name__, argsstr, kwargsstr)

class EmptyWebPageError(WebPageError): pass
class UnLoadedWebPageError(WebPageError): pass


class WebPage(ABC):
    @classmethod
    def factory(cls, *args, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        setattr(cls, 'PageContents', pageContents)             
    
    def __str__(self): return self.__class__.__name__  
    def __init__(self, source, *args, timeout=None, **kwargs): 
        self.__source, self.__timeout = source, timeout 
        self.__pagecontents = False, {}
    
    def __getitem__(self, key): 
        if not self.loaded: raise UnLoadedWebPageError(self)
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.retrieve(key)
        return self.__pagecontents[key]

    def __call__(self, *args, **kwargs): 
        if not self.loaded: raise UnLoadedWebPageError(self)
        yield from self.execute(*args, **kwargs)

    @property
    def source(self): return self.__source  
    @property
    def timeout(self): return self.__timeout
    @property
    def empty(self): return all([not bool(value) for value in self.__pagecontents.values()])
        
    def retrieve(self, key): self.__pagecontents[key] = self.PageContents[key](self.basis, timeout=self.timeout)
    def retrieveall(self): self.__pagecontents = {key:value(self.basis, timeout=self.timeout) for key, value in self.PageContents.items()}
    def retrieved(self, key): return key in self.__pagecontents.keys()
    def retrievedall(self): return all([key in self.__pagecontents.keys() for key in self.PageContents.keys()])

    @property
    @abstractmethod
    def url(self): pass
    @property
    @abstractmethod
    def basis(self): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass


class WebHTMLPage(WebPage):
    def __init_subclass__(cls, *args, pageRefusal=None, **kwargs):    
        if pageRefusal is not None: setattr(cls, 'PageRefusal', pageRefusal)
        cls.factory(*args, **kwargs)
  
    @property
    def session(self): return self.source
    @property
    def htmltree(self): return html.fromstring(self.response.content)         
    @property
    def basis(self): return self.htmltree  
    @property
    def response(self): 
        try: return self.__response
        except AttributeError: raise UnLoadedWebPageError(self)
            
    def load(self, url, *args, parms={},  **kwargs): 
        print("WebHTMLPage Loading: {}\n{}".format(str(self), str(url)))        
        response = self.session.get(str(url), **parms)
        response.raise_for_status()
        self.__response = response        
        refusal = self.PageRefusal(self.htmltree) if hasattr(self, 'PageRefusal') else False
        if refusal:  
            refusal.log()
            refusal.throw(self.response.url, self.response.headers)        
        else: self.retrieveall()
        if self.empty: raise EmptyWebPageError(self, self.response.request.url, **self.response.request.headers)
        else: pass


class WebBrowserPage(WebPage):    
    def __init_subclass__(cls, *args, pageCaptcha=None, pageNext=None, pageIteration=None, **kwargs):
        if pageNext is not None: setattr(cls, 'PageNext', pageNext)
        if pageIteration is not None: setattr(cls, 'PageIteration', pageIteration)
        if pageCaptcha is not None: setattr(cls, 'PageCaptcha', pageCaptcha)
        cls.factory(*args, **kwargs)
          
    @property
    def driver(self): return self.source 
    @property
    def basis(self): return self.driver
   
    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def refresh(self): self.driver.refresh

    def __iter__(self): 
        if not self.loaded: raise UnLoadedWebPageError(self)
        if not hasattr(self, 'PageIteration'): return iter([])
        else: return iter(self.PageIteration(self.driver, self.timeout))
        
    def __next__(self): 
        if not self.loaded: raise UnLoadedWebPageError(self)
        if not hasattr(self, 'PageNext'): return False
        try: return self.PageNext(self.driver, self.timeout)()
        except (EmptyWebDataError, EmptyWebActionsError): return False

    def load(self, url, *args, **kwargs): 
        print("WebBrowserPage Loading: {}\n{}".format(str(self), str(url)))
        self.driver.get(str(url))  
        captcha = self.PageCaptcha(self.driver, self.timeout) if hasattr(self, 'PageCaptcha') else False
        success = captcha.solve(self.driver) if captcha else True
        if not success: captcha.throw(str(url))


             

 

    



        
        
        
        
        
        
        



