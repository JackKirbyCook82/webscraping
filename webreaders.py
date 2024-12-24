# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   WebReader Objects
@author: Jack Kirby Cook

"""

import time
import logging
import requests
import lxml.html
import webbrowser
import multiprocessing
import tkinter as tk
from rauth import OAuth1Service
from datetime import datetime as Datetime
from collections import namedtuple as ntuple
from collections import OrderedDict as ODict

from support.decorators import Wrapper, TypeDispatcher
from support.meta import SingletonMeta, RegistryMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebAuthorizer", "WebReader", "WebStatusError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebStatusErrorMeta(RegistryMeta):
    def __init__(cls, name, bases, attrs, *args, statuscode=None, title=None, **kwargs):
        assert str(name).endswith("Error") and isinstance(statuscode, (int, type(None)))
        parameters = dict(register=statuscode) if bool(statuscode) else {}
        super(WebStatusErrorMeta, cls).__init__(name, bases, attrs, *args, **parameters, **kwargs)
        if not any([type(base) is WebStatusErrorMeta for base in bases]):
            return
        cls.__statuscode__ = statuscode
        cls.__logger__ = __logger__
        cls.__title__ = title

    def __call__(cls, feed):
        logger, statuscode, title, name = cls.__logger__, cls.__statuscode__, cls.__title__, cls.__name__
        instance = super(WebStatusErrorMeta, cls).__call__(name, feed, statuscode)
        logger.info(f"{title}: {repr(instance.feed)}")
        logger.info(str(instance.url))
        return instance


class WebStatusError(Exception, metaclass=WebStatusErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return f"{self.name}|{repr(self.feed)}[{str(self.statuscode)}]\n{str(self.url)}"
    def __init__(self, name, feed, statuscode):
        self.__statuscode = statuscode
        self.__url = feed.url
        self.__feed = feed
        self.__name = name

    @property
    def statuscode(self): return self.__statuscode
    @property
    def feed(self): return self.__feed
    @property
    def name(self): return self.__name
    @property
    def url(self): return self.__url


class AuthenticationError(WebStatusError, statuscode=401, title="Authentication"): pass
class ForbiddenRequestError(WebStatusError, statuscode=403, title="ForbiddenRequest"): pass
class IncorrectRequestError(WebStatusError, statuscode=404, title="IncorrectRequest"): pass
class GatewayError(WebStatusError, statuscode=502, title="Gateway"): pass
class UnavailableError(WebStatusError, statuscode=503, title="Unavailable"): pass


class WebAuthenticator(ntuple("Authenticator", "username password")): pass
class WebAuthorizer(object):
    def __init_subclass__(cls, *args, base, access, request, authorize, **kwargs):
        cls.__urls__ = {"base_url": base, "access_token_url": access, "request_token_url": request, "authorize_url": authorize}

    def __repr__(self): return f"{self.name}"
    def __call__(self): return self.authorize()
    def __init__(self, *args, apikey, apicode, **kwargs):
        self.__name = kwargs.get("name", self.__class__.__name__)
        self.__apikey = apikey
        self.__apicode = apicode

    def service(self):
        return OAuth1Service(**self.urls, consumer_key=self.apikey, consumer_secret=self.apicode)

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
    @property
    def name(self): return self.__name


class WebDelayer(Wrapper):
    def wrapper(self, instance, *args, **kwargs):
        cls = type(instance)
        with cls.mutex: cls.wait(instance.delay)
        return self.function(instance, *args, **kwargs)


class WebReaderMeta(SingletonMeta):
    def __init__(cls, *args, **kwargs):
        cls.__mutex__ = multiprocessing.RLock()
        cls.__timer__ = None

    def wait(cls, delay=0):
        if bool(cls.timer) and bool(delay):
            seconds = (Datetime.now() - cls.timer).total_seconds()
            sleep = max(delay - seconds, 0)
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

    def __repr__(self): return f"{self.name}|Session"
    def __bool__(self): return self.session is not None

    def __init__(self, *args, delay=10, authorizer=None, **kwargs):
        self.__name = kwargs.get("name", self.__class__.__name__)
        self.__mutex = multiprocessing.Lock()
        self.__authorizer = authorizer
        self.__delay = int(delay)
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

    @TypeDispatcher(locator=0)
    def load(self, url, *args, **kwargs): pass

    @load.register(tuple)
    def load(self, url, *args, payload=None, headers={}, authenticate=None, **kwargs):
        address, parameters = url
        parameters = parameters.items()
        parameters = ODict(parameters) | kwargs.get("parameters", {})
        keywords = dict(payload=payload, headers=headers, authenticate=authenticate)
        self.method(address, parameters=parameters, **keywords)

    @load.register(str)
    def load(self, url, *args, payload=None, headers={}, authenticate=None, **kwargs):
        try: address, parameters = str(url).split("?")
        except ValueError: address, parameters = str(url), str("")
        parameters = [str(parameter).split("=") for parameter in str(parameters).split("&") if bool(parameter)]
        parameters = ODict(parameters) | kwargs.get("parameters", {})
        keywords = dict(payload=payload, headers=headers, authenticate=authenticate)
        self.method(address, parameters=parameters, **keywords)

    def method(self, address, payload=None, parameters={}, headers={}, authenticate=None):
        assert isinstance(authenticate, (WebAuthenticator, type(None)))
        keywords = dict(parameters=parameters, headers=headers, authenticate=authenticate)
        with self.mutex:
            if payload is None: response = self.get(address, **keywords)
            else: response = self.post(address, payload, **keywords)
            self.request = response.request
            self.response = response
        try: raise WebStatusError[int(self.response.status_code)](self)
        except KeyError: pass

    @WebDelayer
    def get(self, address, parameters={}, headers={}, authenticate=None):
        assert isinstance(address, str) and isinstance(parameters, dict)
        assert "?" not in str(address) if bool(parameters) else True
        authorized = self.authorizer is not None
        keywords = dict(params=parameters, headers=headers, header_auth=authorized)
        if authenticate is not None: keywords.update({"auth": tuple(authenticate)})
        response = self.session.get(address, **keywords)
        return response

    @WebDelayer
    def post(self, address, payload, parameters={}, headers={}, authenticate=None):
        assert isinstance(address, str) and isinstance(parameters, dict)
        assert "?" not in str(address) if bool(parameters) else True
        authorized = self.authorizer is not None
        keywords = dict(data=payload, params=parameters, headers=headers, header_auth=authorized)
        if authenticate is not None: keywords.update({"auth": tuple(authenticate)})
        response = self.session.post(address, **keywords)
        return response

    @property
    def pretty(self): return lxml.etree.tostring(self.html, pretty_print=True, encoding="unicode")
    @property
    def html(self): return lxml.html.fromstring(self.response.text)
    @property
    def json(self): return self.response.json()
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


