# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebData Objects
@author: Jack Kirby Cook

"""

import json
import types
import lxml.html
import lxml.etree
import pandas as pd
from numbers import Number
from abc import ABC, ABCMeta, abstractmethod
from collections import OrderedDict as ODict
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from support.meta import AttributeMeta, TreeMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMT", "WebJSON", "WebHTML"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebDataErrorMeta(type):
    def __init__(cls, *args, **kwargs):
        super(WebDataErrorMeta, cls).__init__(*args, **kwargs)
        cls.__title__ = kwargs.get("title", getattr(cls, "__title__", None))

    @property
    def title(cls): return cls.__title__
    @property
    def name(cls): return cls.__name__

class WebDataError(Exception, metaclass=WebDataErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass

class WebDataMissingError(WebDataError, title="Missing"): pass
class WebDataMultipleError(WebDataError, title="Multiple"): pass


class WebDataMeta(AttributeMeta, TreeMeta, ABCMeta):
    def __init__(cls, *args, dependents=[], **kwargs):
        function = lambda name, base, locator: type(repr(cls) + str(name).title(), tuple([base]), dict(), locator=locator)
        modified = [function(key, cls.dependents[key], locator) for key, locator in kwargs.get("locators", {}).items()]
        dependents = list(dependents) + list(modified)
        super(WebDataMeta, cls).__init__(*args, dependents=dependents, **kwargs)
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))

    def __call__(cls, source, *args, **kwargs):
        assert not isinstance(cls.locator, types.NoneType)
        sources = list(cls.locate(source, *args, **kwargs))
        if not bool(sources) and not cls.optional: raise WebDataMissingError()
        if len(sources) > 1 and not cls.multiple: raise WebDataMultipleError()
        attributes = dict(children=cls.dependents)
        initialize = lambda value: super(WebDataMeta, cls).__call__(value, *args, **attributes, **kwargs)
        instances = list(map(initialize, sources))
        if bool(cls.multiple): return list(instances)
        else: return instances[0] if bool(instances) else None

    @abstractmethod
    def locate(cls, source, *args, **kwargs): pass

    @property
    def optional(cls): return cls.__optional__
    @property
    def multiple(cls): return cls.__multiple__
    @property
    def locator(cls): return cls.__locator__


class WebData(ABC, metaclass=WebDataMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, source, *arguments, children, **parameters):
        self.__parameters = parameters
        self.__arguments = arguments
        self.__children = children
        self.__source = source

    def __str__(self): return self.string
    def __iter__(self):
        for key, child in self.children.items():
            instance = child(self.source, *self.arguments, **self.parameters)
            yield key, instance

    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __getitem__(self, key):
        child = self.children[key]
        instance = child(self.source, *self.arguments, **self.parameters)
        return instance

    @property
    @abstractmethod
    def string(self): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass

    @property
    def parameters(self): return self.__parameters
    @property
    def arguments(self): return self.__arguments
    @property
    def children(self): return self.__children
    @property
    def source(self): return self.__source


class WebHTMLData(WebData, ABC):
    @classmethod
    def locate(cls, source, *args, **kwargs):
        if isinstance(source, WebDriver): source = lxml.html.fromstring(source.page_source)
        elif isinstance(source, WebElement): source = lxml.html.fromstring(source.get_attribute("innerHTML"))
        contents = list(source.xpath(cls.locator))
        yield from iter(contents)

    @property
    def string(self): return lxml.html.tostring(self.html)
    @property
    def html(self): return self.source

class WebJSONData(WebData, ABC):
    @classmethod
    def locate(cls, source, *args, **kwargs):
        assert isinstance(source, (dict, list, str, Number))
        locators = str(cls.locator).lstrip("//").rstrip("[]").split("/")
        contents = source[str(locators.pop(0))]
        for locator in locators: contents = contents[str(locator)]
        if isinstance(contents, (tuple, list)): yield from iter(contents)
        elif isinstance(contents, (str, Number)): yield contents
        elif isinstance(contents, dict): yield contents
        else: raise TypeError(type(contents))

    @property
    def string(self): return json.dumps(self.json, sort_keys=True, indent=3, separators=(',', ' : '), default=str)
    @property
    def json(self): return self.source

class WebELMTData(WebData, ABC):
    @classmethod
    def locate(cls, source, *args, timeout, **kwargs):
        assert isinstance(source, (WebElement, WebDriver))
        locator = tuple([By.XPATH, cls.locator])
        located = EC.presence_of_all_elements_located(locator)
        try: contents = WebDriverWait(source, timeout).until(located)
        except (NoSuchElementException, TimeoutException, WebDriverException): contents = []
        yield from iter(contents)

    @property
    def stale(self):
        try: self.element.is_displayed()
        except StaleElementReferenceException: return True
        else: return False

    @property
    def string(self): return self.element.get_attribute("innerHTML")
    @property
    def html(self): return lxml.html.fromstring(self.string)
    @property
    def element(self): return self.source


class WebParent(WebData, ABC):
    def execute(self, *args, **kwargs): return {key: value(*args, **kwargs) for key, value in iter(self)}

class WebChild(WebData, ABC):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.__parser__ = kwargs.get("parser", getattr(cls, "__parser__", lambda content: content))

    def execute(self, *args, **kwargs): return self.parse(self.content, *args, **kwargs)
    def parse(self, content, *args, **kwargs): return self.parser(content)

    @property
    @abstractmethod
    def content(self): pass
    @property
    def parser(self): return type(self).__parser__


class WebHTML(WebParent, WebHTMLData, ABC, root=True): pass
class WebJSON(WebParent, WebJSONData, ABC, root=True): pass
class WebELMT(WebParent, WebELMTData, ABC, root=True): pass


class WebHTMLText(WebChild, WebHTML, ABC, attribute="Text"):
    @property
    def text(self): return str(self.html.text)
    @property
    def content(self): return self.text

class WebHTMLLink(WebChild, WebHTML, ABC, attribute="Link"):
    @property
    def link(self): return str(self.html.href)
    @property
    def content(self): return self.link

class WebHTMLTable(WebChild, WebHTML, ABC, attribute="Table"):
    @property
    def table(self): return pd.concat(pd.read_html(self.string, header=0, index_col=None), axis=0)
    @property
    def content(self): return self.table


class WebJsonCollection(WebChild, WebJSON, ABC, attribute="Collection"):
    @property
    def collection(self): return list(self.json)
    @property
    def content(self): return self.collection

class WebJsonMapping(WebChild, WebJSON, ABC, attribute="Mapping"):
    @property
    def mapping(self): return dict(self.json)
    @property
    def content(self): return self.mapping

class WebJsonText(WebChild, WebJSON, ABC, attribute="Text"):
    @property
    def text(self): return str(self.json)
    @property
    def content(self): return self.text


class WebELMTText(WebChild, WebELMT, ABC, attribute="Text"):
    @property
    def text(self): return self.element.get_attribute("text")
    @property
    def content(self): return self.text

class WebELMTLink(WebChild, WebELMT, ABC, attribute="Link"):
    @property
    def link(self): return self.element.get_attribute("href")
    @property
    def content(self): return self.link

class WebELMTClickable(WebELMTText, ABC, attribute="Clickable"):
    def click(self): self.element.click()


class WebELMTButton(WebELMTClickable, ABC, attribute="Button"): pass
class WebELMTInput(WebELMTClickable, ABC, attribute="Input"):
    def fill(self, value): self.element.send_keys(str(value))
    def send(self): self.element.submit()
    def clear(self): self.element.clear()

class WebELMTToggle(WebELMTClickable, ABC, attribute="Toggle"):
    def select(self, value):
        if not str(self.content) != str(value): self.element.click()
        assert str(self.content) == str(value)


class WebELMTMenu(WebELMTClickable, key="menu", locator=None, multiple=True, optional=False): pass
class WebELMTDropdown(WebELMTClickable, ABC, attribute="Dropdown", dependents=[WebELMTMenu]):
    def select(self, value):
        self.click()
        self.menu[str(value)].click()

    @property
    def menu(self):
        function = lambda instance: instance(*self.arguments, **self.parameters)
        keys, values = list(map(function, self["menu"])), list(self["menu"])
        return ODict(list(zip(keys, values)))


