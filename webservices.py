# -*- coding: utf-8 -*-
"""
Created on Fri May 30 2025
@name:   WebService Objects
@author: Jack Kirby Cook

"""

from rauth import OAuth1Service
from abc import ABC, abstractmethod

from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebService"]
__copyright__ = "Copyright 2025, Jack Kirby Cook"
__license__ = "MIT License"


class WebService(Logging, ABC):
    def __init_subclass__(cls, *args, base, access, request, authorize, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.__weburl__ = {"authorize_url": authorize, "request_token_url": request, "access_token_url": access, "base_url": base}

    def __init__(self, *args, webapi, **kwargs):
        super().__init__(*args, **kwargs)
        self.__webapi = webapi

    def service(self, *args, **kwargs):
        service = OAuth1Service(consumer_key=self.webapi.identity, consumer_secret=self.webapi.code, **self.weburl)
        token, secret = service.get_request_token(params={"oauth_callback": "oob", "format": "json"})
        url = str(service.authorize_url).format(str(self.webapi.identity), str(token))
        security = self.security(url, *args, **kwargs)
        session = service.get_auth_session(token, secret, params={"oauth_verifier": security})
        return session

    @abstractmethod
    def security(self, url, *args, **kwargs): pass

    @property
    def weburl(self): return type(self).__weburl__
    @property
    def webapi(self): return self.__webapi



