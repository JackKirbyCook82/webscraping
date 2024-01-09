# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebError Objects
@author: Jack Kirby Cook

"""

import logging

from support.meta import RegistryMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebStatusError", "WebPageError", "WebFeedError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


LOGGER = logging.getLogger(__name__)


class WebStatusErrorMeta(RegistryMeta):
    def __init__(cls, *args, statuscode=None, **kwargs):
        if not any([type(base) is WebStatusErrorMeta for base in cls.__bases__]):
            return
        assert isinstance(statuscode, int)
        super(WebStatusErrorMeta, cls).__init__(*args, key=statuscode, **kwargs)
        cls.__statuscode__ = statuscode

    @property
    def statuscode(cls): return cls.__statuscode__


class WebStatusError(Exception, metaclass=WebStatusErrorMeta):
    def __init_subclass__(cls, **kwargs):
        assert str(cls.__name__).endswith("Error")
        super().__init_subclass__(**kwargs)

    def __init__(self, feed):
        LOGGER.info(str(self.__class__.__name__).replace("Error", f": {repr(feed)}"))
        LOGGER.info(str(feed.url))
        self.__feed = feed
        self.__url = feed.url

    def __repr__(self): return f"{self.__class__.__name__}({repr(self.feed)}, statuscode={str(self.__class__.statuscode)})"
    def __str__(self): return f"{self.__class__.__name__}|{repr(self.feed)}[{str(self.__class__.statuscode)}]\n{str(self.url)}"

    @property
    def feed(self): return self.__feed
    @property
    def url(self): return self.__url


class AuthenticationError(WebStatusError, statuscode=401): pass
class ForbiddenRequestError(WebStatusError, statuscode=403): pass
class IncorrectRequestError(WebStatusError, statuscode=404): pass
class GatewayError(WebStatusError, statuscode=502): pass
class UnavailableError(WebStatusError, statuscode=503): pass


class WebPageError(Exception, metaclass=RegistryMeta):
    def __init_subclass__(cls, **kwargs):
        assert str(cls.__name__).endswith("Error")
        super().__init_subclass__(**kwargs)

    def __init__(self, page):
        LOGGER.info(str(self.__class__.__name__).replace("Error", f": {repr(page)}"))
        self.__page = page

    def __repr__(self): return f"{self.__class__.__name__}({repr(self.page)})"
    def __str__(self): return f"{self.__class__.__name__}|{repr(self.page)}"

    @property
    def page(self): return self.__page


class BadRequestError(WebPageError, key="badrequest"): pass
class CaptchaError(WebPageError, key="captcha"): pass
class ServerFailureError(WebPageError, key="serverfailure"): pass
class ResponseFailureError(WebPageError, key="responsefailure"): pass
class RefusalError(WebPageError, key="refusal"): pass
class PaginationError(WebPageError, key="pagination"): pass
class CrawlingError(WebPageError, key="crawling"): pass


class WebFeedError(Exception):
    def __init_subclass__(cls, **kwargs):
        assert str(cls.__name__).endswith("Error")
        super().__init_subclass__(**kwargs)

    def __init__(self, feed):
        LOGGER.info(str(self.__class__.__name__).replace("Error", f": {str(feed)}"))
        self.__feed = feed

    def __repr__(self): return f"{self.__class__.__name__}({repr(self.feed)})"
    def __str__(self): return f"{self.__class__.__name__}|{repr(self.feed)}"

    @property
    def feed(self): return self.__feed




