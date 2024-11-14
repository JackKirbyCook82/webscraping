# -*- coding: utf-8 -*-
"""
Created on Sat Aug 5 2023
@name:   WebData Objects
@author: Jack Kirby Cook

"""

import json
import logging
import lxml.html
import lxml.etree
import pandas as pd
from abc import ABC, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC

from support.meta import AttributeMeta
from support.trees import MixedNode

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMT", "WebHTML", "WebJSON"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebDataErrorMeta(type):
    def __init__(cls, name, bases, attrs, *args, title=None, **kwargs):
        assert str(name).endswith("Error")
        super(WebDataErrorMeta, cls).__init__(name, bases, attrs)
        cls.__logger__ = __logger__
        cls.__title__ = title

    def __call__(cls, data):
        logger, title, name = cls.__logger__, cls.__title__, cls.__name__
        instance = super(WebDataErrorMeta, cls).__call__(name, data)
        logger.info(f"{title}: {repr(instance.data)}")
        return instance


class WebDataError(Exception, metaclass=WebDataErrorMeta):
    def __str__(self): return f"{self.name}|{repr(self.data)}"
    def __init__(self, name, data):
        self.__data = data
        self.__name = name

    @property
    def data(self): return self.__data
    @property
    def name(self): return self.__name


class WebDataMissingError(WebDataError, title="Missing"): pass
class WebDataMultipleError(WebDataError, title="Multiple"): pass


class WebDataMeta(AttributeMeta):
    def __repr__(cls): return str(cls.__name__)
    def __str__(cls): return str(cls.__key__)

    def __init__(cls, name, bases, attrs, *args, **kwargs):
        super(WebDataMeta, cls).__init__(name, bases, attrs, *args, **kwargs)
        if not any([type(base) is WebDataMeta for base in bases]):
            return
        if ABC in bases:
            existing = getattr(cls, "__parameters__", [])
            update = kwargs.get("parameters", [])
            cls.__parameters__ = list(existing) + list(update)
            return
        existing = {key: value for key, value in getattr(cls, "__subordinates__", {}).items()}
        update = {str(value): value for value in attrs.values() if type(value) is WebDataMeta}
        cls.__subordinates__ = existing | update
        cls.__parameters__ = {key: kwargs[key] for key in getattr(cls, "__parameters__")}
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))
        cls.__parser__ = kwargs.get("parser", getattr(cls, "__parser__", lambda value: value))
        cls.__key__ = kwargs.get("key", getattr(cls, "__key__", None))

    def __call__(cls, source, *args, **kwargs):
        attributes = dict(parameters=cls.__parameters__, parser=cls.__parser__, key=cls.__key__)
        elements = [element for element in cls.locate(source, *args, locator=cls.locator, **kwargs)]
        if not bool(elements) and not cls.optional:
            raise WebDataMissingError(cls)
        if len(elements) > 1 and not cls.multiple:
            raise WebDataMultipleError(cls)
        instances = [super(WebDataMeta, cls).__call__(element, **attributes) for element in elements]
        for instance in instances:
            for key, subcls in cls.subordinates.items():
                subinstances = subcls(instance.contents, *args, **kwargs)
                instance[key] = subinstances
        return (instances[0] if bool(instances) else None) if not bool(cls.multiple) else instances

    @staticmethod
    @abstractmethod
    def locate(source, *args, locator, **kwargs): pass

    @property
    def subordinates(cls): return cls.__subordinates__
    @property
    def optional(cls): return cls.__optional__
    @property
    def multiple(cls): return cls.__multiple__
    @property
    def locator(cls): return cls.__locator__


