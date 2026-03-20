# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   WebReader Objects
@author: Jack Kirby Cook

"""

import requests
import lxml.html

from webscraping.websources import WebSource
from support.meta import RegistryMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebReader", "WebStatusError"]
__copyright__ = "Copyright 2026, Jack Kirby Cook"
__license__ = "MIT License"


class WebStatusErrorMeta(RegistryMeta):
    def __init__(cls, *args, **kwargs):
        super(WebStatusErrorMeta, cls).__init__(*args, **kwargs)
        cls.__title__ = kwargs.get("title", getattr(cls, "__title__", None))

    def __call__(cls, statuscode, *args, **kwargs):
        error = super(WebStatusErrorMeta, cls[statuscode]).__call__(*args, **kwargs)
        return error

    @property
    def title(cls): return cls.__title__
    @property
    def name(cls): return cls.__name__

class WebStatusError(Exception, metaclass=WebStatusErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass

class BadRequestError(WebStatusError, register=400, title="BadRequest"): pass
class AuthenticationError(WebStatusError, register=401, title="Authentication"): pass
class ForbiddenRequestError(WebStatusError, register=403, title="ForbiddenRequest"): pass
class IncorrectRequestError(WebStatusError, register=404, title="IncorrectRequest"): pass
class GatewayError(WebStatusError, register=502, title="Gateway"): pass
class UnavailableError(WebStatusError, register=503, title="Unavailable"): pass


class WebReader(WebSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__response = None
        self.__request = None

    def start(self):
        self.session = requests.Session()

    def stop(self):
        if self.session is not None: self.session.close()
        self.session = None
        self.response = None
        self.request = None

    def load(self, url, *args, payload=None, **kwargs):
        address, params, headers = url
        parameters = dict(params=params, headers=headers)
        with self.mutex:
            if payload is None: response = self.session.get(str(address), **parameters)
            else: response = self.session.post(str(address), data=payload, **parameters)
            self.request = response.request
            self.response = response
        if not self.response.status_code == requests.codes.ok:
            statuscode = self.response.status_code
            raise WebStatusError(int(statuscode))

    @property
    def html(self): return lxml.html.fromstring(self.response.content)
    @property
    def json(self): return self.response.json()
    @property
    def status(self): return self.response.status_code
    @property
    def text(self): return self.response.text
    @property
    def url(self): return self.response.url

    @property
    def session(self): return self.source
    @session.setter
    def session(self, session): self.source = session
    @property
    def response(self): return self.__response
    @response.setter
    def response(self, response): self.__response = response
    @property
    def request(self): return self.__request
    @request.setter
    def request(self, request): self.__request = request



