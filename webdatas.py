# -*- coding: utf-8 -*-
"""
Created on Sat Jan 4 2025
@name:   WebSourcing Objects
@author: Jack Kirby Cook

"""

import json
import types
import logging
import lxml.html
import pandas as pd
from abc import ABC, ABCMeta, abstractmethod
from collections import OrderedDict as ODict
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from support.meta import AttributeMeta, TreeMeta
from support.trees import ParentalNode

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2024, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebDataErrorMeta(type):
    def __init__(cls, name, bases, attrs, *args, title=None, **kwargs):
        assert str(name).endswith("Error")
        super(WebDataErrorMeta, cls).__init__(name, bases, attrs)
        cls.__logger__ = __logger__
        cls.__title__ = title

    def __call__(cls, data):
        instance = super(WebDataErrorMeta, cls).__call__(data)
        cls.logger.info(f"{cls.title}: {repr(data)}")
        return instance

    @property
    def logger(cls): return cls.__logger__
    @property
    def title(cls): return cls.__title__
    @property
    def name(cls): return cls.__name__


class WebDataError(Exception, metaclass=WebDataErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return f"{type(self).name}|{repr(self.data)}"
    def __init__(self, data): self.__data = data

    @property
    def data(self): return self.__data

class WebDataMissingError(WebDataError, title="Missing"): pass
class WebDataMultipleError(WebDataError, title="Multiple"): pass


class WebDataMeta(AttributeMeta, TreeMeta, ABCMeta):
    def __init__(cls, *args, **kwargs):
        function = lambda key, locator, dependent: type(f"{repr(dependent)}{str(key).title()}", tuple([dependent]), {}, locator=locator)
        dependents = {key: function(key, locator, cls.dependents[key]) for key, locator in kwargs.get("locators", {}).items()}
        super(WebDataMeta, cls).__init__(*args, dependents=dependents, **kwargs)
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))

    def __call__(cls, source, *args, **kwargs):
        assert not isinstance(cls.locator, types.NoneType)
        sources = [source for source in cls.locate(source, *args, **kwargs)]
        if not bool(sources) and not cls.optional: raise WebDataMissingError(cls)
        if len(sources) > 1 and not cls.multiple: raise WebDataMultipleError(cls)
        instances = [super(WebDataMeta, cls).__call__(value, *args, **kwargs) for value in sources]
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


class WebData(ParentalNode, ABC, metaclass=WebDataMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, source, *arguments, **parameters):
        super().__init__(*arguments, **parameters)
        self.__parameters = parameters
        self.__arguments = arguments
        self.__source = source

    def __str__(self): return self.string
    def __getitem__(self, key):
        dependent = type(self).dependents[key]
        child = dependent(self.source, *self.arguments, **self.parameters)
        self[key] = child
        return child

    @property
    @abstractmethod
    def string(self): pass

    @property
    def parameters(self): return self.__parameters
    @property
    def arguments(self): return self.__arguments
    @property
    def source(self): return self.__source


class WebHTMLData(WebData):
    @classmethod
    def locate(cls, source, *args, **kwargs):
        contents = list(source.xpath(cls.locator))
        yield from iter(contents)

    @property
    def string(self): return lxml.html.tostring(self.html)
    @property
    def html(self): return self.source

class WebJSONData(WebData):
    @classmethod
    def locate(cls, source, *args, **kwargs):
        locators = str(cls.locator).lstrip("//").rstrip("[]").split("/")
        contents = source[str(locators.pop(0))]
        for locator in locators: contents = contents[str(locator)]
        if isinstance(contents, (tuple, list)): yield from iter(contents)
        elif isinstance(contents, (str, int, float)): yield contents
        elif isinstance(contents, dict): yield contents
        else: raise TypeError(type(contents))

    @property
    def string(self): return json.dumps(self.json, sort_keys=True, indent=3, separators=(',', ' : '), default=str)
    @property
    def json(self): return self.source

class WebELMTData(WebData):
    @classmethod
    def locate(cls, source, *args, timeout, **kwargs):
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
    def string(self): return self.element.get_attribute("outerHTML")
    @property
    def html(self): return lxml.html.fromstring(self.string)
    @property
    def element(self): return self.source


class WebParsing(ParentalNode, ABC):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.parser = kwargs.get("parser", getattr(cls, "parser", lambda content: content))

    def __call__(self, *args, **kwargs):
        data = self.execute(*args, **kwargs)
        return self.parser(data)

    @abstractmethod
    def execute(self, *args, **kwargs): pass

class WebMapping(WebParsing):
    def execute(self, *args, **kwargs): return {key: value(*args, **kwargs) for key, value in iter(self)}

class WebContent(WebParsing):
    def execute(self, *args, **kwargs): return self.content

    @property
    @abstractmethod
    def content(self): pass


class WebHTML(WebMapping, WebHTMLData, ABC, root=True): pass
class WebJSON(WebMapping, WebJSONData, ABC, root=True): pass
class WebELMT(WebMapping, WebELMTData, ABC, root=True): pass


class WebHTMLText(WebContent, WebHTML, ABC, attribute="Text"):
    @property
    def text(self): return str(self.html.attrib["text"])
    @property
    def content(self): return self.text

class WebHTMLLink(WebContent, WebHTML, ABC, attribute="Link"):
    @property
    def link(self): return str(self.html.attrib["href"])
    @property
    def content(self): return self.link

class WebHTMLTable(WebContent, WebHTML, ABC, attribute="Table"):
    @property
    def table(self): return pd.concat(pd.read_html(self.string, header=0, index_col=None), axis=0)
    @property
    def content(self): return self.table


class WebJsonCollection(WebContent, WebJSON, ABC, attribute="Collection"):
    @property
    def collection(self): return list(self.json)
    @property
    def content(self): return self.collection

class WebJsonMapping(WebContent, WebJSON, ABC, attribute="Mapping"):
    @property
    def mapping(self): return dict(self.json)
    @property
    def content(self): return self.mapping

class WebJsonText(WebContent, WebJSON, ABC, attribute="Text"):
    @property
    def text(self): return str(self.json)
    @property
    def content(self): return self.text


class WebELMTText(WebContent, WebELMT, ABC, attribute="Text"):
    @property
    def text(self): return self.element.get_attribute("text")
    @property
    def content(self): return self.content

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


