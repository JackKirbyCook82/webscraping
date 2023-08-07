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
import PySimpleGUI as gui
from rauth import OAuth1Service
from collections import OrderedDict as ODict

from utilities.meta import DelayerMeta

from webscraping.weberrors import WebStatusError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebAuthorizer", "WebReader"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


LOGGER = logging.getLogger(__name__)


class WebAuthorizer(object):
    def __init_subclass__(cls, *args, base, access, request, authorize, **kwargs):
        cls.__urls__ = {"base_url": base, "access_token_url": access, "request_token_url": request, "authorize_url": authorize}

    def __repr__(self): return "{}".format(self.name)
    def __call__(self): return self.authorize()
    def __init__(self, *args, apikey, apicode, **kwargs):
        self.__name = kwargs.get("name", self.__class__.__name__)
        self.__apikey = apikey
        self.__apicode = apicode

    def service(self):
        return OAuth1Service(**self.urls, consumer_key=self.apikey, consumer_secret=self.apicode)

    def prompt(self, url):
        webbrowser.open(str(url))
        layout = [[gui.Text("Enter Security Code:", size=(30, 1))], [gui.Input()], [gui.Submit(), gui.Cancel()]]
        window = gui.Window(repr(self), layout)
        security = window.read()[1][0]
        window.close()
        return security

    def authorize(self):
        service = self.service()
        token, secret = service.get_request_token(params={"oauth_callback": "oob", "format": "json"})
        url = str(service.authorize_url).format(str(self.apikey), str(token))
        security = self.prompt(url)
        session = service.get_auth_session(token, secret, params={"oauth_verifier": security})
        return session

    @property
    def urls(self): return self.__class__.__urls__
    @property
    def name(self): return self.__name
    @property
    def apikey(self): return self.__apikey
    @property
    def apicode(self): return self.__apicode


class WebReader(object, metaclass=DelayerMeta):
    def __repr__(self): return "{}|{}".format(self.name, "Session")
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
    def load(self, url, *args, params={}, payload=None, headers={}, **kwargs):
        url, params = self.urlparse(url, params)
        with self.mutex:
            if payload is None:
                response = self.get(url, params=params, headers=headers)
            else:
                response = self.post(url, payload, params=params, headers=headers)
            self.request = response.request
            self.response = response
            try:
                raise WebStatusError[int(self.response.status_code)](self)
            except KeyError:
                pass

    def get(self, url, params={}, headers={}):
        assert "?" not in str(url) if bool(params) else True
        authorized = self.authorizer is not None
        response = self.session.get(url, params=params, headers=headers, header_auth=authorized)
        return response

    def post(self, url, payload, params={}, headers={}):
        assert "?" not in str(url) if bool(params) else True
        authorized = self.authorizer is not None
        response = self.session.post(url, data=payload, params=params, headers=headers, header_auth=authorized)
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


