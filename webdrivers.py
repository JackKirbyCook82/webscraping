# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   Webdriver Objects
@author: Jack Kirby Cook

"""

from time import sleep
from abc import ABC, abstractmethod
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import TimeoutException, WebDriverException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class MaxWebDriverRetryError(Exception): pass
class EmptyWebDriverError(Exception): pass


class WebDriver(ABC):
    def __bool__(self): return self.__driver is not None
    def __repr__(self): 
        content = {'timeout':self.__timeout, 'retrys':self.__retrys, 'wait':self.__wait, **self.__options}
        string = ', '.join(['='.join([key, str(value)]) for key, value in content.items()])
        return "{}(file='{}', {})".format(self.__class__.__name__, self.__file, string)    
    
    def __init__(self, file, *args, timeout=100, retrys=3, wait=5, **kwargs): 
        self.__options = dict(headless=kwargs.get('headless', False), images=kwargs.get('images', True))
        self.__proxy = kwargs.get('proxy', None)
        self.__timeout, self.__retrys, self.__wait = timeout, retrys, wait
        self.__success = False
        self.__file = file
        self.__driver = None
        
    def __call__(self, *args, **kwargs):
        try: 
            yield from self.controller(*args, **kwargs)
            self.__success = True
        except MaxWebDriverRetryError:
            self.__success = False            
    
    @classmethod
    def create(cls, webpage):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'WebPage':webpage})
        return wrapper  
    
    def controller(self, *args, retry=0, **kwargs):
        try: yield from self.run(*args, **kwargs)    
        except (TimeoutException, WebDriverException) as error:
            self.stop(False)
            print("WebDriver Error: {}, {}|{}".format(error.__class__.__name__, str(retry), str(self.__retrys)))
            print(str(error))
            if retry < self.__retrys: 
                self.sleep()
                yield from self.controller(*args, retry=retry+1, **kwargs)
            else: raise MaxWebDriverRetryError(retry)
        
    def run(self, *args, **kwargs): 
        options, capabilities = self.setup(*args, **kwargs)
        self.start(options, capabilities)   
        page = self.WebPage(self.driver)
        page.load(*args, timeout=self.timeout, **kwargs)
        yield from self.execute(page, *args, **kwargs)
        self.stop(True)        
        
    def setup(self, *args, **kwargs):
        options = self.getoptions(*args, **self.__options, **kwargs)
        capabilities = self.getcapabilities(*args, **kwargs)
        try: 
            proxy = next(self.__proxy)
            driverproxy = self.getproxy(str(proxy), *args, **kwargs)           
            driverproxy.add_to_capabilities(capabilities)                        
        except TypeError: pass   
        return options, capabilities     

    def start(self, options, capabilities): 
        driver = Chrome(executable_path=self.__file, chrome_options=options, desired_capabilities=capabilities) 
        driver.set_page_load_timeout(self.timeout)
        self.__driver = driver 
        
    def stop(self, success):
        assert isinstance(success, bool)
        try: self.__driver.quit()
        except AttributeError: pass
        self.__driver = None
        self.__success = success
        
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
    
    @abstractmethod
    def execute(self, page, *args, **kwargs): pass
 
    @property
    def success(self): return self.__success    
    @property
    def timeout(self): return self.__timeout    
    @property
    def url(self): return self.driver.current_url
    @property
    def html(self): return self.driver.page_source   
    @property
    def driver(self):     
        if self.__driver is None: raise EmptyWebDriverError()
        else: return self.__driver

    def back(self): self.driver.back
    def forward(self): self.driver.forward
    def refresh(self): self.driver.refresh
    def sleep(self): sleep(self.__wait)


    


    







    