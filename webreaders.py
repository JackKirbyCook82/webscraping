# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   WebReader Objects
@author: Jack Kirby Cook

"""

import logging
import requests
import lxml.html
import webbrowser
import multiprocessing
import tkinter as tk
from rauth import OAuth1Service
from collections import namedtuple as ntuple
from collections import OrderedDict as ODict

from support.meta import DelayerMeta, RegistryMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebAuthorizer", "WebReader", "WebStatusError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebStatusErrorMeta(RegistryMeta):
    def __init__(cls, name, bases, attrs, *args, statuscode=None, **kwargs):
        assert str(name).endswith("Error")
        assert isinstance(statuscode, (int, type(None)))
        super(WebStatusErrorMeta, cls).__init__(name, bases, attrs, *args, register=statuscode, **kwargs)
        if not any([type(base) is WebStatusErrorMeta for base in bases]):
            return
        cls.__statuscode__ = statuscode

    def __call__(cls, *args, **kwargs):
        instance = super(WebStatusErrorMeta, cls).__call__(*args, **kwargs)
        __logger__.info(str(instance.name).replace("Error", f": {repr(instance.feed)}"))
        __logger__.info(str(instance.url))
        return instance


class WebStatusError(Exception, metaclass=WebStatusErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return f"{self.name}|{repr(self.feed)}[{str(self.statuscode)}]\n{str(self.url)}"
    def __init__(self, feed):
        self.__statuscode = self.__class__.__statuscode__
        self.__name = self.__class__.__name__
        self.__url = feed.url
        self.__feed = feed

    @property
    def statuscode(self): return self.__statuscode
    @property
    def feed(self): return self.__feed
    @property
    def name(self): return self.__name
    @property
    def url(self): return self.__url


class AuthenticationError(WebStatusError, statuscode=401): pass
class ForbiddenRequestError(WebStatusError, statuscode=403): pass
class IncorrectRequestError(WebStatusError, statuscode=404): pass
class GatewayError(WebStatusError, statuscode=502): pass
class UnavailableError(WebStatusError, statuscode=503): pass


class WebAuthenticator(ntuple("Authenticator", "username password")): pass
class WebSecurity(object):
    def __str__(self): return str(self.variable) if isinstance(self.variable, str) else ""
    def __init__(self, variable): self.variable = variable
    def __call__(self, variable): self.variable = self.variable.get()


class WebAuthorizer(object):
    def __init_subclass__(cls, *args, base, access, request, authorize, **kwargs):
        cls.__urls__ = {"base_url": base, "access_token_url": access, "request_token_url": request, "authorize_url": authorize}

    def __repr__(self): return "{}".format(self.name)
    def __call__(self): return self.authorize()
    def __init__(self, *args, apikey, apicode, **kwargs):
        self.__name = kwargs.get("name", self.__class__.__name__)
        self.__urls = self.__class__.__urls__
        self.__apikey = apikey
        self.__apicode = apicode

    @staticmethod
    def prompt():
        window = tk.Tk()
        window.title("Enter Security Code:")
        variable = tk.StringVar()
        entry = tk.Entry(window, width=50, justify=tk.CENTER, textvariable=variable)
        entry.focus_set()
        entry.grid(padx=10, pady=10)
        security = WebSecurity(variable)
        button = tk.Button(window, text="Submit", command=security)
        button.grid(row=0, column=1, padx=10, pady=10)
        window.mainloop()
        return str(security)

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

    @property
    def apicode(self): return self.__apicode
    @property
    def apikey(self): return self.__apikey
    @property
    def urls(self): return self.__urls
    @property
    def name(self): return self.__name


class WebReader(object, metaclass=DelayerMeta):
    def __init_subclass__(cls, *args, **kwargs): pass

    def __repr__(self): return f"{self.name}|Session"
    def __init__(self, *args, authorizer=None, **kwargs):
        self.__name = kwargs.get("name", self.__class__.__name__)
        self.__mutex = multiprocessing.Lock()
        self.__authorizer = authorizer
        self.__session = None
        self.__response = None
        self.__request = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.stop()

    def start(self):
        if self.authorizer is not None:
            self.session = self.authorizer()
        else:
            self.session = requests.Session()

    def stop(self):
        self.session.close()

    @DelayerMeta.delayer
    def load(self, url, *args, params={}, payload=None, headers={}, auth=None, **kwargs):
        assert isinstance(auth, (WebAuthenticator, type(None)))
        url, params = self.urlparse(url, params)
        with self.mutex:
            if payload is None:
                response = self.get(url, params=params, headers=headers, auth=auth)
            else:
                response = self.post(url, payload, params=params, headers=headers, auth=auth)
            self.request = response.request
            self.response = response
            try:
                raise WebStatusError[int(self.response.status_code)](self)
            except KeyError:
                pass

    def get(self, url, params={}, headers={}, auth=None):
        assert "?" not in str(url) if bool(params) else True
        authorized = self.authorizer is not None
        parameters = dict(params=params, headers=headers, header_auth=authorized)
        if auth is not None:
            parameters.update({"auth": tuple(auth)})
        response = self.session.get(url, **parameters)
        return response

    def post(self, url, payload, params={}, headers={}, auth=None):
        assert "?" not in str(url) if bool(params) else True
        authorized = self.authorizer is not None
        parameters = dict(data=payload, params=params, headers=headers, header_auth=authorized)
        if auth is not None:
            parameters.update({"auth": tuple(auth)})
        response = self.session.post(url, **parameters)
        return response

    @staticmethod
    def urlparse(url, params={}):
        if not bool(params) or "?" not in str(url):
            return url, params
        url, query = str(url).split("?")
        query = ODict([tuple(str(pair).split("=")) for pair in str(query).split("&")])
        params.update(query)
        return url, params

    @property
    def mutex(self): return self.__mutex
    @property
    def authorizer(self): return self.__authorizer
    @property
    def name(self): return self.__name

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
    def url(self): return self.response.url
    @property
    def pretty(self): return lxml.etree.tostring(self.html, pretty_print=True, encoding="unicode")
    @property
    def html(self): return lxml.html.fromstring(self.response.text)
    @property
    def text(self): return self.response.text
    @property
    def json(self): return self.response.json()


