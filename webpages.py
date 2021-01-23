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
    def factory(cls, url, *args, conditions={}, content={}, **kwargs):
        setattr(cls, 'URL', url)
        setattr(cls, 'Conditions', conditions)
        setattr(cls, 'Contents', content)
    
    def __str__(self): return self.__class__.__name__  
    def __init__(self, feed, *args, wait=5, **kwargs): 
        self.__url = str(self.URL(*args, **kwargs)) if isinstance(self.URL, type) else lambda *args, **kwargs: str(self.URL)  
        self.__contents = {}
        self.__operations = {}
        self.__wait = int(wait)
        self.setFeed(feed)

    def __call__(self, *args, **kwargs): yield from self.execute(*args, **kwargs)    
    def __getitem__(self, key): 
        if key in self.__contents.keys(): return self.__contents[key]
        if key in self.__operations.keys(): return self.__operations[key]
        if key in self.Contents.keys(): self.__contents[key] = self.Contents[key](self.source)
        elif key in self.Operations.keys(): self.__operations[key] = self.Operations[key](self.source)
        else: raise KeyError(key)
        return self.__getitem__(key)

    @property
    def url(self): return self.__url
    @property
    def feed(self): return self.__feed  
    @property
    def source(self):
        try: return self.__source
        except AttributeError: raise UnLoadedWebPageError(self)
    
    @property
    def empty(self): return all([not bool(value) for value in self.__contents.values()])    
    def fill(self, key): self.__content[key] = self.Content[key](self.source)
    def fillall(self): self.__content = {key:value(self.source) for key, value in self.Content.items()}

    def setFeed(self, feed): self.__feed = feed
    def setSource(self, source): self.__source = source

    def sleep(self):
        if isinstance(self.__wait, int): time.sleep(self.__wait)
        elif isinstance(self.__wait, tuple): time.sleep(random.uniform(*self.__wait))
        else: raise TypeError(type(self.__wait))   

    @abstractmethod
    def load(self, *args, **kwargs): pass
    @abstractmethod
    def setup(self, *args, **kwargs): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass


class WebRequestPage(WebPage):
    def __init_subclass__(cls, *args, url, **kwargs):   
        setattr(cls, 'type', kwargs['type'])
        setattr(cls, 'Referer', kwargs.get('referer', None))
        cls.factory(url, *args, **kwargs)
     
    def __init__(self, *args, **kwargs):
        if self.Referer is None: self.__referer = None
        else: self.__referer = str(self.Referer(*args, **kwargs)) if isinstance(self.Referer, type) else lambda *args, **kwargs: str(self.Referer)  
        super().__init__(*args, **kwargs)
        
    @property
    def htmltree(self): return self.source
    @property
    def referer(self): return self.__referer    
      
    def load(self, *args, params=None, **kwargs): 
        referer = self.referer(*args, **kwargs) if self.referer is not None else None
        url = self.url(*args, **kwargs)
        print("WebRequestPage Loading: {}\n{}".format(str(self), str(url)))
        if referer: self.feed.headers.update({'Referer':referer})
        response = self.feed.get(url, params=params)
        response.raise_for_status()
        self.setSource(self.parser(self.pageType, response))
        try: refusal = self['refusal']
        except KeyError: refusal = False
        if refusal: raise RefusalError(self, response.request.url, **response.request.headers)
        try: badrequest = self['badrequest']
        except KeyError: badrequest = False
        if badrequest: raise BadRequestError(self, response.request.url)
        self.setup(*args, **kwargs) 
        if self.empty: open_in_browser(response)
        if self.empty: raise EmptyWebPageError(self, response.request.url, **response.request.headers)

    @keydispatcher
    def parser(self, response): pass
    @parser.register('html')
    def parser_html(self, response): return fromstring(response.content)
    @parser.register('json')
    def parser_json(self, response): return response.json()


class WebBrowserPage(WebPage):    
    def __init_subclass__(cls, *args, url, **kwargs):
        cls.factory(url, *args, **kwargs)
         
    def __init__(self, *args, crawling=[], **kwargs):
        self.__crawling = crawling
        super().__init__(*args, **kwargs)
        
    @property
    def driver(self): return self.source 
    @property
    def current(self): return self.driver.current_url
   
    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def refresh(self): self.driver.refresh

    def load(self, *args, **kwargs): 
        url = self.url(*args, **kwargs)
        print("WebRequestPage Loading: {}\n{}".format(str(self), str(url)))
        self.feed.get(url)  
        self.setSource(self.feed)
        try: captcha = self['captcha']
        except KeyError: captcha = False
        success = captcha.solve(self.source) if captcha else True
        if not success: raise CaptchaError(self, url) 
        try: refusal = self['refusal']
        except KeyError: refusal = False
        if refusal: raise RefusalError(self, url)
        try: badrequest = self['badrequest']
        except KeyError: badrequest = False
        if badrequest: raise BadRequestError(self, url)        
        self.setup(*args, **kwargs) 
        if self.empty: raise EmptyWebPageError(self, url)

    def __iter__(self): return self.generator
    def __next__(self): return self.crawler()

    def generator(self):
        active = True
        while active:
            for value in self['iterator'].values(): yield value
            active = self['next'].perform() if self['next'] else False
            if active: self.sleep()
            else: pass
        
    def crawl(self):
        try: [value for key, value in self['crawler'].items() if key in self.__crawling][0].click()
        except IndexError: return False
        return True


        
        
        
        
        



