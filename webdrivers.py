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

from webscraping.elements import EmptyElementError
from webscraping.webpages import EmptyPageError, FailurePageError, CaptchaPageError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class MaxDriverRetryError(Exception): pass
class EmptyDriverError(Exception):
    def __str__(self): return "{}\n{}".format(self.__class__.__name__, self.args[0])


class WebDriver(ABC):
    def __init_subclass__(cls, *args, page, options={}, extensions={}, **kwargs):
        assert isinstance(options, dict) and isinstance(extensions, dict)
        setattr(cls, 'WebPage', page)
        setattr(cls, 'options', options)
        setattr(cls, 'extensions', extensions)        
        
    def __bool__(self): return self.__driver is not None
    def __str__(self): return self.__class__.__name__
    def __repr__(self): 
        content = {'loadtime':self.__loadtime, 'timeout':self.__timeout, 'retrys':self.__retrys, **self.options}
        string = ', '.join(['='.join([key, str(value)]) for key, value in content.items()])
        return "{}(file='{}', {})".format(self.__class__.__name__, self.__file, string)    
    
    def __init__(self, file, *args, loadtime=50, timeout=10, wait=10, retrys=5, **kwargs): 
        self.__loadtime, self.__timeout, self.__wait, self.__retrys = loadtime, timeout, wait, retrys
        self.proxy = kwargs.get('proxy', None)
        self.__driver = None
        self.__success = False
        self.__file = file
                
    def __call__(self, *args, **kwargs):
        try: 
            yield from self.controller(*args, **kwargs)
            self.__success = True
        except MaxDriverRetryError:
            self.__success = False            
    
    def controller(self, *args, retry=0, **kwargs):
        try: 
            print("WebDriver Running: {}".format(self.__class__.__name__))
            print("Attempt: {}|{}".format(str(retry+1), str(self.__retrys+1)))            
            yield from self.run(*args, **kwargs)
            print("WebDriver Success: {}".format(self.__class__.__name__), "\n")
        except (EmptyElementError, EmptyPageError, FailurePageError, CaptchaPageError, EmptyDriverError) as error:
            self.stop(False)
            print("WebDriver Failure: {}".format(self.__class__.__name__))
            print(str(error), '\n')
            if retry < self.__retrys: yield from self.controller(*args, retry=retry+1, **kwargs)
            else: raise MaxDriverRetryError(retry)
        
    def run(self, *args, **kwargs): 
        options, capabilities = self.setup(*args, **kwargs)
        self.start(options, capabilities)   
        page = self.WebPage(self.driver, self.timeout, *args, wait=self.wait, **kwargs)
        page.load(*args, **kwargs)
        page.checkFailure()
        yield from self.execute(page, *args, **kwargs)
        self.stop(True)        
        
    def setup(self, *args, **kwargs):
        options = Options()
        options = self.getOptions(options, **self.options)
        options = self.getExtensions(options, **self.extensions)
        capabilities = self.getCapabilities(*args, **kwargs)
        try: 
            proxy = next(self.proxy)
            driverproxy = self.getProxy(str(proxy), *args, **kwargs)           
            driverproxy.add_to_capabilities(capabilities)                        
        except TypeError: pass   
        return options, capabilities     

    def start(self, options, capabilities): 
        driver = Chrome(executable_path=self.__file, chrome_options=options, desired_capabilities=capabilities) 
        driver.set_page_load_timeout(self.loadtime)
        self.__driver = driver 
        
    def stop(self, success):
        assert isinstance(success, bool)
        self.__driver.quit()
        self.__driver = None
        self.__success = success

    @classmethod
    def addOptions(cls, options): setattr(cls, 'options', options)  
    def getOptions(self, options, *args, incognito, headless, images, **kwargs): 
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        if incognito: options.add_argument("--incognito")
        if headless: 
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")     
        if not images: options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        return options
    
    @classmethod
    def addExtensions(cls, extensions): setattr(cls, 'extensions', extensions)  
    def getExtensions(self, options, *args, **extensions):
        for key, value in extensions.items(): options.add_argument('--load-extension={}'.format(value))
        return options
    
    def addProxy(self, proxy): self.proxy = proxy
    def getProxy(self, proxy, *args, **kwargs):
        instance = Proxy({'proxyType':ProxyType.MANUAL, 'httpProxy':proxy, 'ftpProxy':proxy, 'sslProxy':proxy})
        instance.autodetect = False
        return instance

    def getCapabilities(self, *args, **kwargs):
        return DesiredCapabilities.CHROME.copy()
       
    @abstractmethod
    def execute(self, page, *args, **kwargs): pass
 
    @property
    def success(self): return self.__success    
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

    


    







    