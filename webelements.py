# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebElement Objects
@author: Jack Kirby Cook

"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from webscraping.elements import Element, Clickable, Link, Text, Table, Input, Selection

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebClickable', 'WebButton', 'WebRadioButton', 'WebCheckBox', 'WebText', 'WebTable', 'WebInput', 'WebSelection', 'WebLink', 'WebTexts', 'WebLinks']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""

      
class WebElement(object):
    __registry = []
    def __init_subclass__(cls, *args, **kwargs): 
        if 'xpath' in kwargs.keys():
            setattr(cls, 'xpath', kwargs['xpath'])
            cls.__registry.append(cls)
        elif 'element' in kwargs.keys():
            setattr(cls, 'Element', kwargs['element'])
        else: raise ValueError('xpath', 'element')
            
    __instance = None
    def __init__(self, driver, timeout, *args, **kwargs): self.element = self.Element(self.get(driver, timeout))    
    def __getattr__(self, attr): return getattr(self.element, attr)
    def __new__(cls, *args, **kwargs):
        assert cls in cls.__registry and hasattr(cls, 'xpath')
        if cls.__instance is None: cls.__instance = super().__new__(cls) 
        return cls.__instance  
     
    def get(self, driver, timeout):        
          print("WebElement Loading: {}".format(self.__class__.__name__))
          try: element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, self.xpath)))
          except (NoSuchElementException, TimeoutException, WebDriverException): element = None        
          if element is None: print("WebElement Missing: {}".format(self.__class__.__name__))  
          return element


class WebElements(list):
    def __init_subclass__(cls, *args, **kwargs): 
        if 'xpath' in kwargs.keys():
            setattr(cls, 'xpath', kwargs['xpath'])
            cls.__registry.append(cls)
        elif 'element' in kwargs.keys():
            assert kwargs['element'] in Element.__subclasses__()
            setattr(cls, 'Element', kwargs['element'])
        else: raise ValueError('xpath', 'element')

    def __init__(self, driver, timeout, *args, **kwargs): super().__init__([self.Element(element) for element in self.get(driver, timeout)])
    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'xpath')
        return super().__new__(cls)   
        
    def get(self, driver, timeout):
        print("WebElements Loading: {}".format(self.__class__.__name__))
        try: elements = WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, self.xpath)))
        except (NoSuchElementException, TimeoutException, WebDriverException): elements = []  
        if not elements: print("WebElements Missing: {}".format(self.__class__.__name__))  
        return elements


class WebClickable(WebElement, element=Clickable): pass
class WebButton(WebElement, element=Clickable): pass
class WebRadioButton(WebElement, element=Clickable): pass
class WebCheckBox(WebElement, element=Clickable): pass
class WebText(WebElement, element=Text): pass
class WebTable(WebElement, element=Table): pass
class WebInput(WebElement, element=Input): pass
class WebSelection(WebElement, element=Selection): pass
class WebLink(WebElement, element=Link): pass
class WebTexts(WebElements, element=Text): pass
class WebLinks(WebElements, element=Link): pass

























