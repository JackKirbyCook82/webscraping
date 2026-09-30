# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 2026
@name:   WebURL Objects
@author: Jack Kirby Cook
@file:   webscraping\weburl.py

"""

from dataclasses import dataclass
from collections import OrderedDict as ODict

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebURL"]
__copyright__ = "Copyright 2026, Jack Kirby Cook"
__license__ = "MIT License"


@dataclass(frozen=True)
class WebAddress:
    domain: str; path: list

    def __str__(self):
        return "/".join([self.domain, "/".join(self.path)])


class WebHeaders(ODict): pass
class WebParameters(ODict):
    def __str__(self):
        parameters = [list(map(str, parameter)) for parameter in self.items()]
        return str("&").join([str("=").join(parameter) for parameter in parameters])


@dataclass(frozen=True)
class WebCURL:
    address: WebAddress; parameters: WebParameters | dict; headers: WebHeaders | dict

    def __iter__(self):
        yield self.address; yield self.parameters; yield self.headers

    def __str__(self):
        parameters = (str("?") + str(self.parameters)) if bool(self.parameters) else str("")
        return str(self.address) + str(parameters)


class WebURLMeta(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        domain = kwargs.get("domain", getattr(cls, "attributes", {}).get("domain", None))
        path = getattr(cls, "attributes", {}).get("path", []) + kwargs.get("path", [])
        parameters = getattr(cls, "attributes", {}).get("parameters", {}) | kwargs.get("parameters", {})
        headers = getattr(cls, "attributes", {}).get("headers", {}) | kwargs.get("headers", {})
        cls.attributes = dict(domain=domain, path=path, parameters=parameters, headers=headers)

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        domain = cls.attributes["domain"]
        path = cls.attributes["path"] + instance.path(*args, **kwargs)
        parameters = cls.attributes["parameters"] | instance.parameters(*args, **kwargs)
        headers = cls.attributes["headers"] | instance.headers(*args, **kwargs)
        address = WebAddress(domain, path)
        parameters = WebParameters(parameters.items())
        return WebCURL(address, parameters, headers)


class WebURL(object, metaclass=WebURLMeta):
    def __new__(cls, *args, **kwargs): return super().__new__(cls)
    def __init__(self, *args, **kwargs): super().__init__()

    @staticmethod
    def path(*args, **kwargs): return []
    @staticmethod
    def parameters(*args, **kwargs): return {}
    @staticmethod
    def headers(*args, **kwargs): return {}

