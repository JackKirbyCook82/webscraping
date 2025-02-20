# -*- coding: utf-8 -*-
"""
Created on Weds Jul 29 2020
@name:   WebURL Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple
from collections import OrderedDict as ODict

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebURL"]
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = "MIT License"


class WebAddress(ntuple("Address", "domain path")):
    def __str__(self): return "/".join([self.domain, "/".join(self.path)])

class WebParameters(ODict):
    def __str__(self):
        parameters = [list(map(str, parameter)) for parameter in self.items()]
        parameters = str("&").join([str("=").join(parameter) for parameter in parameters])
        return parameters

class Website(ntuple("URL", "address parameters headers")):
    def __str__(self):
        parameters = (str("?") + str(self.parameters)) if bool(self.parameters) else str("")
        return str(self.address) + str(parameters)


class WebURL(object):
    def __init_subclass__(cls, *args, **kwargs):
        domain = kwargs.get("domain", getattr(cls, "attributes", {}).get("domain", None))
        path = getattr(cls, "attributes", {}).get("path", []) + kwargs.get("path", [])
        parameters = getattr(cls, "attributes", {}).get("parameters", {}) | kwargs.get("parameters", {})
        headers = getattr(cls, "attributes", {}).get("headers", {}) | kwargs.get("headers", {})
        cls.attributes = dict(domain=domain, path=path, parameters=parameters, headers=headers)

    def __new__(cls, *args, **kwargs):
        domain = cls.attributes["domain"]
        path = cls.attributes["path"] + cls.path(*args, **kwargs)
        parameters = cls.attributes["parameters"] | cls.parameters(*args, **kwargs)
        headers = cls.attributes["headers"] | cls.headers(*args, **kwargs)
        address = WebAddress(domain, path)
        parameters = WebParameters(parameters.items())
        return Website(address, parameters, headers)

    @staticmethod
    def path(*args, **kwargs): return []
    @staticmethod
    def parameters(*args, **kwargs): return {}
    @staticmethod
    def headers(*args, **kwargs): return {}






