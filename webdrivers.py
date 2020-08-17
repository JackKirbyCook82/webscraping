# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   Webdriver Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
from time import sleep
import random
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebPage', 'WebDriver']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class MaxWebDriverRetryError(Exception): pass
class MissingWebDriverURLError(Exception): pass


class WebPage(ABC):
    def __init__(self, driver): self.__elements = {key:value(driver) for key, value in self.Elements.items()}    
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __getitem__(self, key): return self.__elements[key]
    def __setitem__(self, key, value): self.__elements[key] = value
    def __iter__(self): 
        for key, value in self.__elements.items(): yield key ,value
    
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    
    @classmethod
    def create(cls, **elements):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'Elements':elements})
        return wrapper  


class WebDriver(ABC):
    def __repr__(self): 
        content = {'timeout':self.__timeout, **self.__options}
        string = ', '.join(['='.join([key, str(value)]) for key, value in content.items()])
        return "{}({})".format(self.__class__.__name__, string)
    
    def __init__(self, file, *args, timeout=100, **kwargs): 
        self.__file = file
        self.__driver = None
        self.__url = kwargs.get('url', None)
        self.__options = dict(headless=kwargs.get('headless', False), images=kwargs.get('images', True))
        self.__proxy = kwargs.get('proxy', None)
        self.__timeout = timeout
        self.__success = False
        
    def __call__(self, *args, **kwargs):
        url = kwargs.get('url', self.__url)
        if url is None: raise MissingWebDriverURLError()
        yield from self.controller(url, *args, **kwargs)
        print('URL Request Success:')
        print(str(url), '\n')
        self.__success = True
    
    def controller(self, *args, **kwargs):
        yield from self.run(*args, **kwargs)    
         
    def run(self, url, *args, **kwargs): 
        options = self.getoptions(*args, **self.__options, **kwargs)
        capabilities = self.getcapabilities(*args, **kwargs)
        try: 
            proxy = next(self.__proxy)
            driverproxy = self.getproxy(str(proxy), *args, **kwargs)           
            driverproxy.add_to_capabilities(capabilities)                        
        except TypeError: pass
        self.start(url, options, capabilities)
        self.driver.get(str(url))      
        yield from self.execute(*args, **kwargs)
        self.stop()

    def start(self, url, options, capabilities): 
        self.__driver = Chrome(executable_path=self.__file, chrome_options=options, desired_capabilities=capabilities) 
        self.__driver.set_page_load_timeout(self.__timeout)
        
    def stop(self): 
        self.__driver.quit()
        self.__driver = None

    @abstractmethod
    def execute(self, *args, **kwargs): pass

    @property
    def driver(self): return self.__driver    
    @property
    def url(self): return self.driver.current_url
    @property
    def html(self): return self.driver.page_source
    @property
    def success(self): return self.success
    
    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def refresh(self): self.driver.refresh

    def sleep(self, seconds): sleep(seconds)
    def wait(self): sleep(random.randint(*self.__wait))
    
    def getoptions(self, *args, headless, images, **kwargs):
        options = Options()
        options.add_argument("--incognito")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        if headless: 
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
        if not images: options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        return options
    
    def getproxy(self, proxy, *args, **kwargs):
        instance = Proxy({'proxyType':ProxyType.MANUAL, 'httpProxy':proxy, 'ftpProxy':proxy, 'sslProxy':proxy})
        instance.autodetect = False
        return instance

    def getcapabilities(self, *args, **kwargs):
        return DesiredCapabilities.CHROME.copy()


       












    