# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPage Objects
@author: Jack Kirby Cook

"""

import time
import logging
from abc import ABC, abstractmethod

from webscraping.weberrors import WebPageError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebBrowserPage", "WebJsonPage", "WebHtmlPage", "ConditionMixin", "CaptchaMixin", "IterationMixin", "PaginationMixin", "CrawlingMixin"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


LOGGER = logging.getLogger(__name__)


class OperationError(Exception): pass
class IterationNotSupportedError(OperationError): pass
class PaginationNotSupportedError(OperationError): pass
class CrawlingNotSupportedError(OperationError): pass
class IterationEmptyError(OperationError): pass
class PaginationEmptyError(OperationError): pass
class CrawlingEmptyError(OperationError): pass

class ConditionError(Exception): pass
class CaptchaNotSupportedError(ConditionError): pass


class WebPage(ABC):
    def __init_subclass__(cls, *args, **kwargs):
        pass

#        cls.__reader__ = kwargs.get("reader", None)
#        cls.__writer__ = kwargs.get("writer", None)

    def __repr__(self): return self.name
    def __init__(self, feed, *args, **kwargs):
        self.__name = kwargs.get("name", self.__class__.__name__)
        self.__feed = feed

    def load(self, url, *args, payload=None, params={}, headers={}, **kwargs):
        string = "&".join(["=".join([str(key), str(value)]) for key, value in params.items()])
        string = ("?" + string) if "?" not in str(url) else ("&" + string)
        string = str(url) + (string if bool(params) else "")
        LOGGER.info("WebPage Loading: {}".format(repr(self)))
        LOGGER.info(str(string))
        self.feed.load(url, payload=payload, params=params, headers=headers)

    @staticmethod
    def sleep(seconds): time.sleep(seconds)
    @abstractmethod
    def load(self, *args, **kwargs): pass

    @property
    def name(self): return self.__name
    @property
    def feed(self): return self.__feed

#    @property
#    def reader(self): return self.__class__.__reader__
#    @property
#    def writer(self): return self.__class__.__writer__


class WebJsonPage(WebPage, ABC):
    def __repr__(self): return "{}|{}|{}".format(self.name, "Session", "Json")

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.feed.response.status_code
        LOGGER.info("WebPage Loaded: {}: StatusCode|{}".format(repr(self), str(status_code)))

#    def read(self, *args, **kwargs):
#        LOGGER.info("WebPage Reading: {}".format(repr(self)))
#        content = self.reader(self.json)
#        return content(*args, **kwargs)

    @property
    def pretty(self): return self.feed.pretty
    @property
    def html(self): return self.feed.html
    @property
    def text(self): return self.feed.text
    @property
    def json(self): return self.feed.json


class WebHtmlPage(WebPage, ABC):
    def __repr__(self): return "{}|{}|{}".format(self.name, "Session", "Html")

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        status_code = self.feed.response.status_code
        LOGGER.info("WebPage Loaded: {}: StatusCode|{}".format(repr(self), str(status_code)))

#    def read(self, *args, **kwargs):
#        LOGGER.info("WebPage Reading: {}".format(repr(self)))
#        content = self.reader(self.html)
#        return content(*args, **kwargs)

    @property
    def pretty(self): return self.feed.pretty
    @property
    def html(self): return self.feed.html
    @property
    def text(self): return self.feed.text


class WebBrowserPage(WebPage, ABC):
    def __repr__(self): return "{}|{}|{}".format(self.name, "Browser", str(self.feed.browser).title())

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        LOGGER.info("WebPage Loaded: {}".format(repr(self)))

    def run(self, *args, **kwargs):
        LOGGER.info("WebPage Running: {}".format(repr(self)))
        self.execute(*args, **kwargs)

#    def read(self, *args, **kwargs):
#        LOGGER.info("WebPage Reading: {}".format(repr(self)))
#        content = self.reader(self.html)
#        return content(*args, **kwargs)

    def execute(self, *args, **kwargs): pass
    def forward(self): self.feed.foward()
    def back(self): self.feed.back()
    def refresh(self): self.feed.refresh()
    def maximize(self): self.feed.maximize()
    def minimize(self): self.feed.minimize()
    def pageUp(self): self.feed.pageUp()
    def pageDown(self): self.feed.pageDown()
    def pageHome(self): self.feed.pageHome()
    def pageEnd(self): self.feed.pageEnd()

    @property
    def driver(self): return self.feed.driver
    @property
    def url(self): return self.feed.url

    @property
    def pretty(self): return self.feed.pretty
    @property
    def html(self): return self.feed.html
    @property
    def text(self): return self.feed.text


class ConditionMixin(WebPage, ABC):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.__badrequest__ = kwargs.get("badrequest", getattr(cls, "__badrequest__", None))
        cls.__refusal__ = kwargs.get("refusal", getattr(cls, "__refusal__", None))
        cls.__serverfailure__ = kwargs.get("serverfailure", getattr(cls, "__serverfailure__", None))

    def __new__(cls, *args, **kwargs):
        if cls.__badrequest__ is None:
            LOGGER.info("BadRequest Not Supported: {}".format(cls.__name__))
        if cls.__refusal__ is None:
            LOGGER.info("Refusal Not Supported: {}".format(cls.__name__))
        if cls.__serverfailure__ is None:
            LOGGER.info("ServerFailure Not Supported: {}".format(cls.__name__))
        return super().__new__(cls)

    @classmethod
    def badrequest(cls, html): return cls.__badrequest__(html)
    @classmethod
    def refusal(cls, html): return cls.__refusal__(html)
    @classmethod
    def serverfailure(cls, html): return cls.__serverfailure__(html)

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        badrequest = self.badrequest(self.html)
        if bool(badrequest):
            LOGGER.info("WebPage Loading Failure: {}".format(repr(self)))
            raise WebPageError["badrequest"](self)
        refusal = self.refusal(self.html)
        if bool(refusal):
            LOGGER.info("WebPage Loading Failure: {}".format(repr(self)))
            raise WebPageError["refusal"](self)
        serverfailure = self.serverfailure(self.html)
        if bool(serverfailure):
            LOGGER.info("WebPage Loading Failure: {}".format(repr(self)))
            raise WebPageError["serverfailure"](self)
        LOGGER.info("WebPage Loading Success: {}".format(repr(self)))


class CaptchaMixin(WebBrowserPage, ABC):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.__captcha__ = kwargs.get("captcha", getattr(cls, "__captcha__", None))

    def __new__(cls, *args, **kwargs):
        if cls.__captcha__ is None:
            raise CaptchaNotSupportedError(cls.__name__)
        return super().__new__(cls)

    @classmethod
    def captcha(cls, driver): return cls.__captcha__(driver)

    def load(self, *args, **kwargs):
        super().load(*args, **kwargs)
        captcha = self.captcha(self.driver)
        if bool(captcha):
            cleared = captcha.clear()
            if not bool(cleared):
                raise WebPageError["captcha"](self)
        LOGGER.info("Ready: {}".format(repr(self)))


class IterationMixin(WebBrowserPage, ABC):
    def __iter__(self): return self.iterate()

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.__iterator__ = kwargs.get("iterate", getattr(cls, "__iterator__", None))

    def __new__(cls, *args, **kwargs):
        if cls.__iterator__ is None:
            raise IterationNotSupportedError(cls.__name__)
        return super().__new__(cls)

    @classmethod
    def iterator(cls, driver): return cls.__iterator__(driver)

    def iterate(self):
        LOGGER.info("WebPage Iterating: {}".format(repr(self)))
        iterator = self.iterator(self.feed.driver)
        if not bool(iterator):
            LOGGER.info("WebPage Iterator Empty: {}".format(repr(self)))
            raise IterationEmptyError(self)
        return iter(iterator)


class PaginationMixin(WebBrowserPage, ABC):
    def __next__(self): return self.pagination()

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.__pager__ = kwargs.get("pagination", getattr(cls, "__pager__", None))

    def __new__(cls, *args, **kwargs):
        if cls.__pagination__ is None:
            raise PaginationNotSupportedError(cls.__name__)
        return super().__new__(cls)

    @classmethod
    def pager(cls, driver): return cls.__pager__(driver)

    def pagination(self):
        type(self.feed).wait()
        pagination = self.pagination(self.feed.driver)
        if not bool(pagination):
            raise PaginationEmptyError(self)
        fromURL = str(self.url)
        toURL = str(pagination.url)
        assert fromURL != toURL
        LOGGER.info("WebPage Pagination: {}".format(repr(self)))
        LOGGER.info("{}".format(str(toURL)))
        pagination.click()
        newURL = str(self.url)
        if fromURL == newURL:
            LOGGER.info("WebPage Pagination Failure: {}".format(repr(self)))
            raise WebPageError["pagination"](self)
        LOGGER.info("WebPage Pagination Success: {}".format(repr(self)))
        return self


class CrawlingMixin(WebBrowserPage, ABC):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.__crawler__ = kwargs.get("crawl", getattr(cls, "__crawler__", None))

    def __new__(cls, *args, **kwargs):
        if cls.__crawler__ is None:
            raise CrawlingNotSupportedError(cls.__name__)
        return super().__new__(cls)

    @classmethod
    def crawler(cls, driver): return cls.__crawler__(driver)

    def crawl(self, key):
        type(self.feed).wait()
        crawler = self.crawler(self.feed.driver)
        if not bool(crawler):
            raise CrawlingEmptyError(self)
        fromURL = str(self.url)
        toURL = str(crawler[key].url)
        assert fromURL != toURL
        LOGGER.info("WebPage Crawling: {}".format(repr(self)))
        LOGGER.info("{}".format(str(toURL)))
        crawler.sel(choice=key)
        newURL = str(self.url)
        if fromURL == newURL:
            LOGGER.info("WebPage Crawling Failure: {}".format(repr(self)))
            raise WebPageError["crawling"](self)
        LOGGER.info("WebPage Crawling Success: {}".format(repr(self)))
        return self



