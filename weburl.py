# -*- coding: utf-8 -*-
"""
Created on Weds Jul 29 2020
@name:   WebURL Objects
@author: Jack Kirby Cook

"""

from abc import ABCMeta, abstractmethod
from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebURL"]
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = "MIT License"


class WebURLBase(ntuple("URL", "address query")):
    def __str__(self):
        query = ("?" + "&".join(["=".join([str(key), str(value)]) for key, value in self.query.items()])) if self.query else ""
        return str(self.address) + str(query)


class WebURL(ABCMeta):
    def __new__(mcs, *args, **kwargs):
        cls = super(WebURL, mcs).__new__(mcs, "WebURLBase", (WebURLBase,), {})
        self = cls(*args, **kwargs)
        return self

    def __call__(cls, *args, **kwargs):
        domain = cls.domain(*args, **kwargs)
        path = cls.path(*args, **kwargs)
        params = cls.parms(*args, **kwargs)
        assert isinstance(domain, str) and isinstance(path, str)
        assert isinstance(params, dict)
        address = (str(domain) + str(path)) if path is not None else str(domain)
        instance = WebURLBase(address, params)
        return instance

    @abstractmethod
    def domain(cls, *args, **kwargs): pass
    def path(cls, *args, **kwargs): return ""
    def parms(cls, *args, **kwargs): return {}





