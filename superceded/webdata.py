# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebData Objects
@author: Jack Kirby Cook

"""

import json
import lxml.html
from colorama import Fore, Style
from collections.abc import Iterable
from abc import ABC, ABCMeta, abstractmethod
from lxml.html import HtmlElement as StaticElement
from selenium.webdriver.chrome.webdriver import WebDriver as DynamicDriver
from selenium.webdriver.remote.webelement import WebElement as DynamicElement

from utilities.dispatchers import typedispatcher

from webscraping.webnode import WebNode, WebNodeError


__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebData", "WebDataList", "WebDataDict"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


@typedispatcher
def string(source): raise TypeError(type(source).__name__)

@string.register(StaticElement)
def static_string(source):
    return lxml.html.tostring(source, pretty_print=True, encoding="unicode")

@string.register(list, dict)
def content_string(source):
    return json.dumps(source, sort_keys=True, indent=3, separators=(',', ' : '), default=str)

@string.register(str, int, float)
def value_string(source):
    return str(source)

@string.register(DynamicDriver)
def driver_string(source):
    html = lxml.html.fromstring(source.page_source)
    return lxml.html.tostring(html, pretty_print=True, encoding="unicode")

@string.register(DynamicElement)
def dynamic_string(source):
    html = lxml.html.fromstring(source.get_attribute("outerHTML"))
    return lxml.html.tostring(html, pretty_print=True, encoding="unicode")


class WebDataMeta(ABCMeta):
    def __repr__(cls): return repr(cls.__WebNode__)
    def __init__(cls, name, bases, attrs, *args, **kwargs):
        if not any([type(base) is WebDataMeta for base in bases]):
            return
        children = [value.__WebNode__ for value in attrs.values() if type(value) is WebDataMeta]
        try:
            parameters = dict(children=children)
            cls.__WebNode__ = type(name, (cls.__WebNode__,), {}, *args, **parameters, **kwargs)
        except AttributeError:
            parameters = dict(children=children, iterable=isinstance(cls, Iterable))
            cls.__WebNode__ = type(name, (WebNode,), {}, *args, **parameters, **kwargs)

    def __call__(cls, source):
        try:
            webnodes = cls.__WebNode__(source)
            instance = super(WebDataMeta, cls).__call__(webnodes)
            return instance
        except WebNodeError as error:
            content = string(source)
            print(Fore.RED + cls.__name__ + Style.RESET_ALL)
            print(Fore.RED + repr(cls) + Style.RESET_ALL)
            print(Fore.RED + content + Style.RESET_ALL)
            raise error


class WebDataBase(ABC, metaclass=WebDataMeta):
    def __init_subclass__(cls, *args, **kwargs): pass

    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __repr__(self): return "{}|{}[{:.0f}]".format(self.webnodes[0].name, self.webnodes[0].type, len(self))
    def __str__(self): return ",".join(self.webnodes)
    def __bool__(self): return bool(self.webnodes)
    def __len__(self): return len(self.webnodes)

    @property
    @abstractmethod
    def webnodes(self): pass
    def execute(self, *args, **kwargs): pass


class WebData(WebDataBase, object, ABC):
    def __init__(self, webnode): self.__webnode = webnode
    def __getitem__(self, key): return self.webnode.get(key) if bool(self) else None
    def __getattr__(self, attr): return getattr(self.webnode, attr) if bool(self) else None

    @property
    def webnodes(self): return list(filter(None, [self.webnode]))
    @property
    def webnode(self): return self.webnode


class WebDataList(WebDataBase, list, ABC):
    def __init__(self, webnodes): super.__init__([webnode for webnode in webnodes])

    @property
    def webnodes(self): return list(self)


class WebDataDict(WebDataBase, dict, ABC):
    def __init__(self, webnodes): super().__init__({webnode.key: webnode for webnode in webnodes})

    @property
    def webnodes(self): return list(self.values())



