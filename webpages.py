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


class WebPageMeta(ABCMeta):
    def __init__(cls, *args, **kwargs):
        existing = list(getattr(cls, "__data__", []))
        update = kwargs.get("data", [])
        if isinstance(update, list): existing.extend(update)
        else: existing.append(update)
        cls.__data__ = existing + update

    def __call__(cls, *args, source, **kwargs):
        contents = {str(data): data(*args, source=source, **kwargs) for data in cls.data}
        parameters = dict(source=source, contents=contents)
        instance = super(WebPageMeta, cls).__call__(*args, **parameters, **kwargs)
        return instance

    @property
    def data(cls): return cls.__data__


class WebPage(Logging, ABC):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, *args, source, contents, **kwargs):
        super().__init__(*args, **kwargs)
        self.__contents = contents
        self.__source = source

    def __getitem__(self, key): return self.contents[key]
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)

    def load(self, url, *args, payload=None, parameters={}, headers={}, **kwargs):
        string = str("&").join([str("=").join(list(pairing)) for pairing in parameters.items()])
        string = ("&" if "?" in str(url) else "?") + str(string) if bool(string) else ""
        string = str(url) + str(string)
        self.logger.info(f"Loading: {repr(self)}")
        self.logger.info(string)
        self.source.load(url, payload=payload, parameters=parameters, headers=headers)

    @staticmethod
    def sleep(seconds): time.sleep(seconds)
    @abstractmethod
    def execute(self, *args, **kwargs): pass

    @property
    def contents(self): return self.__contents
    @property
    def source(self): return self.__source


class WebJsonPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Session|Json"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.feed.response.status_code
        self.logger.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")


class WebHtmlPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Session|Html"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.feed.response.status_code
        self.logger.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")


class WebBrowserPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Browser|{str(self.feed.browser.name).title()}"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        self.logger.info(f"Loaded: {repr(self)}")







