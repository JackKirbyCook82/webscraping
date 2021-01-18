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

from webscraping.webdata import EmptyWebDataError
from webscraping.webactions import EmptyWebActionsError

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


class WebPage(ABC):
    @classmethod
    def factory(cls, *args, pageContents={}, **kwargs):
        assert isinstance(pageContents, dict)
        setattr(cls, 'PageContents', pageContents)             
    
    def __str__(self): return self.__class__.__name__  
    def __init__(self, feed, *args, timeout=None, **kwargs): 
        self.setfeed(feed)
        self.__timeout = timeout
        self.__pagecontents = {}
    
    def __call__(self, *args, **kwargs): yield from self.execute(*args, **kwargs)
    def __getitem__(self, key): 
        try: return self.__pagecontents[key]
        except KeyError: pass
        self.retrieve(key)
        return self.__pagecontents[key]

    @property
    def feed(self): return self.__feed  
    @property
    def timeout(self): return self.__timeout
    @property
    def empty(self): return all([not bool(value) for value in self.__pagecontents.values()])
    @property
    def source(self):
        try: return self.__source
        except AttributeError: raise UnLoadedWebPageError(self)
    
    def setfeed(self, feed): self.__feed = feed
    def setsource(self, source): self.__source = source
       
    def retrieve(self, key): self.__pagecontents[key] = self.PageContents[key](self.source, timeout=self.timeout)
    def retrieveall(self): self.__pagecontents = {key:value(self.source, timeout=self.timeout) for key, value in self.PageContents.items()}
    def retrieved(self, key): return key in self.__pagecontents.keys()
    def retrievedall(self): return all([key in self.__pagecontents.keys() for key in self.PageContents.keys()])

    @abstractmethod
    def setup(self, *args, **kwargs): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass


class WebRequestPage(WebPage):
    def __init_subclass__(cls, *args, pageRefusal=None, pageType='html', pageReferer=None, **kwargs):    
        if pageRefusal is not None: setattr(cls, 'PageRefusal', pageRefusal)
        setattr(cls, 'pageReferer', pageReferer)
        setattr(cls, 'pageType', pageType)
        cls.factory(*args, **kwargs)
      
    @property
    def htmltree(self): return self.source
      
    def load(self, url, *args, params=None, **kwargs): 
        print("WebHTMLPage Loading: {}\n{}".format(str(self), str(url)))
        if self.pageReferer: 
            self.feed.get(self.pageReferer)
            self.feed.headers.update({'Referer':self.pageReferer})
        response = self.feed.get(str(url), params=params)
        response.raise_for_status()
        self.setsrouce(self.parser(self.pageType, response))
        refusal = self.PageRefusal(self.source) if hasattr(self, 'PageRefusal') else False
        if not refusal: content = self.setup(*args, **kwargs) 
        else: raise RefusalError(self, url=response.request.url, **response.request.headers)  
        if self.empty: open_in_browser(response)
        else: pass
        return content    
    
        @keydispatcher
        def parser(self, response): pass
        @parser.register('html')
        def parser_html(self, response): return fromstring(self.response.content)
        @property.register('json')
        def parser_json(self, response): return response.json()


class WebBrowserPage(WebPage):    
    def __init_subclass__(cls, *args, pageCaptcha=None, pageNext=None, pageIteration=None, **kwargs):
        if pageNext is not None: setattr(cls, 'PageNext', pageNext)
        if pageIteration is not None: setattr(cls, 'PageIteration', pageIteration)
        if pageCaptcha is not None: setattr(cls, 'PageCaptcha', pageCaptcha)
        cls.factory(*args, **kwargs)
          
    @property
    def driver(self): return self.source 
   
    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def refresh(self): self.driver.refresh

    def __iter__(self): 
        if not hasattr(self, 'PageIteration'): return iter([])
        else: return iter(self.PageIteration(self.source, self.timeout))
        
    def __next__(self): 
        if not hasattr(self, 'PageNext'): return False
        try: return self.PageNext(self.source, self.timeout)()
        except (EmptyWebDataError, EmptyWebActionsError): return False

    def load(self, url, *args, **kwargs): 
        print("WebBrowserPage Loading: {}\n{}".format(str(self), str(url)))
        self.feed.get(str(url))  
        self.setsource(self.feed)
        captcha = self.PageCaptcha(self.source, self.timeout) if hasattr(self, 'PageCaptcha') else False
        success = self.solve(captcha) if captcha else True
        if success: content = self.setup(*args, **kwargs) 
        else: raise CaptchaError(self, str(url))
        return content
        
    def solve(self, captcha):
        print("WebCaptcha Clearing: {}".format(self.__class__.__name__))
        wait = WebDriverWait(self.driver, self.timeout, poll_frequency=self.frequency)         
        try: success = wait.until(EC.staleness_of(captcha.DOMElement))
        except TimeoutException: success = False           
        if success: print("WebCaptcha Cleared: {}".format(self.__class__.__name__))
        else: print("WebCaptcha Not Cleared: {}".format(self.__class__.__name__))       
        return success  
    

        
        
        
        
        