class WebData(MixedNode, ABC, metaclass=WebDataMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, contents, *args, key, parser, parameters={}, **kwargs):
        MixedNode.__init__(self, *args, **kwargs)
        self.__parameters = parameters
        self.__contents = contents
        self.__parser = parser
        self.__key = key

    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __getattr__(self, attribute):
        if attribute not in self.parameters.keys():
            raise AttributeError(attribute)
        return self.parameters[attribute]

    def execute(self, *args, **kwargs):
        return self.data

    @property
    def parameters(self): return self.__parameters
    @property
    def parser(self): return self.__parser
    @property
    def contents(self): return self.__contents
    @property
    def key(self): return self.__key

    @property
    @abstractmethod
    def string(self): pass
    @property
    @abstractmethod
    def data(self): pass


class WebELMT(WebData, ABC, attribute="Element"):
    def click(self): self.element.click()

    @property
    def html(self): return lxml.html.fromstring(self.element.get_attribute("outerHTML"))

    @property
    def string(self): return self.element.get_attribute("outerHTML")
    @property
    def data(self): return self.parser(self.element.get_attribute("outerHTML"))
    @property
    def element(self): return self.contents

    @staticmethod
    def locate(source, *args, locator, timeout=5, **kwargs):
        try:
            elements = WebDriverWait(source, timeout).until(EC.presence_of_all_elements_located((By.XPATH, locator)))
        except (NoSuchElementException, TimeoutException, WebDriverException):
            elements = []
        yield from iter(elements)


class WebELMTCaptcha(WebELMT, ABC, attribute="Captcha"):
    pass


class WebELMTInput(WebELMT, ABC, attribute="Input"):
    def fill(self, value): self.element.send_keys(value)
    def send(self): self.element.submit()
    def clear(self): self.element.clear()


class WebELMTSelect(WebELMT, ABC, attribute="Select"):
    def __init__(self, contents, *args, **kwargs):
        WebELMT.__init__(self, contents, *args, **kwargs)
        self.__select = Select(contents)

    def sel(self, key): self.select.select_by_value(key)
    def isel(self, key): self.select.select_by_index(key)
    def clear(self): self.select.deselect_all()

    @property
    def select(self): return self.__select


class WebELMTCheckBox(WebELMT, ABC, attribute="CheckBox"):
    @property
    def checked(self): return True if self.element.get_attribute("ariaChecked") in ("true", "mixed") else False


class WebHTML(WebData, ABC, attribute="Html"):
    @property
    def text(self): return self.html.attrib["text"]
    @property
    def link(self): return self.html.attrib["href"]

    @property
    def string(self): return lxml.html.tostring(self.html)
    @property
    def data(self): return self.parser(lxml.html.tostring(self.html))
    @property
    def html(self): return self.contents

    @staticmethod
    def locate(source, *args, locator, removal=None, **kwargs):
        elements = [element.remove(removal) if bool(removal) else element for element in source.xpath(locator)]
        yield from iter(elements)


class WebHTMLText(WebHTML, ABC, attribute="Text"):
    @property
    def data(self): return self.parser(str(self.text))

class WebHTMLLink(WebHTML, ABC, attribute="Link"):
    @property
    def data(self): return self.parser(str(self.link))

class WebHTMLTable(WebHTML, ABC, attribute="Table"):
    @property
    def data(self):
        table = pd.concat(pd.read_html(self.string, header=0), axis=0)
        return self.parser(table)


class WebJSON(WebData, ABC, attribute="Json"):
    @property
    def string(self): return str(json.dumps(self.json, sort_keys=True, indent=3, separators=(',', ' : '), default=str))
    @property
    def data(self): return self.parser(self.json)
    @property
    def json(self): return self.contents

    @staticmethod
    def locate(source, *args, locator, **kwargs):
        assert isinstance(source, dict) and isinstance(locator, str)
        if not bool(locator):
            yield source
            return
        locators = str(locator).strip("/").split("/")
        elements = source[str(locators.pop(0)).strip("[]")]
        for value in locators:
            elements = elements[str(value).strip("[]")]
        elements = [elements] if not isinstance(elements, (list, tuple)) else list(elements)
        yield from iter(elements)


class WebJsonText(WebJSON, ABC, attribute="Text"):
    @property
    def string(self): return str(self.json)












