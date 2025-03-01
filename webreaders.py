# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   WebReader Objects
@author: Jack Kirby Cook

"""

import time
import requests
import lxml.html
import webbrowser
import multiprocessing
import tkinter as tk
from rauth import OAuth1Service
from datetime import datetime as Datetime
from collections import namedtuple as ntuple

from support.meta import RegistryMeta
from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebAuthorizer", "WebAuthorizerAPI", "WebReader", "WebStatusError"]
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


class WebAuthorizerAPI(ntuple("AuthorizerAPI", "identity code")): pass
class WebAuthorizer(object):
    def __init__(self, *args, api, base, access, request, authorize, **kwargs):
        self.__urls = {"base_url": base, "access_token_url": access, "request_token_url": request, "authorize_url": authorize}
        self.__api = api

    def __call__(self):
        service = OAuth1Service(**self.urls, consumer_key=self.api.identity, consumer_secret=self.api.code)
        token, secret = service.get_request_token(params={"oauth_callback": "oob", "format": "json"})
        url = str(service.authorize_url).format(str(self.api.identity), str(token))
        webbrowser.open(str(url))
        security = self.prompt()
        session = service.get_auth_session(token, secret, params={"oauth_verifier": security})
        return session

    @staticmethod
    def prompt():
        window = tk.Tk()
        window.title("Enter Security Code:")
        variable = tk.StringVar()
        entry = tk.Entry(window, width=50, justify=tk.CENTER, textvariable=variable)
        entry.focus_set()
        entry.grid(padx=10, pady=10)
        button = tk.Button(window, text="Submit", command=window.destroy)
        button.grid(row=0, column=1, padx=10, pady=10)
        window.mainloop()
        return str(variable.get())

    @property
    def urls(self): return self.__urls
    @property
    def api(self): return self.__api


class WebReader(Logging):
    def __bool__(self): return self.session is not None
    def __init__(self, *args, delay=2, authorizer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__mutex = multiprocessing.Lock()
        self.__authorizer = authorizer
        self.__delay = int(delay)
        self.__timer = None
        self.__session = None
        self.__response = None
        self.__request = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.stop()

    def start(self):
        if self.authorizer is not None: self.session = self.authorizer()
        else: self.session = requests.Session()

    def stop(self):
        self.session.close()
        self.session = None
        self.response = None
        self.request = None

    def load(self, url, *args, payload=None, **kwargs):
        address, parameters, headers = url
        authorized = bool(self.authorizer is not None)
        keywords = dict(params=parameters, headers=headers)
        if authorized: keywords["header_auth"] = authorized
        with self.mutex:
            elapsed = (Datetime.now() - self.timer).total_seconds() if bool(self.timer) else self.delay
            wait = max(self.delay - elapsed, 0) if bool(self.delay) else 0
            if bool(wait):
                self.console(f"{elapsed:.02f} sec", title="Waiting")
                time.sleep(wait)
            if payload is None: response = self.session.get(str(address), data=payload, **keywords)
            else: response = self.session.post(str(address), **keywords)
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
    def authorizer(self): return self.__authorizer
    @property
    def delay(self): return self.__delay
    @property
    def mutex(self): return self.__mutex

    @property
    def timer(self): return self.__timer
    @timer.setter
    def timer(self, timer): self.__timer = timer




