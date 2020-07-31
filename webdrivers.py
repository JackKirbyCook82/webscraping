# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   Webdriver Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
from time import sleep
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import TimeoutException, WebDriverException

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebDriver(ABC):
    def __init__(self, file, *args, retry=5, wait=(5, 10), timeout=100, **kwargs): 
        options = self.getoptions(*args, **kwargs)
        proxy = self.getproxy(*args, **kwargs)
        capabilities = self.getcapabilities(*args, **kwargs)
        proxy.add_to_capabilities(capabilities)
        driversetup = dict(executable_path=file, chrome_options=options, desired_capabilities=capabilities)
        self.__driver = webdriver.Chrome(**driversetup) 
        self.__driver.set_page_load_timeout(timeout)
        self.__retry = retry
        self.__wait = wait
        
    def __call__(self, url, *args, retrys=0, **kwargs):         
        try: 
            self.__driver.get(str(url))
            yield from self.execute(*args, **kwargs)
            self.__driver.quit()
        except (TimeoutException, WebDriverException):
            self.sleep(self.__retry)
            yield from self(url, *args, retrys=retrys+1, **kwargs)
    
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
    
    def getoptions(self, *args, headless=False, images=True, **kwargs):
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















    