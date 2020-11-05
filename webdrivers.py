# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDriver Objects
@author: Jack Kirby Cook

"""

import time
from abc import ABC, abstractmethod
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType

from webscraping.webelements import EmptyWebElementError, EmptyWebItemError, CaptchaError
from webscraping.webactions import EmptyWebActionsError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebDriverError(Exception):
    def __str__(self): return "{}: {}".format(self.__class__.__name__, self.args[0].__class__.__name__)   

class FailureWebDriverError(WebDriverError): pass
class MaxWebDriverRetryError(WebDriverError): pass
class EmptyWebDriverError(WebDriverError): pass


class WebDriver(ABC):
    def __init_subclass__(cls, *args, webpage, options={}, extensions={}, **kwargs):
        assert isinstance(options, dict) and isinstance(extensions, dict)
        setattr(cls, 'WebPage', webpage)
        setattr(cls, 'options', options)
        setattr(cls, 'extensions', extensions)        
        
    def __bool__(self): return self.__driver is not None
    def __str__(self): return self.__class__.__name__
    def __repr__(self): 
        content = {'loadtime':self.__loadtime, 'timeout':self.__timeout, 'retrys':self.__retrys, **self.options}
        string = ', '.join(['='.join([key, str(value)]) for key, value in content.items()])
        return "{}(file='{}', {})".format(self.__class__.__name__, self.__file, string)    
    
    def __init__(self, file, *args, loadtime=50, timeout=10, wait=5, retrys=5, **kwargs): 
        self.__loadtime, self.__timeout, self.__wait, self.__retrys = loadtime, timeout, wait, retrys
        self.__driver = None
        self.__file = file
                
    def __call__(self, url, *args, **kwargs):
        try: yield from self.controller(url, *args, **kwargs)
        except MaxWebDriverRetryError: raise FailureWebDriverError(self)       
    
    def controller(self, url, *args, retry=0, **kwargs):
        try: 
            print("WebDriver Running: {}".format(self.__class__.__name__))
            print("Attempt: {}|{}".format(str(retry+1), str(self.__retrys+1)))            
            yield from self.run(url, *args, **kwargs)
            print("WebDriver Success: {}".format(self.__class__.__name__), "\n")
        except (EmptyWebDriverError, EmptyWebActionsError, EmptyWebElementError, EmptyWebItemError, CaptchaError) as error:
            self.stop()
            print("WebDriver Failure: {}".format(self.__class__.__name__))
            print(str(error), '\n')
            if retry < self.__retrys: yield from self.controller(url, *args, retry=retry+1, **kwargs)
            else: raise MaxWebDriverRetryError(retry)
        
    def run(self, url, *args, **kwargs): 
        options, capabilities = self.setup(*args, **kwargs)
        self.start(options, capabilities)   
        webpage = self.WebPage(self.driver, self.timeout, *args, wait=self.wait, **kwargs)
        webpage.load(url, *args, **kwargs)
        yield from self.execute(webpage, *args, **kwargs)
        self.stop()        
        
    def start(self, options, capabilities): 
        driver = Chrome(executable_path=self.__file, chrome_options=options, desired_capabilities=capabilities) 
        driver.set_page_load_timeout(self.loadtime)
        self.__driver = driver 
        
    def stop(self):
        self.__driver.quit()
        self.__driver = None        
        
    def setup(self, *args, **kwargs):
        capabilities = self.getCapabilities(*args, **kwargs)
        proxy = self.getProxy()
        useragent = self.getUserAgent()       
        options = Options()
        options = self.setOptions(options, *args, useragent=useragent, **kwargs)
        options = self.setExtensions(options, *args, **kwargs)
        proxy.add_to_capabilities(capabilities)
        return options, capabilities            

    @classmethod
    def addOptions(cls, options): setattr(cls, 'options', options)  
    @classmethod
    def addExtensions(cls, extensions): setattr(cls, 'extensions', extensions)  
    def addProxys(self, proxys): setattr(self, 'proxys', proxys)
    def addUserAgents(self, useragents): setattr(self, 'useragents', useragents)

    def setOptions(self, options, *args, **kwargs): pass
    def setExtensions(self, options, *args, **kwargs): pass
    
    def getProxy(self): pass
    def getUserAgent(self): pass

#    def getOptions(self, options, *args, useragent=None, incognito=False, headless=False, images=True, **kwargs): 
#        options = Options()
#        options.add_argument("--start-maximized")
#        options.add_argument("--disable-notifications")
#        options.add_argument("--disable-gpu")
#        options.add_argument("user-agent={}".format(useragent))
#        if incognito: options.add_argument("--incognito")
#        if headless: 
#            options.add_argument("--headless")
#            options.add_argument("--no-sandbox")     
#        if not images: options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
#        options.add_experimental_option("excludeSwitches", ["enable-automation"])
#        options.add_experimental_option('useAutomationExtension', False)
#        return options
    
#    def getExtensions(self, options, *args, **extensions):
#        for key, value in extensions.items(): options.add_argument('--load-extension={}'.format(value))
#        return options
    
#    def getProxy(self):
#        proxy = next(self.proxy)
#        instance = Proxy({'proxyType':ProxyType.MANUAL, 'httpProxy':str(proxy), 'ftpProxy':str(proxy), 'sslProxy':str(proxy)})
#        instance.utodetect = False
#        return instance

#    def getUserAgent(self):
#        instance = next(self.useragents)
#        return instance

#    def getCapabilities(self, *args, **kwargs):
#        return DesiredCapabilities.CHROME.copy()
       
    @abstractmethod
    def execute(self, page, *args, **kwargs): pass
  
    @property
    def loadtime(self): return self.__loadtime
    @property
    def timeout(self): return self.__timeout    
    @property
    def wait(self): return self.__wait
    @property
    def url(self): return self.driver.current_url
    @property
    def html(self): return self.driver.page_source   
    @property
    def driver(self):     
        if self.__driver is None: raise EmptyWebDriverError(str(self))
        else: return self.__driver

    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def sleep(self): time.sleep(self.__wait)
    def refresh(self): 
        self.driver.refresh
        self.sleep()

    


    







    