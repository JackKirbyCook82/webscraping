# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
import logging
from abc import ABC, ABCMeta, abstractmethod

from support.meta import RegistryMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMTPage", "WebJSONPage", "WebHTMLPage", "WebPageError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebPageErrorMeta(RegistryMeta):
    def __init__(cls, name, bases, attrs, *args, title=None, **kwargs):
        assert str(name).endswith("Error")
        super(WebPageErrorMeta, cls).__init__(name, bases, attrs, *args, **kwargs)
        cls.__title__ = title

    def __call__(cls, page):
        instance = super(WebPageErrorMeta, cls).__call__(page)
        __logger__.info(f"{cls.title}: {repr(page)}")
        return instance

    @property
    def title(cls): return cls.__title__
    @property
    def name(cls): return cls.__name__


class WebPageError(Exception, metaclass=WebPageErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return f"{type(self).name}|{repr(self.page)}"
    def __init__(self, page): self.__page = page

    @property
    def page(self): return self.__page


class BadRequestError(WebPageError, title="BadRequest", register="badrequest"): pass
class CaptchaError(WebPageError, title="Captcha", register="captcha"): pass
class ServerFailureError(WebPageError, title="ServerFailure", register="serverfailure"): pass
class ResponseFailureError(WebPageError, title="ResponseFailure", register="responsefailure"): pass
class RefusalError(WebPageError, title="Refusal", register="refusal"): pass
class PaginationError(WebPageError, title="Pagination", register="pagination"): pass
class CrawlingError(WebPageError, title="Crawling", register="crawling"): pass


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


class WebPage(object, ABC):
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
        __logger__.info(f"Loading: {repr(self)}")
        __logger__.info(str(url))
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
    def __repr__(self): return f"{self.name}|Session|Json"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.source.response.status_code
        __logger__.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")

    @property
    def json(self): return self.source.json
    @property
    def content(self): return self.source.json


class WebHTMLPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Session|Html"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.source.response.status_code
        __logger__.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")

    @property
    def html(self): return self.source.html
    @property
    def content(self): return self.source.html


class WebELMTPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Browser|{str(self.source.browser.name).title()}"
    def __getattr__(self, attribute):
        attributes = ("navigate", "pageup", "pagedown", "pagehome", "pageend", "maximize", "minimize", "refresh", "forward", "back")
        if attribute in attributes: return getattr(self.source, attribute)
        else: raise AttributeError(attribute)

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        __logger__.info(f"Loaded: {repr(self)}")

    @property
    def html(self): return self.source.html
    @property
    def elmt(self): return self.source.element
    @property
    def content(self): return self.source.element





