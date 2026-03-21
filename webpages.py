# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
from abc import ABC, abstractmethod

from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMTPage", "WebJSONPage", "WebHTMLPage", "WebStream"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebStream(Logging, ABC):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__Pages__ = getattr(cls, "__Pages__", {}) | kwargs.get("pages", {})
        cls.__Page__ = kwargs.get("page", getattr(cls, "__Page__", None))

    def __init__(self, *args, source, account=None, authenticator=None, capacity=100, **kwargs):
        super().__init__(*args, **kwargs)
        parameters = dict(source=source, account=account, authenticator=authenticator)
        self.__pages = {key: value(**parameters) for key, value in self.Pages.items()}
        self.__page = self.Page(**parameters) if self.Page is not None else None
        self.__capacity = int(capacity)

    @property
    def Pages(self): return type(self).__Pages__
    @property
    def Page(self): return type(self).__Page__

    @property
    def capacity(self): return self.__capacity
    @property
    def pages(self): return self.__pages
    @property
    def page(self): return self.__page


class WebPage(Logging, ABC):
    def __init__(self, *args, source, account, authenticator, **kwargs):
        super().__init__(*args, **kwargs)
        self.__authenticator = authenticator
        self.__account = account
        self.__source = source

    @staticmethod
    def sleep(seconds): time.sleep(seconds)

    @abstractmethod
    def load(self, *args, **kwargs): pass

    @property
    def authenticator(self): return self.__authenticator
    @property
    def account(self): return self.__account
    @property
    def source(self): return self.__source


class WebJSONPage(WebPage, ABC):
    def load(self, url, *args, payload=None, **kwargs):
        self.console("Loading", str(url))
        self.source.load(url, *args, payload=payload, **kwargs)
        self.console("Loaded", f"JSON|statuscode|{str(self.source.status)}")
        return self.source.json

    @property
    def json(self): return self.source.json


class WebHTMLPage(WebPage, ABC):
    def load(self, url, *args, payload=None, **kwargs):
        self.console("Loading", str(url))
        self.source.load(url, *args, payload=payload, **kwargs)
        self.console("Loaded", f"HTML|statuscode|{str(self.source.status)}")
        return self.source.html

    @property
    def html(self): return self.source.html


class WebELMTPage(WebPage, ABC):
    def __getattr__(self, attribute):
        attributes = ("navigate", "pageup", "pagedown", "pagehome", "pageend", "maximize", "minimize", "refresh", "forward", "back")
        if attribute in attributes: return getattr(self.source, attribute)
        else: raise AttributeError(attribute)

    def load(self, url, *args, **kwargs):
        self.console("Loading", str(url))
        self.source.load(url, *args, **kwargs)
        self.console("Loaded", "ELMT")
        return self.source.element

    @property
    def elmt(self): return self.source.element
    @property
    def html(self): return self.source.html



