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
        path = getattr(cls, "attributes", {}).get("path", []) + kwargs.get("path", [])
        parms = getattr(cls, "attributes", {}).get("parms", {}) | kwargs.get("parms", {})
        cls.__domain__ = kwargs.get("domain", getattr(cls, "__domain__", None))
        cls.__attributes__ = dict(path=path, parms=parms)

    def __call__(cls, *args, **kwargs):
        path = cls.path(*args, **kwargs)
        parms = cls.parms(*args, **kwargs)
        assert isinstance(path, list) and isinstance(parms, dict)
        address = "/".join([cls.domain, "/".join(path)])
        parameters = dict(parms)
        instance = super(WebURLMeta, cls).__call__(address, parameters)
        return instance

    @abstractmethod
    def path(cls, *args, **kwargs): return []
    @abstractmethod
    def parms(cls, *args, **kwargs): return {}

    @property
    def attributes(cls): return cls.__attributes__
    @property
    def domain(cls): return cls.__domain__
    @property
    def name(cls): return cls.__name__


class WebURL(ntuple("URL", "address parameters"), ABC, metaclass=WebURLMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self):
        parameters = [list(map(str, parameter)) for parameter in self.parameters.items()]
        parameters = str("&").join([str("=").join(parameter) for parameter in parameters])
        parameters = (str("?") + str(parameters)) if bool(parameters) else str("")
        return str(self.address) + str(parameters)





















