# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   WebReader Objects
@author: Jack Kirby Cook

"""

import time
import requests
import lxml.html
import multiprocessing
from datetime import datetime as Datetime

from support.meta import RegistryMeta
from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebReader", "WebStatusError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
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


class WebReader(Logging):
    def __bool__(self): return self.session is not None
    def __init__(self, *args, delay=5, **kwargs):
        super().__init__(*args, **kwargs)
        self.__mutex = multiprocessing.Lock()
        self.__delay = int(delay)
        self.__session = None
        self.__response = None
        self.__request = None
        self.__timer = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.stop()

    def start(self): self.session = requests.Session()
    def stop(self):
        self.session.close()
        self.session = None
        self.response = None
        self.request = None

    def load(self, url, *args, payload=None, parameters={}, **kwargs):
        address, params, headers = url
        keywords = dict(params=params, headers=headers) | parameters
        with self.mutex:
            elapsed = (Datetime.now() - self.timer).total_seconds() if bool(self.timer) else self.delay
            wait = max(self.delay - elapsed, 0) if bool(self.delay) else 0
            if bool(wait):
                self.console(f"{elapsed:.02f} seconds", title="Waiting")
                time.sleep(wait)
            if payload is None: response = self.session.get(str(address), **keywords)
            else: response = self.session.post(str(address), json=payload, **keywords)
            self.timer = Datetime.now()
            self.request = response.request
            self.response = response
        if not self.response.status_code == requests.codes.ok:
            statuscode = self.response.status_code
            raise WebStatusError(int(statuscode))

    @property
    def html(self): return lxml.html.fromstring(self.response.text)
    @property
    def json(self): return self.response.json()
    @property
    def status(self): return self.response.status_code
    @property
    def text(self): return self.response.text
    @property
    def url(self): return self.response.url

    @property
    def session(self): return self.__session
    @session.setter
    def session(self, session): self.__session = session
    @property
    def response(self): return self.__response
    @response.setter
    def response(self, response): self.__response = response
    @property
    def request(self): return self.__request
    @request.setter
    def request(self, request): self.__request = request

    @property
    def delay(self): return self.__delay
    @property
    def mutex(self): return self.__mutex

    @property
    def timer(self): return self.__timer
    @timer.setter
    def timer(self, timer): self.__timer = timer




