# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
from abc import ABC, ABCMeta, abstractmethod

from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMTPage", "WebJSONPage", "WebHTMLPage"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebPageMeta(ABCMeta):
    def __init__(cls, *args, **kwargs):
        url = kwargs.get("url", getattr(cls, "__attributes__", {}).get("url", None))
        data = kwargs.get("data", getattr(cls, "__attributes__", {}).get("data", {}))
        cls.__attributes__ = dict(url=url, data=data)

    def __call__(cls, *args, **kwargs):
        instance = super(WebPageMeta, cls).__call__(*args, **cls.attributes, **kwargs)
        return instance

    @property
    def attributes(cls): return cls.__attributes__


class WebPage(Logging, ABC, metaclass=WebPageMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, *args, source, url=None, data=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__source = source
        self.__data = data
        self.__url = url

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def load(self, url, *args, payload=None, headers={}, **kwargs):
        assert all([hasattr(url, attribute) for attribute in ("address", "parameters")])
        self.console(str(url), title="Loading")
        self.source.load(url, payload=payload, headers=headers)

    def execute(self, *args, **kwargs):
        url = self.url(*args, **kwargs)
        self.load(url, *args, **kwargs)
        function = lambda data: data(self.content, *args, **kwargs)
        if isinstance(self.data, dict): return {dataset: function(data) for dataset, data in self.data.items()}
        elif isinstance(self.data, list): return [function(data) for data in self.data]
        else: return function(self.data)

    @staticmethod
    def sleep(seconds): time.sleep(seconds)

    @property
    @abstractmethod
    def content(self): pass

    @property
    def source(self): return self.__source
    @property
    def data(self): return self.__data
    @property
    def url(self): return self.__url


class WebJSONPage(WebPage, ABC):
    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.source.response.status_code
        self.console(f"JSON|StatusCode|{str(status_code)}", title="Loaded")

    @property
    def json(self): return self.source.json
    @property
    def content(self): return self.source.json


class WebHTMLPage(WebPage, ABC):
    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.source.response.status_code
        self.console(f"HTML|StatusCode|{str(status_code)}", title="Loaded")

    @property
    def html(self): return self.source.html
    @property
    def content(self): return self.source.html


class WebELMTPage(WebPage, ABC):
    def __getattr__(self, attribute):
        attributes = ("navigate", "pageup", "pagedown", "pagehome", "pageend", "maximize", "minimize", "refresh", "forward", "back")
        if attribute in attributes: return getattr(self.source, attribute)
        else: raise AttributeError(attribute)

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        browser = self.source.browser.name
        self.console(f"ELMT|{str(browser)}", title="Loaded")

    @property
    def html(self): return self.source.html
    @property
    def elmt(self): return self.source.element
    @property
    def content(self): return self.source.element





