# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   Webpage Objects
@author: Jack Kirby Cook

"""

from time import sleep
from abc import ABC, abstractmethod
from itertools import chain
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from webscraping.webelements import WebElement, EmptyWebElementError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebPage']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebPage(ABC):        
    def __getitem__(self, key): return self.__elements[key]          
    def __init__(self, driver, *args, **kwargs): 
        self.__driver = driver 
        self.__elements = {key:webelement(driver) for key, webelement in self.WebElements.items()}
    
    def __call__(self, *args, timeout, **kwargs): 
        for key in self.executeElements: self[key].load(timeout)
        return self.execute(*args, **kwargs)
    
    def load(self, timeout): 
        for key in self.loadElements: self[key].load(timeout)

    @abstractmethod
    def execute(self, *args, **kwargs): pass        
        
    @classmethod
    def create(cls, onLoad={}, onExecute={}):
        assert isinstance(onLoad, dict) and isinstance(onExecute, dict)
        assert all([isinstance(item, WebElement) for item in chain(onLoad.values(), onExecute.values())])
        def wrapper(subclass): 
            attrs = {'loadElements':tuple(onLoad.keys()), 'executeElements':tuple(onExecute.keys()), 'WebElements':{**onLoad, **onExecute}}
            return type(subclass.__name__, (subclass, cls), attrs)
        return wrapper          
            

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    