# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
import random
from abc import ABC, abstractmethod
from lxml.html import fromstring

from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebBrowserPage', 'WebRequestPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebPageError(Exception):
    def __str__(self): return "{}|{}".format(self.__class__.__name__, self.args[0])    

class EmptyWebPageError(WebPageError): pass
class NotLoadedError(WebPageError): pass
class NotExistError(WebPageError): pass
class CaptchaError(WebPageError): pass
class RefusalError(WebPageError): pass
class BadRequestError(WebPageError): pass


class WebPage(ABC):
    @classmethod
    def factory(cls, url, *args, conditions={}, contents={}, operations={}, **kwargs):
        setattr(cls, 'URL', url)
        setattr(cls, 'Contents', contents)        
        setattr(cls, 'Conditions', conditions)
        setattr(cls, 'Operations', operations)
    
    def __str__(self): return self.__class__.__name__  
    def __init__(self, feed, *args, wait=5, **kwargs): 
        self.__url = self.URL(*args, **kwargs) if isinstance(self.URL, type) else lambda *args, **kwargs: str(self.URL)  
        try: self.__wait = int(wait)
        except TypeError: self.__wait = tuple([int(item) for item in wait])
        self.refresh()
        self.setFeed(feed)

    def __call__(self, *args, **kwargs): 
        if self.badrequest(): raise BadRequestError(self)    
        self.setup(*args, **kwargs)
        if self.empty: raise EmptyWebPageError(self)
        else: yield from self.execute(*args, **kwargs)    
    
    def __getitem__(self, key): 
        if self.isContent(key): 
            if not self.isLoadedContent(key): self.loadContent(key)
            return self.getContent(key)
        elif self.isCondition(key): 
            if not self.isLoadedCondition(key): self.loadCondition(key)
            return self.getCondition(key)
        else: raise NotExistError('{}[{}]'.format(str(self), key))
            
    @property
    def empty(self): return all([not bool(value) for value in self.__contents.values()])    
    @property
    def feed(self): return self.__feed  
    @property
    def source(self):
        try: return self.__source
        except AttributeError: raise NotLoadedError(str(self))
  
    @classmethod
    def isContent(cls, key): return key in cls.Contents.keys()
    @classmethod
    def isCondition(cls, key): return key in cls.Conditions.keys()
    @classmethod
    def isOperation(cls, key): return key in cls.Operations.keys()
  
    def isLoadedContent(self, key): return key in self.__contents.keys()
    def isLoadedCondition(self, key): return key in self.__conditions.keys()
    def isLoadedOperation(self, key): return key in self.__operations.keys()
  
    def loadContent(self, key): self.__contents[key] = self.Contents[key](self.source)
    def loadCondition(self, key): self.__conditions[key] = self.Conditions[key](self.source)
    def loadOperation(self, key): self.__operations[key] = self.Operations[key](self.source)
 
    def loadAllContents(self): self.__contents = {key:value(self.source) for key, value in self.Contents.items()}
    def loadAllCondtions(self): self.__conditions = {key:value(self.source) for key, value in self.Conditions.items()}
    def loadAllOperations(self): self.__operations = {key:value(self.source) for key, value in self.Operations.items()}
 
    def getContent(self, key): 
        try: return self.__contents[key]  
        except KeyError: 
            try: raise NotLoadedError('.'.join([str(self), self.Contents[key].__name__]))
            except KeyError: raise NotExistError('{}[{}]'.format(str(self), key))

    def getCondition(self, key): 
        try: return self.__conditions[key]  
        except KeyError: 
            try: raise NotLoadedError('.'.join([str(self), self.Conditions[key].__name__]))
            except KeyError: raise NotExistError('{}[{}]'.format(str(self), key))
    
    def getOperation(self, key): 
        try: return self.__operations[key]  
        except KeyError: 
            try: raise NotLoadedError('.'.join([str(self), self.Operations[key].__name__]))
            except KeyError: raise NotExistError('{}[{}]'.format(str(self), key))

    def getURL(self, *args, **kwargs): return self.__url
    def setFeed(self, feed): self.__feed = feed
    def setSource(self, source): self.__source = source

    def refresh(self): self.__contents = self.__conditions = self.__operations = {}
    def sleep(self):
        if isinstance(self.__wait, int): time.sleep(self.__wait)
        elif isinstance(self.__wait, tuple): time.sleep(random.uniform(*self.__wait))
        else: raise TypeError(type(self.__wait))   

    def refusal(self):
        try: refusal = self['refusal']
        except NotExistError: refusal = False
        return bool(refusal)
    
    def badrequest(self):
        try: badrequest = self['badrequest']
        except NotExistError: badrequest = False
        return bool(badrequest)

    @property
    @abstractmethod
    def url(self): pass
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
        if self.Referer is None: self.__referer = lambda *args, **kwargs: None
        else: self.__referer = self.Referer(*args, **kwargs) if isinstance(self.Referer, type) else lambda *args, **kwargs: str(self.Referer)  
        super().__init__(*args, **kwargs)
        
    @property
    def htmltree(self): return self.source
    @property
    def referer(self): return self.__referer    
    @property
    def url(self): return str(self.response.url)
    @property
    def headers(self): return self.response.headers
    @property
    def response(self):
        try: return self.__response
        except AttributeError: raise NotLoadedError(str(self))

    def getReferer(self, *args, **kwargs): return self.__referer  
    def setResponse(self, response): self.__response = response
    
    def load(self, *args, params=None, **kwargs): 
        referer = self.getReferer(*args, **kwargs)
        url = self.getURL(*args, **kwargs)
        print("WebRequestPage Loading: {}\n{}".format(str(self), str(url)))
        if self.referer: self.feed.headers.update({'Referer':str(referer)})
        response = self.feed.get(str(url), params=params)
        response.raise_for_status()
        self.setSource(self.parser(self.pageType, response))
        self.setResponse(response)
        if self.refusal(): raise RefusalError(self)

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
        assert isinstance(crawling, list)
        self.__crawling = crawling
        super().__init__(*args, **kwargs)
        
    @property
    def driver(self): return self.source 
    @property
    def url(self): return str(self.driver.current_url)
   
    def back(self): self.driver.back
    def forward(self): self.driver.forward

    def load(self, *args, **kwargs): 
        url = self.getURL(*args, **kwargs)
        print("WebRequestPage Loading: {}\n{}".format(str(self), str(url)))
        self.feed.get(str(url))  
        self.setSource(self.feed)
        if self.captcha(): raise CaptchaError(self)    
        if self.refusal(): raise RefusalError(self)

    def captcha(self):
        try: captcha = self['captcha']
        except NotExistError: captcha = False
        success = captcha.solve(self.source) if captcha else True
        return not success   

    def __iter__(self): return self.generator()
    def __next__(self): return self.crawler()

    def generator(self):
        active = True
        while active:
            self.loadOperation('iterator')
            for value in self.getOperation('iterator').values(): yield value
            self.loadOperation('next')
            active = self.getOperation('next').perform() if self.getOperation('next') else False
            if not active: return
            self.sleep()
            self.refresh()
            
    def crawler(self):
        self.loadOperation('crawler')
        crawling = {key:value for (key, value) in self.getOperation('crawler').items() if key in self.__crawling}
        try: key = random.choice(list(crawling.keys()))
        except IndexError: return False
        self.__crawling.remove(key)
        crawling[key].click()
        self.sleep()
        self.refresh()
        if self.captcha(): raise CaptchaError(self)    
        if self.refusal(): raise RefusalError(self)
        return True


        
        
        
        
        



