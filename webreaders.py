# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   WebReader Objects
@author: Jack Kirby Cook

"""

import requests
import lxml.html
import multiprocessing
from rauth import OAuth1Service
from abc import ABC, abstractmethod

from support.meta import RegistryMeta
from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebReader", "WebService", "WebStatusError"]
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


class WebService(ABC):
    def __init_subclass__(cls, *args, **kwargs):
        base = kwargs.get("base", getattr(cls, "__urls__", {}).get("base_url", None))
        access = kwargs.get("access", getattr(cls, "__urls__", {}).get("access_token_url", None))
        request = kwargs.get("request", getattr(cls, "__urls__", {}).get("request_token_url", None))
        authorize = kwargs.get("authorize", getattr(cls, "__urls__", {}).get("authorize_url", None))
        cls.__urls__ = {"authorize_url": authorize, "request_token_url": request, "access_token_url": access, "base_url": base}

    def __init__(self, *args, delayer, webapi, **kwargs):
        assert hasattr(webapi, "identity") and hasattr(webapi, "code")
        self.__delayer = delayer
        self.__webapi = webapi

    def __call__(self, *args, **kwargs):
        service = OAuth1Service(consumer_key=self.webapi.identity, consumer_secret=self.webapi.code, **self.urls)
        token, secret = service.get_request_token(params={"oauth_callback": "oob"}, header_auth=True)
        url = str(service.authorize_url).format(str(self.webapi.identity), str(token))
        security = self.security(url, *args, **kwargs)
        session = service.get_auth_session(token, secret, params={"oauth_verifier": security})
        session.headers.update({"consumerKey": self.webapi.identity})
        return session

    @abstractmethod
    def security(self, url, *args, **kwargs): pass

    @property
    def urls(self): return type(self).__urls__
    @property
    def webapi(self): return self.__webapi


class WebReader(Logging, ABC):
    def __bool__(self): return self.session is not None
    def __init__(self, *args, delayer, service=requests.Session, authenticate=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.__mutex = multiprocessing.Lock()
        self.__authenticate = authenticate
        self.__service = service
        self.__delayer = delayer
        self.__session = None
        self.__response = None
        self.__request = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.stop()

    def start(self):
        self.session = self.service()

    def stop(self):
        self.session.close()
        self.session = None
        self.response = None
        self.request = None

    def load(self, url, *args, payload=None, **kwargs):
        address, params, headers = url
        parameters = dict(params=params, headers=headers)
        if bool(self.authenticate): parameters.update({"header_auth": True})
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
    def authenticate(self): return self.__authenticate
    @property
    def service(self): return self.__service
    @property
    def delayer(self): return self.__delayer
    @property
    def mutex(self): return self.__mutex

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


