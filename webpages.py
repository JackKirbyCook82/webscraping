# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
import random
from abc import ABC, abstractmethod
from lxml.html import fromstring, open_in_browser

from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebBrowserPage', 'WebRequestPage']
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
class CaptchaError(WebPageError): pass
class RefusalError(WebPageError): pass
class BadRequestError(WebPageError): pass


class WebPage(ABC):
    @classmethod
    def factory(cls, *args, pageReferer=None, pageURL, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        setattr(cls, 'PageReferer', pageReferer)
        setattr(cls, 'PageURL', pageURL)
        setattr(cls, 'PageContents', pageContents)             
    
    def __str__(self): return self.__class__.__name__  
    def __init__(self, feed, *args, wait=5, **kwargs): 
        self.setContents()
        self.setReferer(*args, **kwargs)
        self.setURL(*args, **kwargs)
        self.setFeed(feed)       
        self.__wait = wait
    
    def __call__(self, *args, **kwargs): yield from self.execute(*args, **kwargs)    
    def __getitem__(self, key): 
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.retrieve(key)
        return self.__pagecontents[key]

    @property
    def empty(self): return all([not bool(value) for value in self.__pagecontents.values()])
    @property
    def content(self): return self.__pagecontent
    @property
    def referer(self): return self.__referer
    @property
    def url(self): return self.__url
    @property
    def feed(self): return self.__feed  
    @property
    def source(self):
        try: return self.__source
        except AttributeError: raise UnLoadedWebPageError(self)

    def sleep(self):
        if isinstance(self.__wait, int): time.sleep(self.__wait)
        elif isinstance(self.__wait, tuple): time.sleep(random.uniform(*self.__wait))
        else: raise TypeError(type(self.__wait))   

    def setContents(self): self.__pagecontents = {}
    def setReferer(self, *args, **kwargs): self.__referer = self.PageReferer(*args, **kwargs) if isinstance(self.PageReferer, type)  else self.PageReferer
    def setURL(self, *args, **kwargs): self.__url = self.PageURL(*args, **kwargs) if isinstance(self.PageURL, type) else self.PageURL  
    def setFeed(self, feed): self.__feed = feed
    def setSource(self, source): self.__source = source
    
    def retrieve(self, key): self.__pagecontents[key] = self.PageContents[key](self.source)
    def retrieveall(self): self.__pagecontents = {key:value(self.source) for key, value in self.PageContents.items()}
    def retrieved(self, key): return key in self.__pagecontents.keys()
    def retrievedall(self): return all([key in self.__pagecontents.keys() for key in self.PageContents.keys()])

    @abstractmethod
    def setup(self, *args, **kwargs): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass


class WebRequestPage(WebPage):
    def __init_subclass__(cls, *args, pageType='html', pageRefusal=None, pageBadRequest=None, pageReferer=None, **kwargs):   
        setattr(cls, 'pageType', pageType)
        if pageRefusal is not None: setattr(cls, 'PageRefusal', pageRefusal)
        if pageBadRequest is not None: setattr(cls, 'PageBadRequest', pageBadRequest)
        cls.factory(*args, **kwargs)
      
    @property
    def htmltree(self): return self.source
      
    def load(self, *args, params=None, **kwargs): 
        if hasattr(self.referer, '__call__'): referer = str(self.referer(*args, **kwargs))
        elif isinstance(self.referer, str): referer = str(self.referer)
        elif self.referer is None: referer = None
        else: raise ValueError(self.referer)       
        if hasattr(self.url, '__call__'): url = str(self.url(*args, **kwargs))
        elif isinstance(self.url, str): url = str(self.url)
        else: raise ValueError(self.url)
        print("WebRequestPage Loading: {}\n{}".format(str(self), str(url)))
        if referer: 
            self.feed.get(referer)
            self.feed.headers.update({'Referer':referer})
            self.sleep()
        response = self.feed.get(url, params=params)
        response.raise_for_status()
        self.setSource(self.parser(self.pageType, response))
        refusal = self.PageRefusal(self.source) if hasattr(self, 'PageRefusal') else False
        if refusal: raise RefusalError(self, url=response.request.url, **response.request.headers)
        badrequest = self.PageBadRequest(self.source) if hasattr(self, 'PageBadReqeust') else False
        if badrequest: raise BadRequestError(self, url=response.request.url, **response.request.headers)
        self.setup(*args, **kwargs) 
        if self.empty: open_in_browser(response)
        if self.empty: raise EmptyWebPageError(self, url=response.request.url, **response.request.headers)

    @keydispatcher
    def parser(self, response): pass
    @parser.register('html')
    def parser_html(self, response): return fromstring(response.content)
    @parser.register('json')
    def parser_json(self, response): return response.json()


class WebBrowserPage(WebPage):    
    def __init_subclass__(cls, *args, pageCaptcha=None, pageBadRequest=None, pageNext=None, pageIteration=None, pageCrawl=None, **kwargs):
        if pageNext is not None: setattr(cls, 'PageNext', pageNext)
        if pageIteration is not None: setattr(cls, 'PageIteration', pageIteration)  
        if pageCrawl is not None: setattr(cls, 'PageCrawl', pageCrawl)        
        if pageBadRequest is not None: setattr(cls, 'PageBadRequest', pageBadRequest)
        if pageCaptcha is not None: setattr(cls, 'PageCaptcha', pageCaptcha)
        cls.factory(*args, **kwargs)
          
    @property
    def driver(self): return self.source 
    @property
    def currentURL(self): return self.driver.current_url
   
    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def refresh(self): self.driver.refresh

    def pageIteration(self): return self.PageIteration(self.source) if hasattr(self, 'PageIteration') else []    
    def pageNext(self): return self.PageNext(self.source) if hasattr(self, 'PageNext') else None
    def pageCrawl(self): return self.PageCrawl(self.source) if hasattr(self, 'PageCrawl') else {}

    def load(self, *args, **kwargs): 
        if hasattr(self.referer, '__call__'): referer = str(self.referer(*args, **kwargs))
        elif isinstance(self.referer, str): referer = str(self.referer)
        elif self.referer is None: referer = None
        else: raise ValueError(self.referer)       
        if hasattr(self.url, '__call__'): url = str(self.url(*args, **kwargs))
        elif isinstance(self.url, str): url = str(self.url)
        else: raise ValueError(self.url)
        print("WebBrowserPage Loading: {}\n{}".format(str(self), str(url)))
        if referer: 
            self.feed.get(referer)
            self.sleep()
        self.feed.get(url)  
        self.setSource(self.feed)
        captcha = self.PageCaptcha(self.source) if hasattr(self, 'PageCaptcha') else False
        success = captcha.solve(self.source) if captcha else True
        if not success: raise CaptchaError(self, url)
        badrequest = self.PageBadRequest(self.source) if hasattr(self, 'PageBadReqeust') else False
        if badrequest: raise BadRequestError(self, url)
        self.setup(*args, **kwargs) 
        if self.empty: raise EmptyWebPageError(self, url)
        

    

        
        
        
        
        



