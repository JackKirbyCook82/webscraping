# -*- coding: utf-8 -*-
"""
Created on Sat Aug 5 2023
@name:   WebData Objects
@author: Jack Kirby Cook

"""

import json
import lxml.html
import lxml.etree
import pandas as pd
from abc import ABC, ABCMeta, abstractmethod
from collections import namedtuple as ntuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC

from support.mixins import Node

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMT", "WebHTML", "WebJSON"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


Style = ntuple("Style", "branch terminate run blank")
aslist = lambda x: [x] if not isinstance(x, (list, tuple)) else list(x)
asdunder = lambda x: "__{}__".format(x)
double = Style("╠══", "╚══", "║  ", "   ")
single = Style("├──", "└──", "│  ", "   ")
curved = Style("├──", "╰──", "│  ", "   ")


class WebDataError(Exception): pass
class WebDataEmptyError(WebDataError): pass
class WebDataMultipleError(WebDataError): pass


class WebDataMeta(ABCMeta):
    def __repr__(cls):
        renderer = cls.hierarchy(style=cls.__style__)
        rows = [pre + "|".join(key, value.__name__) for pre, key, value in iter(renderer)]
        return "\n".format(rows)

    def __new__(mcs, name, bases, attrs, *args, **kwargs):
        cls = super(WebDataMeta, mcs).__new__(mcs, name, bases, attrs)
        if not any([type(base) is WebDataMeta for base in bases]):
            return cls
        assert type(bases[0]) is WebDataMeta
        assert all([type(base) is not WebDataMeta for base in bases[1:]])
        if ABC in bases:
            setattr(bases[0], kwargs["register"], cls)
            return cls
        children = {key: value for key, value in getattr(cls, "__children__", {}).items()}
        update = {key: value for key, value in attrs.items() if type(value) is WebDataMeta}
        children.update(update)
        setattr(cls, "__children__", children)
        return cls

    def __init__(cls, name, bases, attrs, *args, **kwargs):
        if not any([type(base) is WebDataMeta for base in bases]):
            return
        assert type(bases[0]) is WebDataMeta
        assert all([type(base) is not WebDataMeta for base in bases[1:]])
        if ABC in bases:
            return
        cls.__collection__ = kwargs.get("collection", getattr(cls, "__collection__", False))
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__parameters__ = kwargs.get("parameters", getattr(cls, "__parameters__", {}))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))
        cls.__parser__ = kwargs.get("parser", getattr(cls, "__parser__", None))
        cls.__style__ = kwargs.get("style", getattr(cls, "__style__", single))
        cls.__key__ = kwargs.get("key", getattr(cls, "__key__", None))

    def __call__(cls, source):
        locator, optional, collection = cls.__locator__, cls.__optional__, cls.__collection__
        elements = [element for element in cls.locate(source, locator=cls.__locator__)]
        if not bool(elements) and not optional:
            raise WebDataEmptyError()
        if len(elements) > 1 and not collection:
            raise WebDataMultipleError()
        attributes = {attr: getattr(cls, asdunder(attr)) for attr in ("parameters", "parser", "locator", "key", "style")}
        instances = [super(WebDataMeta, cls).__call__(element, **attributes) for element in elements]
        for instance in instances:
            for key, child in cls.__children__.items():
                subinstances = child(instance.contents)
                instance[key] = subinstances
        return (instances[0] if bool(instances) else None) if collection else instances

    def hierarchy(cls, layers=[], style=single):
        last = lambda i, x: i == x
        func = lambda i, x: "".join([pads(), pre(i, x)])
        pre = lambda i, x: style.terminate if last(i, x) else style.blank
        pads = lambda: "".join([style.blank if layer else style.run for layer in layers])
        if not layers:
            yield "", None, cls
        for index, (key, values) in enumerate(iter(cls.__children__)):
            for value in aslist(values):
                yield func(index, len(cls.__children__) - 1), key, value
                yield from value.renderer(layers=[*layers, last(index, len(cls.__children__) - 1)])


