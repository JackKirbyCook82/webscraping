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
from selenium.common.exceptions import TimeoutException, WebDriverException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver', 'WebPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class MaxWebDriverRetryError(Exception): pass
class MissingWebDriverURLError(Exception): pass


class WebDriver(ABC):
    def __init__(self, file, *args, retrys=5, wait=(5, 10), timeout=100, **kwargs): 
        self.__file = file
        self.__url = kwargs.get('url', None)
        self.__options = dict(headless=kwargs.get('headless', False), images=kwargs.get('images', True))
        self.__proxy = kwargs.get('proxy', None)
        self.__timeout = timeout
        self.__retrys = retrys
        self.__wait = wait
        
    def __call__(self, *args, **kwargs):
        url = kwargs.get('url', self.__url)
        if url is None: raise MissingWebDriverURLError()
        yield from self.controller(*args, **kwargs)
    
    def controller(self, *args, retrys=0, **kwargs):
        if retrys > self.__retrys: raise MaxWebDriverRetryError()
        try: yield from self.run(*args, **kwargs)
        except (TimeoutException, WebDriverException):
            self.sleep(self.__retry)
            yield from self.controller(*args, retrys=retrys+1, **kwargs)        
         
    def run(self, url, *args, **kwargs): 
        options = self.getoptions(*args, **self.__options, **kwargs)
        capabilities = self.getcapabilities(*args, **kwargs)
        try: 
            proxy = next(self.__proxy)
            driverproxy = self.getproxy(str(proxy), *args, **kwargs)           
            driverproxy.add_to_capabilities(capabilities)                        
        except AttributeError: pass
        driversetup = dict(executable_path=self.__file, chrome_options=options, desired_capabilities=capabilities)
        driver = Chrome(**driversetup) 
        driver.set_page_load_timeout(self.__timeout)
        driver.get(str(url))       
        yield from self.execute(*args, **kwargs)
        driver.quit()

    @abstractmethod
    def execute(self, *args, **kwargs): pass

    @property
    def driver(self): return self.__driver    
    @property
    def url(self): return self.__driver.current_url
    @property
    def html(self): return self.__driver.page_source
    
    def back(self): self.__driver.back
    def forward(self): self.__driver.forward
    def refresh(self): self.__driver.refresh

    def sleep(self, seconds): sleep(seconds)
    def wait(self): sleep(random.randint(*self.__wait))
    
    def getoptions(self, *args, headless, images, **kwargs):
        options = Options()
        options.add_argument("--incognito", "--start-maximized", "--disable-notifications")
        if headless: options.add_argument("--headless", "--no-sandbox")
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


class WebPage(ABC):
    def __init__(self, webdriver): self.__webelements = {key:value(webdriver) for key, value in self.__registry.items()}
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __getitem__(self, key): return self.__webelements[key]
    def __setitem__(self, key, value): self.__webelements[key] = value
    def __getattr__(self, attr): 
        try: return self.__webelements[attr]
        except KeyError: raise AttributeError(attr)
    
    @classmethod
    def create(cls, **webelements):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'__registry':webelements})
        return wrapper         












    