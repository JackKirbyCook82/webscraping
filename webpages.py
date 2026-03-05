# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
from types import SimpleNamespace
from abc import ABC, abstractmethod

from support.mixins import Sizing, Emptying, Partition, Logging
from support.custom import SliceOrderedDict as SODict

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMTPage", "WebJSONPage", "WebHTMLPage", "WebATTRPage", "WebDownloader", "WebUploader"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebStream(Sizing, Emptying, Partition, Logging, ABC):
    def __init_subclass__(cls, *args, pages, page=None, **kwargs):
        assert isinstance(pages, dict)
        super().__init_subclass__(*args, **kwargs)
        cls.__Pages__ = pages
        cls.__Page__ = page

    def __init__(self, *args, limit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__pages = SimpleNamespace(**{key: value(*args, **kwargs) for key, value in self.Pages.items()})
        self.__page = self.Page(*args, **kwargs) if self.Page is not None else None
        self.__limit = int(limit)

    @staticmethod
    def querys(querys, querytype):
        assert isinstance(querys, (list, dict, querytype))
        assert all([isinstance(query, querytype) for query in querys]) if isinstance(querys, (list, dict)) else True
        if isinstance(querys, querytype): querys = [querys]
        elif isinstance(querys, dict): querys = SODict(querys)
        else: querys = list(querys)
        return querys

    @property
    def Pages(self): return self.__Pages__
    @property
    def Page(self): return self.__Page__

    @property
    def limit(self): return self.__limit
    @property
    def pages(self): return self.__pages
    @property
    def page(self): return self.__page


class WebDownloader(WebStream, ABC, title="Downloaded"): pass
class WebUploader(WebStream, ABC, title="Uploaded"): pass


class WebPage(Logging, ABC):
    def __init__(self, *args, source, **kwargs):
        super().__init__(*args, **kwargs)
        self.__source = source

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    @staticmethod
    def sleep(seconds): time.sleep(seconds)

    @abstractmethod
    def execute(self, *args, **kwargs): pass
    @abstractmethod
    def load(self, *args, **kwargs): pass

    @property
    def source(self): return self.__source


class WebATTRPage(WebPage, ABC):
    def load(self, dataset, *args, **kwargs):
        self.console(str(dataset), title="Loading")
        return self.source.load(dataset, *args, **kwargs)


class WebJSONPage(WebPage, ABC):
    def load(self, url, *args, payload=None, **kwargs):
        self.console(str(url), title="Loading")
        self.source.load(url, *args, payload=payload, **kwargs)
        self.console(f"JSON|statuscode|{str(self.source.status)}", title="Loaded")

    @property
    def json(self): return self.source.json


class WebHTMLPage(WebPage, ABC):
    def load(self, url, *args, payload=None, **kwargs):
        self.console(str(url), title="Loading")
        self.source.load(url, *args, payload=payload, **kwargs)
        self.console(f"HTML|statuscode|{str(self.source.status)}", title="Loaded")

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

    @property
    def elmt(self): return self.source.element
    @property
    def html(self): return self.source.html



