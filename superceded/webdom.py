# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDOM Objects
@author: Jack Kirby Cook

"""

import json
import lxml.html
import pandas as pd
from abc import ABC, abstractmethod
from functools import update_wrapper
from lxml.html import HtmlElement as StaticElement
from selenium.webdriver.support.ui import Select as SelectElement
from selenium.webdriver.remote.webelement import WebElement as DynamicElement

from utilities.meta import RegistryMeta, VariantMeta
from utilities.dispatchers import typedispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebDOMs"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebDOMParserError(Exception, metaclass=RegistryMeta):
    def __str__(self): return "{}|{}|{}[{}]".format(self.__class__.__name__, repr(self.dom), self.error.__class__.__name__, str(self.data).strip())
    def __init__(self, dom, error, data):
        self.__dom = dom
        self.__error = error
        self.__data = data

    @property
    def dom(self): return self.__dom
    @property
    def error(self): return self.__error
    @property
    def data(self): return self.__data


class WebDOMKeyParserError(WebDOMParserError, key="key"): pass
class WebDOMLinkParserError(WebDOMParserError, key="link"): pass
class WebDOMDataParserError(WebDOMParserError, key="data"): pass
class WebDOMTableParserError(WebDOMParserError, key="table"): pass


def parser(cls, key, function):
    exception = WebDOMParserError[key]

    def wrapper(data, *args, **kwargs):
        try:
            return function(data, *args, **kwargs)
        except Exception as error:
            raise exception(cls, error, data)
    update_wrapper(wrapper, function)
    return wrapper

def key_parser(x, *args, **kwargs): return str(x)
def value_parser(x, *args, **kwargs): return x
def link_parser(x, *args, **kwargs): return None if not bool(x) else x

def data_parser(x, *args, method="records", **kwargs):
    assert method == "records" or method == "list"
    if isinstance(x, pd.DataFrame):
        return x.to_dict(method)
    elif isinstance(x, pd.Series):
        return x.to_frame().to_dict(method)
    else:
        return x

def table_parser(x, *args, **kwargs):
    assert isinstance(x, (pd.DataFrame, pd.Series))
    return x.to_frame() if isinstance(x, pd.Series) else x


class WebDOMMeta(VariantMeta):
    def __repr__(cls): return cls.name
    def __init__(cls, *args, **kwargs):
        parameters = {key: value for key, value in getattr(cls, "__parameters__", {}).items()}
        parameters.update({key: staticmethod(value) if callable(value) else value for key, value in kwargs.get("parameters", {}).items()})
        parsers = {key: value for key, value in getattr(cls, "__parsers__", {}).items()}
        parsers.update({key: parser(cls, key, value) for key, value in kwargs.get("parsers", {}).items()})
        cls.__parameters__ = parameters
        cls.__parsers__ = parsers

    def __call__(cls, dom, *args, **kwargs):
        parameters = dict(parsers=cls.__parsers__, parameters=cls.__parameters__)
        instance = super(WebDOMMeta, cls).__call__(dom, *args, variant=type(dom), **parameters, **kwargs)
        return instance

    def create(cls, name, base, *args, **kwargs):
        return type(cls)(name, (cls, base), {}, *args, **kwargs)

    def update(cls, name, *args, **kwargs):
        return type(cls)(name, (cls,), {}, *args, **kwargs)

    @property
    def name(cls): return cls.__name__


class WebDOMBase(ABC, metaclass=WebDOMMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __repr__(self): return "{}|{}".format(self.name, self.type)
    def __str__(self): return str(self.text)

    def __getattr__(self, attr):
        try:
            return self.parameters[attr]
        except KeyError:
            raise AttributeError(attr)

    def __init__(self, dom, *args, parsers={}, parameters={}, **kwargs):
        self.__parameters = parameters
        self.__parsers = parsers
        self.__dom = dom

    @property
    @abstractmethod
    def text(self): pass

    @property
    def type(self): return type(self.dom).__name__
    @property
    def name(self): return self.__class__.__name__

    @property
    def parameters(self): return self.__parameters
    @property
    def parsers(self): return self.__parsers

    @property
    def DOM(self): return self.__dom
    @property
    def dom(self): return self.__dom


class WebJsonDOMBase(WebDOMBase, variants=[list, dict]):
    @property
    def text(self): return json.dumps(self.dom, sort_keys=True, indent=3, separators=(',', ' : '), default=str)
    @property
    def json(self): return self.dom


class WebValueDOMBase(WebDOMBase, variants=[str, int, float]):
    @property
    def text(self): return str(self.dom)
    @property
    def value(self): return self.dom


class WebHtmlDOMBase(WebDOMBase):
    @abstractmethod
    def table(self, *args, header=None, index=None, **kwargs): pass

    @property
    @abstractmethod
    def html(self): pass
    @property
    @abstractmethod
    def text(self): pass
    @property
    @abstractmethod
    def href(self): pass


class WebStaticDOMBase(WebHtmlDOMBase, variant=StaticElement):
    def table(self, *args, header=None, index=None, **kwargs):
        return pd.concat(pd.read_html(self.text, header=header, index_col=index), axis=0)

    @property
    def html(self): return self.dom
    @property
    def text(self): return lxml.html.tostring(self.dom)
    @property
    def href(self): return self.dom.attrib["href"]


class WebDynamicDOMBase(WebHtmlDOMBase, variant=DynamicElement):
    def click(self): self.dom.click()
    def table(self, *args, header=None, index=None, **kwargs):
        return pd.concat(pd.read_html(self.text, header=header, index_col=index), axis=0)

    @property
    def html(self): return lxml.html.fromstring(self.dom.get_attribute("outerHTML"))
    @property
    def text(self): return self.dom.get_attribute("outerHTML")
    @property
    def href(self): return self.dom.get_attribute("href")

    @property
    def location(self): return self.dom.location
    @property
    def size(self): return self.dom.size
    @property
    def width(self): return self.size["width"]
    @property
    def height(self): return self.size["height"]
    @property
    def x(self): return self.location["x"]
    @property
    def y(self): return self.location["y"]

    @property
    def enabled(self): return self.dom.is_enabled()
    @property
    def visible(self): return self.dom.is_displayed()
    @property
    def selected(self): return self.dom.is_selected()


class WebHtmlDOM(WebHtmlDOMBase, ABC): pass
class WebJsonDOM(WebJsonDOMBase, ABC, parsers={"data": data_parser, "key": key_parser}):
    def data(self, *args, **kwargs): return self.parsers["data"](self.json, *args, **kwargs)
    def key(self, *args, **kwargs): return self.parsers["key"](self.json, *args, **kwargs)


class WebBadRequestDOM(WebHtmlDOMBase, ABC): pass
class WebServerFailureDOM(WebDynamicDOMBase): pass
class WebCaptchaDOM(WebDynamicDOMBase): pass


class WebInputDOM(WebDynamicDOMBase):
    @property
    def value(self): return str(self.dom.get_attribute("value"))

    def fill(self, text): self.dom.send_keys(str(text))
    def clear(self): self.dom.clear()
    def send(self): self.dom.submit()


class WebSelectDOM(WebDynamicDOMBase, parsers={"key": key_parser, "data": value_parser}):
    def __init__(self, dom):
        self.__select = SelectElement(dom)
        super().__init__(dom)

    @property
    def select(self): return self.__select
    @property
    def options(self): return self.__select.options
    @property
    def size(self): return len(list(self.options))

    def clear(self): self.select.deselect_all()
    def keys(self): return tuple([option.get_attribute("value") for option in self.options])
    def values(self): return tuple([option.text for option in self.options])
    def items(self): return tuple([(key, value) for key, value in zip(self.keys(), self.values())])

    def data(self, *args, **kwargs):
        return tuple([(self.parsers["key"](key, *args, **kwargs), self.parsers["data"](value, *args, **kwargs)) for key, value in self.items()])

    @typedispatcher
    def sel(self, key): raise TypeError(type(key).__name__)
    @sel.register(int)
    def isel(self, key): self.select.select_by_index(key)
    @sel.register(str)
    def tsel(self, key): self.select.select_by_value(key)


class WebCheckableDOM(WebDynamicDOMBase):
    @property
    def checked(self): return True if self.dom.get_attribute("ariaChecked") in ("true", "mixed") else False


class WebClickableDOM(WebDynamicDOMBase, parsers={"link": link_parser, "data": data_parser, "key": key_parser}):
    @property
    def expanded(self): return True if str(self.dom.get_attribute("ariaExpanded")) == "true" else False

    def link(self, *args, **kwargs): return self.parsers["link"](self.href, *args, **kwargs)
    def data(self, *args, **kwargs): return self.parsers["data"](self.text, *args, **kwargs)
    def key(self, *args, **kwargs): return self.parsers["key"](self.text, *args, **kwargs)


class WebLinkDOM(WebHtmlDOMBase, ABC, parsers={"link": link_parser, "data": data_parser, "key": key_parser}):
    def link(self, *args, **kwargs): return self.parsers["link"](self.href, *args, **kwargs)
    def data(self, *args, **kwargs): return self.parsers["data"](self.href, *args, **kwargs)
    def key(self, *args, **kwargs): return self.parsers["key"](self.href, *args, **kwargs)


class WebTextDOM(WebDOMBase, ABC, parsers={"data": data_parser, "key": key_parser}):
    def __float__(self): return float(self.data())
    def __bool__(self): return bool(self.data())
    def __int__(self): return int(self.data())
    def __str__(self): return str(self.data())

    def data(self, *args, **kwargs): return self.parsers["data"](self.text, *args, **kwargs)
    def key(self, *args, **kwargs): return self.parsers["key"](self.text, *args, **kwargs)


class WebTableDOM(WebHtmlDOMBase, ABC, parameters={"header": 0, "index": None}, parsers={"table": table_parser}):
    @property
    def size(self): return self.table.size

    def table(self, *args, **kwargs):
        return self.parsers["table"](super().table(header=self.header, index=self.index), *args,  **kwargs)


class WebStaticDOMs(object):
    Text = WebTextDOM.create("WebStaticTextDOM", WebStaticDOMBase)
    Html = WebHtmlDOM.create("WebStaticHtmlDOM", WebStaticDOMBase)
    Link = WebLinkDOM.create("WebStaticLinkDOM", WebStaticDOMBase)
    Table = WebTableDOM.create("WebStaticTableDOM", WebStaticDOMBase)
    BadRequest = WebBadRequestDOM.create("WebStaticBadRequestDOM", WebStaticDOMBase)

class WebDynamicDOMs(object):
    Text = WebTextDOM.create("WebDynamicTextDOM", WebDynamicDOMBase)
    Html = WebHtmlDOM.create("WebDynamicHtmlDOM", WebDynamicDOMBase)
    Link = WebLinkDOM.create("WebDynamicLinkDOM", WebDynamicDOMBase)
    Table = WebTableDOM.create("WebDynamicTableDOM", WebDynamicDOMBase)
    BadRequest = WebBadRequestDOM.create("WebDynamicBadRequestDOM", WebDynamicDOMBase)
    ServerFailure = WebServerFailureDOM
    Checkable = WebCheckableDOM
    Clickable = WebClickableDOM
    Captcha = WebCaptchaDOM
    Input = WebInputDOM
    Select = WebSelectDOM

class WebJsonDOMs(object):
    Text = WebTextDOM.create("WebJsonTextDOM", WebJsonDOMBase)
    Json = WebJsonDOM

class WebDOMs(object):
    JSON = WebJsonDOMs
    STATIC = WebStaticDOMs
    DYNAMIC = WebDynamicDOMs



