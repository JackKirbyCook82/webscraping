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
    def __init__(self, *args, source, **kwargs):
        super().__init__(*args, **kwargs)
        self.__source = source

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def load(self, url, *args, payload=None, headers={}, **kwargs):
        assert isinstance(url, tuple) and len(url) == 2
        assert all([hasattr(url, attribute) for attribute in ("address", "parameters")])
        self.logger.info(f"Loading: {repr(self)}")
        self.logger.info(str(url))
        self.source.load(url, payload=payload, headers=headers)

    @staticmethod
    def sleep(seconds): time.sleep(seconds)
    @abstractmethod
    def execute(self, *args, **kwargs): pass

    @property
    def source(self): return self.__source


class WebJsonPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Session|Json"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.source.response.status_code
        self.logger.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")


class WebHtmlPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Session|Html"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.source.response.status_code
        self.logger.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")


class WebBrowserPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Browser|{str(self.source.browser.name).title()}"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        self.logger.info(f"Loaded: {repr(self)}")







