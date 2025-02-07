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

from support.meta import SingletonMeta, RegistryMeta
from support.decorators import Wrapper

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebAuthorizer", "WebReader", "WebStatusError"]
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

class AuthenticationError(WebStatusError, register=401, title="Authentication"): pass
class ForbiddenRequestError(WebStatusError, register=403, title="ForbiddenRequest"): pass
class IncorrectRequestError(WebStatusError, register=404, title="IncorrectRequest"): pass
class GatewayError(WebStatusError, register=502, title="Gateway"): pass
class UnavailableError(WebStatusError, register=503, title="Unavailable"): pass


class WebAuthenticator(ntuple("Authenticator", "username password")): pass
class WebAuthorizer(object):
    def __init_subclass__(cls, *args, base, access, request, authorize, **kwargs):
        cls.__urls__ = {"base_url": base, "access_token_url": access, "request_token_url": request, "authorize_url": authorize}

    def __call__(self): return self.authorize()
    def __init__(self, *args, apikey, apicode, **kwargs):
        self.__apikey = apikey
        self.__apicode = apicode

    def service(self): return OAuth1Service(**self.urls, consumer_key=self.apikey, consumer_secret=self.apicode)
    def authorize(self):
        service = self.service()
        token, secret = service.get_request_token(params={"oauth_callback": "oob", "format": "json"})
        url = str(service.authorize_url).format(str(self.apikey), str(token))
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
    def urls(self): return type(self).__urls__
    @property
    def apicode(self): return self.__apicode
    @property
    def apikey(self): return self.__apikey


class WebDelayer(Wrapper):
    def wrapper(self, instance, *args, **kwargs):
        cls = type(instance)
        with cls.mutex: cls.wait(instance.delay)
        return self.function(instance, *args, **kwargs)


class WebReaderMeta(SingletonMeta):
    def __init__(cls, *args, **kwargs):
        cls.__mutex__ = multiprocessing.RLock()
        cls.__timer__ = None

    def wait(cls, delay):
        assert isinstance(delay, int)
        if bool(cls.timer) and bool(delay):
            elapsed = (Datetime.now() - cls.timer).total_seconds()
            sleep = max(delay - elapsed, 0)
            time.sleep(sleep)
        cls.timer = Datetime.now()

    @property
    def timer(cls): return cls.__timer__
    @timer.setter
    def timer(cls, timer): cls.__timer__ = timer

    @property
    def delay(cls): return cls.__delay__
    @property
    def mutex(cls): return cls.__mutex__


class WebReader(object, metaclass=WebReaderMeta):
    def __init_subclass__(cls, *args, **kwargs): pass

    def __bool__(self): return self.session is not None
    def __init__(self, *args, delay=10, authorizer=None, name, **kwargs):
        self.__mutex = multiprocessing.Lock()
        self.__authorizer = authorizer
        self.__delay = int(delay)
        self.__name = str(name)
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

    @WebDelayer
    def load(self, url, *args, payload=None, authenticate=None, headers={}, **kwargs):
        assert all([hasattr(url, attribute) for attribute in ("address", "parameters")])
        assert isinstance(authenticate, (WebAuthenticator, type(None)))
        address, parameters = url
        with self.mutex:
            authorized = self.authorizer is not None
            keywords = dict(params=parameters, headers=headers, header_auth=authorized)
            if authenticate is not None: keywords.update({"auth": tuple(authenticate)})
            if payload is None: response = self.session.get(str(address), **keywords)
            else: response = self.session.post(str(address), **keywords)
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
    def name(self): return self.__name



