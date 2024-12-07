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

from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebBrowserPage", "WebJsonPage", "WebHtmlPage", "WebPageError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebPageErrorMeta(RegistryMeta):
    def __init__(cls, name, bases, attrs, *args, title=None, **kwargs):
        assert str(name).endswith("Error")
        super(WebPageErrorMeta, cls).__init__(name, bases, attrs, *args, **kwargs)
        cls.__logger__ = __logger__
        cls.__title__ = title

    def __call__(cls, page):
        logger, title, name = cls.__logger__, cls.__title__, cls.__name__
        instance = super(WebPageErrorMeta, cls).__call__(name, page)
        logger.info(f"{title}: {repr(instance.page)}")
        return instance


class WebPageError(Exception, metaclass=WebPageErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return f"{self.name}|{repr(self.page)}"
    def __init__(self, name, page):
        self.__page = page
        self.__name = name

    @property
    def page(self): return self.__page
    @property
    def name(self): return self.__name


class BadRequestError(WebPageError, title="BadRequest", register="badrequest"): pass
class CaptchaError(WebPageError, title="Captcha", register="captcha"): pass
class ServerFailureError(WebPageError, title="ServerFailure", register="serverfailure"): pass
class ResponseFailureError(WebPageError, title="ResponseFailure", register="responsefailure"): pass
class RefusalError(WebPageError, title="Refusal", register="refusal"): pass
class PaginationError(WebPageError, title="Pagination", register="pagination"): pass
class CrawlingError(WebPageError, title="Crawling", register="crawling"): pass


class WebPage(Logging, ABC):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, *args, feed, **kwargs):
        Logging.__init__(self, *args, **kwargs)
        self.feed = feed

    def load(self, url, *args, payload=None, params={}, headers={}, **kwargs):
        string = "&".join(["=".join([str(key), str(value)]) for key, value in params.items()])
        string = ("?" + string) if "?" not in str(url) else ("&" + string)
        string = str(url) + (string if bool(params) else "")
        self.logger.info(f"Loading: {repr(self)}")
        self.logger.info(str(string))
        self.feed.load(url, payload=payload, params=params, headers=headers)

    @staticmethod
    def sleep(seconds): time.sleep(seconds)

    @property
    @abstractmethod
    def source(self): pass


class WebJsonPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Session|Json"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.feed.response.status_code
        self.logger.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")

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
        self.logger.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")

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
        self.logger.info(f"Loaded: {repr(self)}")

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






