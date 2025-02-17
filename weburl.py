# -*- coding: utf-8 -*-
"""
Created on Weds Jul 29 2020
@name:   WebURL Objects
@author: Jack Kirby Cook

"""

from abc import ABC, ABCMeta, abstractmethod
from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebURL"]
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = "MIT License"


class WebURLMeta(ABCMeta):
    def __init__(cls, *args, **kwargs):
        super(WebURLMeta, cls).__init__(*args, **kwargs)
        domain = kwargs.get("authenticate", getattr(cls, "domain", {}).get("domain", None))
        path = getattr(cls, "attributes", {}).get("path", []) + kwargs.get("path", [])
        parameters = getattr(cls, "attributes", {}).get("parameters", {}) | kwargs.get("parameters", {})
        headers = getattr(cls, "attributes", {}).get("headers", {}) | kwargs.get("headers", {})
        cls.__attributes__ = dict(domain=domain, path=path, parameters=parameters, headers=headers)

    def __call__(cls, *args, authenticate=None, **kwargs):
        path = cls.attributes["path"] + cls.path(*args, **kwargs)
        parameters = cls.attributes["parameters"] | cls.parameters(*args, **kwargs)
        headers = cls.attributes["headers"] | cls.headers(*args, **kwargs)
        assert isinstance(path, list) and isinstance(parameters, dict)
        address = "/".join([cls.attributes["domain"], "/".join(path)])
        instance = super(WebURLMeta, cls).__call__(address, parameters, headers, authenticate)
        return instance

    @staticmethod
    def path(*args, **kwargs): return []
    @staticmethod
    def parameters(*args, **kwargs): return {}
    @staticmethod
    def headers(*args, **kwargs): return {}

    @property
    def attributes(cls): return cls.__attributes__
    @property
    def name(cls): return cls.__name__


class WebURL(ntuple("URL", "address parameters headers authenticate"), ABC, metaclass=WebURLMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self):
        parameters = [list(map(str, parameter)) for parameter in self.parameters.items()]
        parameters = str("&").join([str("=").join(parameter) for parameter in parameters])
        parameters = (str("?") + str(parameters)) if bool(parameters) else str("")
        return str(self.address) + str(parameters)





















