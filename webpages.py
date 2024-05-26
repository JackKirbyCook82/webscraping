# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
import logging
from abc import ABC, abstractmethod
from support.meta import RegistryMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebBrowserPage", "WebJsonPage", "WebHtmlPage", "WebPageError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebPageErrorMeta(RegistryMeta):
    def __init__(cls, name, bases, attrs, *args, **kwargs):
        assert str(name).endswith("Error")
        super(WebPageErrorMeta, cls).__init__(name, bases, attrs, *args, **kwargs)

    def __call__(cls, *args, **kwargs):
        instance = super(WebPageErrorMeta, cls).__call__(*args, **kwargs)
        __logger__.info(instance.name).replace("Error", f": {repr(instance.page)}")
        return instance


class WebPageError(Exception, metaclass=WebPageErrorMeta):
    def __str__(self): return f"{self.name}|{repr(self.page)}"
    def __init__(self, page):
        self.__name = self.__class__.__name__
        self.__page = page

    @property
    def page(self): return self.__page
    @property
    def name(self): return self.__name


class BadRequestError(WebPageError, register="badrequest"): pass
class CaptchaError(WebPageError, register="captcha"): pass
class ServerFailureError(WebPageError, register="serverfailure"): pass
class ResponseFailureError(WebPageError, register="responsefailure"): pass
class RefusalError(WebPageError, register="refusal"): pass
class PaginationError(WebPageError, register="pagination"): pass
class CrawlingError(WebPageError, register="crawling"): pass


class WebPage(ABC):
    def __repr__(self): return self.name
    def __init__(self, *args, feed, **kwargs):
        self.__name = kwargs.get("name", self.__class__.__name__)
        self.__feed = feed

    def load(self, url, *args, payload=None, params={}, headers={}, **kwargs):
        string = "&".join(["=".join([str(key), str(value)]) for key, value in params.items()])
        string = ("?" + string) if "?" not in str(url) else ("&" + string)
        string = str(url) + (string if bool(params) else "")
        __logger__.info(f"Loading: {repr(self)}")
        __logger__.info(str(string))
        self.feed.load(url, payload=payload, params=params, headers=headers)

    @staticmethod
    def sleep(seconds): time.sleep(seconds)

    @property
    @abstractmethod
    def source(self): pass
    @property
    def name(self): return self.__name
    @property
    def feed(self): return self.__feed


class WebJsonPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Session|Json"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.feed.response.status_code
        __logger__.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")

    @property
    def source(self): return self.json
    @property
    def pretty(self): return self.feed.pretty
    @property
    def html(self): return self.feed.html
    @property
    def text(self): return self.feed.text
    @property
    def json(self): return self.feed.json


class WebHtmlPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Session|Html"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.feed.response.status_code
        __logger__.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")

    @property
    def source(self): return self.html
    @property
    def pretty(self): return self.feed.pretty
    @property
    def html(self): return self.feed.html
    @property
    def text(self): return self.feed.text


class WebBrowserPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Browser|{str(self.feed.browser.name).title()}"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        __logger__.info(f"Loaded: {repr(self)}")

    def run(self, *args, **kwargs):
        __logger__.info(f"Running: {repr(self)}")
        self.execute(*args, **kwargs)

    def execute(self, *args, **kwargs): pass
    def forward(self): self.feed.foward()
    def back(self): self.feed.back()
    def refresh(self): self.feed.refresh()
    def maximize(self): self.feed.maximize()
    def minimize(self): self.feed.minimize()
    def pageup(self): self.feed.pageup()
    def pagedown(self): self.feed.pagedown()
    def pagehome(self): self.feed.pagehome()
    def pageend(self): self.feed.pageend()

    @property
    def source(self): return self.feed.html
    @property
    def url(self): return self.feed.url
    @property
    def pretty(self): return self.feed.pretty
    @property
    def html(self): return self.feed.html
    @property
    def text(self): return self.feed.text






