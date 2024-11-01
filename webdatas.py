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
from abc import ABC, ABCMeta, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC

from support.mixins import MultipleNode
from support.meta import RegistryMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMT", "WebHTML", "WebJSON"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebDataErrorMeta(RegistryMeta):
    def __init__(cls, name, bases, attrs, *args, **kwargs):
        assert str(name).endswith("Error")
        super(WebDataErrorMeta, cls).__init__(name, bases, attrs, *args, **kwargs)

    def __call__(cls, *args, **kwargs):
        instance = super(WebDataErrorMeta, cls).__call__(*args, **kwargs)
        __logger__.info(str(instance.name).replace("Error", f": {repr(instance.data)}"))
        return instance


class WebDataError(Exception, metaclass=WebDataErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return f"{self.name}|{repr(self.data)}"
    def __init__(self, data):
        self.__name = self.__class__.__name__
        self.__data = data

    @property
    def data(self): return self.__data
    @property
    def name(self): return self.__name


class WebDataEmptyError(WebDataError): pass
class WebDataMultipleError(WebDataError): pass


class WebDataMeta(ABCMeta):
    def __repr__(cls): return str(cls.__name__)
    def __init__(cls, name, bases, attrs, *args, **kwargs):
        assert all([attr not in attrs.keys() for attr in ("children", "collection", "optional", "style")])
        if not any([type(base) is WebDataMeta for base in bases]):
            return
        assert type(bases[0]) is WebDataMeta
        assert all([type(base) is not WebDataMeta for base in bases[1:]])
        if ABC in bases:
            setattr(bases[0], kwargs["register"], cls)
            return
        children = {key: value for key, value in getattr(cls, "__children__", {}).items()}
        update = {value.__key__: value for value in attrs.values() if type(value) is WebDataMeta}
        children.update(update)
        cls.__children__ = children | update
        cls.__collection__ = kwargs.get("collection", getattr(cls, "__collection__", False))
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__parameters__ = kwargs.get("parameters", getattr(cls, "__parameters__", {}))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))
        cls.__parser__ = kwargs.get("parser", getattr(cls, "__parser__", lambda x: x))
        cls.__key__ = kwargs.get("key", getattr(cls, "__key__", None))

    def __call__(cls, source):
        attributes = {attr: getattr(cls, f"__{attr}__") for attr in ("locator", "key", "parameters", "parser")}
        locator, optional, collection = cls.__locator__, cls.__optional__, cls.__collection__
        elements = [element for element in cls.locate(source, locator=cls.__locator__)]
        if not bool(elements) and not optional:
            raise WebDataEmptyError(cls)
        if len(elements) > 1 and not collection:
            raise WebDataMultipleError(cls)
        instances = [super(WebDataMeta, cls).__call__(element, **attributes) for element in elements]
        for instance in instances:
            for key, subcls in cls.__children__.items():
                subinstances = subcls(instance.contents)
                instance[key] = subinstances
        return (instances[0] if bool(instances) else None) if not bool(collection) else instances


class WebData(MultipleNode, metaclass=WebDataMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, contents, *args, key, locator, parser, parameters, **kwargs):
        MultipleNode.__init__(self)
        self.__parameters = parameters
        self.__parser = parser
        self.__contents = contents
        self.__locator = locator
        self.__key = key

    def __contains__(self, key): return bool(key in self.nodes.keys())
    def __setitem__(self, key, value): self.set(key, value)
    def __getitem__(self, key): return self.get(key)

    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __reversed__(self): return reversed(self.items())
    def __iter__(self): return iter(self.items())

    def execute(self, *args, **kwargs):
        return self.data

    @property
    @abstractmethod
    def string(self): pass
    @property
    @abstractmethod
    def data(self): pass

    @property
    def parameters(self): return self.__parameters
    @property
    def parser(self): return self.__parser
    @property
    def contents(self): return self.__contents
    @property
    def locator(self): return self.__locator
    @property
    def key(self): return self.__key

    @staticmethod
    @abstractmethod
    def locate(source, *args, locator, **kwargs): pass


class WebELMT(WebData, ABC, register="Element"):
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


class WebELMTCaptcha(WebELMT, ABC, register="Captcha"):
    pass


class WebELMTInput(WebELMT, ABC, register="Input"):
    def fill(self, value): self.element.send_keys(value)
    def send(self): self.element.submit()
    def clear(self): self.element.clear()


class WebELMTSelect(WebELMT, ABC, register="Select"):
    def __init__(self, contents, *args, **kwargs):
        WebELMT.__init__(self, contents, *args, **kwargs)
        self.__select = Select(contents)

    def sel(self, key): self.select.select_by_value(key)
    def isel(self, key): self.select.select_by_index(key)
    def clear(self): self.select.deselect_all()

    @property
    def select(self): return self.__select


class WebELMTCheckBox(WebELMT, ABC, register="CheckBox"):
    @property
    def checked(self): return True if self.element.get_attribute("ariaChecked") in ("true", "mixed") else False


class WebHTML(WebData, ABC, register="Html"):
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


class WebHTMLText(WebHTML, ABC, register="Text"):
    @property
    def data(self): return self.parser(str(self.text))

class WebHTMLLink(WebHTML, ABC, register="Link"):
    @property
    def data(self): return self.parser(str(self.link))

class WebHTMLTable(WebHTML, ABC, register="Table"):
    @property
    def data(self):
        header = self.parameters.get("header", 0)
        index = self.parameters.get("index", None)
        table = pd.concat(pd.read_html(self.string, header=header, index_col=index), axis=0)
        return self.parser(table)


class WebJSON(WebData, ABC, register="Json"):
    @property
    def string(self): return str(json.dumps(self.json, sort_keys=True, indent=3, separators=(',', ' : '), default=str))
    @property
    def data(self): return self.parser(self.json)
    @property
    def json(self): return self.contents

    @classmethod
    def locate(cls, source, *args, locator, **kwargs):
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


class WebJsonText(WebJSON, ABC, register="Text"):
    @property
    def string(self): return str(self.json)



