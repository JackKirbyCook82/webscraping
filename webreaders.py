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

from webscraping.webinterface import WebInterface
from support.meta import RegistryMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebReader", "WebService", "WebStatusError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"

from webscraping.websupport import WebDelayer


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

    def __call__(self, *args, account, authenticator, **kwargs):
        parameters = dict(account=account, authenticator=authenticator, delayer=delayer)
        service = OAuth1Service(consumer_key=authenticator.identity, consumer_secret=authenticator.code, **self.urls)
        token, secret = service.get_request_token(params={"oauth_callback": "oob"}, header_auth=True)
        url = str(service.authorize_url).format(str(authenticator.identity), str(token))
        security = self.security(url, *args, **parameters, **kwargs)
        session = service.get_auth_session(token, secret, params={"oauth_verifier": security})
        session.headers.update({"consumerKey": authenticator.identity})
        return session

    @abstractmethod
    def security(self, url, *args, **kwargs): pass
    @property
    def urls(self): return type(self).__urls__


class WebReader(WebInterface):
    def __init__(self, *args, service=requests.Session, **kwargs):
        super().__init__(*args, **kwargs)
        self.__service = service
        self.__response = None
        self.__request = None

    def start(self):
        parameters = dict(account=self.account, authenticator=self.authenticator, delayer=self.delayer)
        self.session = self.service(**parameters)

    def stop(self):
        self.session.close()
        self.session = None
        self.response = None
        self.request = None

    @WebDelayer.register
    def load(self, url, *args, payload=None, **kwargs):
        address, params, headers = url
        parameters = dict(params=params, headers=headers)
        if bool(self.authenticator is not None): parameters.update({"header_auth": True})
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
    def service(self): return self.__service

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


