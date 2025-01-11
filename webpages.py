# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
from abc import ABC, abstractmethod

from support.meta import RegistryMeta
from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebBrowserPage", "WebJsonPage", "WebHtmlPage", "WebPageError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebPageErrorMeta(RegistryMeta):
    def __init__(cls, name, bases, attrs, *args, title=None, **kwargs):
        assert str(name).endswith("Error")
        super(WebPageErrorMeta, cls).__init__(name, bases, attrs, *args, **kwargs)
        cls.__title__ = title

    def __call__(cls, page):
        instance = super(WebPageErrorMeta, cls).__call__(page)
        page.logger.info(f"{cls.title}: {repr(page)}")
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


class WebPage(Logging, ABC):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, *args, source, **kwargs):
        super().__init__(*args, **kwargs)
        self.__source = source

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def load(self, url, *args, payload=None, headers={}, **kwargs):
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

    @property
    def json(self): return self.source.json


class WebHtmlPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Session|Html"

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.source.response.status_code
        self.logger.info(f"Loaded: {repr(self)}: StatusCode|{str(status_code)}")

    @property
    def html(self): return self.source.html


class WebBrowserPage(WebPage, ABC):
    def __repr__(self): return f"{self.name}|Browser|{str(self.source.browser.name).title()}"
    def __getattr__(self, attribute):
        attributes = ("navigate", "pageup", "pagedown", "pagehome", "pageend", "maximize", "minimize", "refresh", "forward", "back")
        if attribute in attributes: return getattr(self.source, attribute)
        else: raise AttributeError(attribute)

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        self.logger.info(f"Loaded: {repr(self)}")

    @property
    def elmt(self): return self.source.element
    @property
    def html(self): return self.source.html





