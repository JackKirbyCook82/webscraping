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
__all__ = ["WebELMTPage", "WebJSONPage", "WebHTMLPage"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


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
        self.console(str(url), title="Loading")
        self.source.load(url, *args, payload=payload, **kwargs)
        self.console(f"JSON|statuscode|{str(self.source.status)}", title="Loaded")
        return self.source.json

    @property
    def json(self): return self.source.json


class WebHTMLPage(WebPage, ABC):
    def load(self, url, *args, payload=None, **kwargs):
        self.console(str(url), title="Loading")
        self.source.load(url, *args, payload=payload, **kwargs)
        self.console(f"HTML|statuscode|{str(self.source.status)}", title="Loaded")
        return self.source.html

    @property
    def html(self): return self.source.html


class WebELMTPage(WebPage, ABC):
    def __getattr__(self, attribute):
        attributes = ("navigate", "pageup", "pagedown", "pagehome", "pageend", "maximize", "minimize", "refresh", "forward", "back")
        if attribute in attributes: return getattr(self.source, attribute)
        else: raise AttributeError(attribute)

    def load(self, url, *args, **kwargs):
        self.console(str(url), title="Loading")
        self.source.load(url, *args, **kwargs)
        return self.source.element

    @property
    def elmt(self): return self.source.element
    @property
    def html(self): return self.source.html



