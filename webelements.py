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

from webscraping.elements import Clickable, Link, Text, Table, Input, Selection

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebClickable', 'WebButton', 'WebRadioButton', 'WebCheckBox', 'WebText', 'WebTable', 'WebInput', 'WebSelection', 'WebLink', 'WebClickables', 'WebLinks']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


WEBELEMENT_REGISTRY = {}
WEBELEMENTS_REGISTRY = {}
      
_aslist = lambda items: [items] if not isinstance(items, (tuple, list)) else list(items)


def getelement(driver, timeout, xpath):
    try: element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): element = None        
    return element    

def getelements(driver, timeout, xpath): 
    try: elements = WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
    except (NoSuchElementException, TimeoutException, WebDriverException): elements = []  
    return elements
    

class WebElement(object):
    @classmethod
    def addchild(cls, key, child):
        assert key is not None
        cls.Children[key] = child
        
    def __init_subclass__(cls, *args, xpath=None, element=None, parent=None, key=None, **attrs):
        if element is not None: setattr(cls, 'Element', element)
        if xpath is not None: setattr(cls, 'xpath', xpath)
        cls.Element.update(**attrs)
        if hasattr(cls, 'xpath') and hasattr(cls, 'Element'): 
            setattr(cls, 'Children', {})
            if parent is None: WEBELEMENT_REGISTRY[cls.__name__] = cls
            else: WEBELEMENT_REGISTRY[parent.__name__].addchild(key, cls)
           
    __instance = None
    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'xpath') and hasattr(cls, 'Element')
        assert cls.__name__ in WEBELEMENT_REGISTRY.keys() and cls in WEBELEMENT_REGISTRY.values()
        if cls.__instance is None: cls.__instance = super().__new__(cls) 
        return cls.__instance  
    
    def __init__(self, driver, timeout, *args, **kwargs):
        if getattr(self, 'initialized', False): return
        self.__element = self.Element(self.get(driver, timeout))
        self.__children = {key:child(self.element, timeout, *args, **kwargs) for key, child in self.Children.items()}
        self.initialized = True

    @property
    def element(self): return self.__element
    @property
    def children(self): return self.__children
    
    def __bool__(self): return bool(self.__element)
    def __str__(self): return "{}|{}".format(self.__class__.__name__, str(bool(self.__element)))      
    def __getattr__(self, attr): return getattr(self.element, attr)   
    def __getitem__(self, key): return self.__children[key] 
       
    def get(self, driver, timeout):
        print("WebElement Loading: {}".format(self.__class__.__name__))    
        element = getelement(driver, timeout, self.xpath)
        if element is None: print("WebElement Missing: {}".format(self.__class__.__name__))         
        return element
    

class WebElements(object):    
    @classmethod
    def addchild(cls, key, child):
        assert key is not None
        cls.Children[key] = child
    
    def __init_subclass__(cls, *args, xpath=None, element=None, parent=None, key=None, **attrs):
        if element is not None: setattr(cls, 'Element', element)
        if xpath is not None: setattr(cls, 'xpath', xpath)
        cls.Element.update(**attrs)
        if hasattr(cls, 'xpath') and hasattr(cls, 'Element'): 
            setattr(cls, 'Children', {})
            if parent is None: WEBELEMENTS_REGISTRY[cls.__name__] = cls
            else: WEBELEMENTS_REGISTRY[parent.__name__].addchild(key, cls)

    def __new__(cls, *args, **kwargs):
        assert hasattr(cls, 'xpath') and hasattr(cls, 'Element') 
        assert cls.__name__ in WEBELEMENTS_REGISTRY.keys() and cls in WEBELEMENTS_REGISTRY.values()
        return super().__new__(cls)   

    def __init__(self, driver, timeout, *args, **kwargs):
        self.__elements = [self.Element(element) for element in self.get(driver, timeout)]
        self.__childrens = [{} for element in self.__elements]
        for index, webelement in enumerate(self.__elements):
            self.__children[index]
            self.__children[index].update({key:child(webelement, timeout, *args, **kwargs) for key, child in self.Children.items()})

    @property
    def elements(self): return self.__elements
    @property
    def childrens(self): return self.__children

    def __bool__(self): return all([bool(element) for element in self.__elements])
    def __str__(self): return "{}|({})".format(self.__class__.__name__, ', '.join([str(bool(element)) for element in self.__elements]))  
    def __getitem__(self, locator): 
        if isinstance(locator, int): return self.__elements[locator]
        elif isinstance(locator, tuple): 
            assert len(locator) == 2 and isinstance(locator[0], int) and isinstance(locator[1], str)
            return self.__children[locator[0]][locator[1]]
        else: raise TypeError(type(locator).__name__)
        
    def get(self, driver, timeout):
        print("WebElements Loading: {}".format(self.__class__.__name__))
        elements = getelements(driver, timeout, self.xpath)
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

class WebClickables(WebElements, element=Clickable): pass
class WebLinks(WebElements, element=Link): pass



