class WebData(Node, metaclass=WebDataMeta):
    def __init__(self, contents, *args, key, locator, parser, parameters, style, **kwargs):
        super().__init__(style=style)
        self.__parameters = parameters
        self.__parser = parser
        self.__contents = contents
        self.__locator = locator
        self.__key = key

    def __setitem__(self, key, value): self.set(key, value)
    def __getitem__(self, key): return self.get(key)
    def __reversed__(self): return reversed(self.items())
    def __iter__(self): return iter(self.items())

    def __call__(self, *args, **kwargs):
        data = self.data
        data = self.parser(data)
        data = self.execute(data, *args, **kwargs)
        return data

    @staticmethod
    @abstractmethod
    def locate(source, *args, locator, **kwargs): pass

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


class WebELMT(WebData, ABC, register="Element"):
    def click(self): self.element.click()

    @staticmethod
    def locate(source, *args, locator, timeout=5, **kwargs):
        try:
            elements = WebDriverWait(source, timeout).until(EC.presence_of_all_elements_located((By.XPATH, locator)))
        except (NoSuchElementException, TimeoutException, WebDriverException):
            elements = []
        yield from iter(elements)

    @property
    def html(self): return lxml.html.fromstring(self.element.get_attribute("outerHTML"))

    @property
    def string(self): return self.element.get_attribute("outerHTML")
    @property
    def data(self): return self.element.get_attribute("outerHTML")
    @property
    def element(self): return self.contents


class WebELMTCaptcha(WebELMT, ABC, register="Captcha"):
    pass


class WebELMTInput(WebELMT, ABC, register="Input"):
    def fill(self, value): self.element.send_keys(value)
    def send(self): self.element.submit()
    def clear(self): self.element.clear()


class WebELMTSelect(WebELMT, ABC, register="Select"):
    def __init__(self, contents, *args, **kwargs):
        super().__init__(contents, *args, **kwargs)
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
    @staticmethod
    def locate(source, *args, locator, removal=None, **kwargs):
        elements = [element.remove(removal) if bool(removal) else element for element in source.xpath(locator)]
        yield from iter(elements)

    @property
    def text(self): return self.html.attrib["text"]
    @property
    def link(self): return self.html.attrib["href"]

    @property
    def string(self): return lxml.html.tostring(self.html)
    @property
    def data(self): return lxml.html.tostring(self.html)
    @property
    def html(self): return self.contents


class WebHTMLText(WebHTML, ABC, register="Text"):
    @property
    def data(self): return str(self.text)


class WebHTMLLink(WebHTML, ABC, register="Link"):
    @property
    def data(self): return str(self.link)


class WebHTMLTable(WebHTML, ABC, register="Table"):
    @property
    def data(self):
        header = self.parameters.get("header", 0)
        index = self.parameters.get("index", None)
        return pd.concat(pd.read_html(self.string, header=header, index_col=index), axis=0)


class WebJSON(WebData, ABC, register="Json"):
    @classmethod
    def locate(cls, source, *args, locator, **kwargs):
        assert isinstance(source, (list, dict)) and isinstance(locator, (list, str))
        locators = str(locator).strip("/").split("/") if isinstance(locator, str) else locator
        locator = locators.pop(0)
        locator, collection = str(locator).strip("[]"), str(locator).endswith("[]")
        elements = source[str(locator)] if isinstance(source, dict) else source[int(locator)]
        elements = [elements] if not bool(collection) else aslist(elements)
        for element in iter(elements):
            if bool(locators):
                yield from cls.locate(element, *args, locator=locators, **kwargs)
            else:
                yield element

    @property
    def string(self): return str(json.dumps(self.json, sort_keys=True, indent=3, separators=(',', ' : '), default=str))
    @property
    def data(self): return self.json
    @property
    def json(self): return self.contents


class WebJsonText(WebJSON, ABC, register="Text"):
    @property
    def string(self): return str(self.json)



