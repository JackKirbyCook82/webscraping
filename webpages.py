# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
from lxml.html import fromstring, open_in_browser
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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
    def factory(cls, *args, pageURL, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        setattr(cls, 'PageURL', pageURL)
        setattr(cls, 'PageContents', pageContents)             
    
    def __str__(self): return self.__class__.__name__  
    def __init__(self, feed, *args, **kwargs): 
        self.setContents()
        self.setURL(*args, **kwargs)
        self.setFeed(feed)       
    
    def __call__(self, *args, query, queue, **kwargs): 
        assert isinstance(query, str) and isinstance(queue, dict)
        yield from self.execute(*args, query=query, queue=queue, **kwargs)    

    def __getitem__(self, key): 
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.retrieve(key)
        return self.__pagecontents[key]

    @property
    def url(self): return self.__url
    @property
    def feed(self): return self.__feed  
    @property
    def empty(self): return all([not bool(value) for value in self.__pagecontents.values()])
    @property
    def source(self):
        try: return self.__source
        except AttributeError: raise UnLoadedWebPageError(self)

    def setContents(self): self.__pagecontents = {}
    def setURL(self, *args, **kwargs): self.__url = self.PageURL(*args, **kwargs) if hasattr(self.__PageURL, '__call__') else self.PageURL    
    def setFeed(self, feed): self.__feed = feed
    def setSource(self, source): self.__source = source
    
    def retrieve(self, key): self.__pagecontents[key] = self.PageContents[key](self.source, timeout=self.timeout)
    def retrieveall(self): self.__pagecontents = {key:value(self.source, timeout=self.timeout) for key, value in self.PageContents.items()}
    def retrieved(self, key): return key in self.__pagecontents.keys()
    def retrievedall(self): return all([key in self.__pagecontents.keys() for key in self.PageContents.keys()])

    @abstractmethod
    def setup(self, *args, **kwargs): pass
    @abstractmethod
    def execute(self, *args, query, queue, **kwargs): pass


class WebRequestPage(WebPage):
    def __init_subclass__(cls, *args, pageType='html', pageRefusal=None, pageBadRequest=None, pageReferer=None, **kwargs):    
        if pageRefusal is not None: setattr(cls, 'PageRefusal', pageRefusal)
        if pageBadRequest is not None: setattr(cls, 'PageBadRequest', pageBadRequest)
        setattr(cls, 'pageReferer', pageReferer)
        setattr(cls, 'pageType', pageType)
        cls.factory(*args, **kwargs)
      
    @property
    def htmltree(self): return self.source
      
    def load(self, *args, params=None, **kwargs): 
        try: url = str(self.url(*args, **kwargs))
        except TypeError: url = str(self.url)
        print("WebHTMLPage Loading: {}\n{}".format(str(self), url))
        if self.pageReferer: 
            self.feed.get(self.pageReferer)
            self.feed.headers.update({'Referer':self.pageReferer})
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
        @property.register('json')
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
   
    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def refresh(self): self.driver.refresh

    def pageIteration(self): return self.PageIteration(self.source) if hasattr(self, 'PageIteration') else None    
    def pageNext(self): return self.PageNext(self.source) if hasattr(self, 'PageNext') else None
    def pageCrawl(self): return self.PageCrawl(self.source) if hasattr(self, 'PageCrawl') else None

    def load(self, *args, **kwargs): 
        try: url = str(self.url(*args, **kwargs))
        except TypeError: url = str(self.url)
        print("WebBrowserPage Loading: {}\n{}".format(str(self), url))
        self.feed.get(str(url))  
        self.setSource(self.feed)
        captcha = self.PageCaptcha(self.source) if hasattr(self, 'PageCaptcha') else False
        success = self.solve(captcha) if captcha else True
        if not success: raise CaptchaError(self, str(url))
        badrequest = self.PageBadRequest(self.source) if hasattr(self, 'PageBadReqeust') else False
        if badrequest: raise BadRequestError(self, url)
        self.setup(*args, **kwargs) 
        if self.empty: raise EmptyWebPageError(self, url)
        
    def solve(self, captcha):
        print("WebCaptcha Clearing: {}".format(self.__class__.__name__))
        wait = WebDriverWait(self.driver, 60*10, poll_frequency=15)         
        try: success = wait.until(EC.staleness_of(captcha.DOMElement))
        except TimeoutException: success = False           
        if success: print("WebCaptcha Cleared: {}".format(self.__class__.__name__))
        else: print("WebCaptcha Not Cleared: {}".format(self.__class__.__name__))       
        return success  
    

        
        
        
        
        



