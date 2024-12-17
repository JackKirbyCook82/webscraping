# -*- coding: utf-8 -*-
"""
Created on Weds Jul 29 2020
@name:   WebURL Objects
@author: Jack Kirby Cook

"""

from abc import ABC, ABCMeta
from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebURL"]
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = "MIT License"


class WebURLMeta(ABCMeta):
    def __init__(cls, *args, **kwargs):
        super(WebURL, cls).__init__(*args, **kwargs)
        cls.__domain__ = kwargs.get("domain", getattr(cls, "__domain__", None))

    def __call__(cls, *args, **kwargs):
        path = cls.path(*args, **kwargs)
        parms = cls.parms(*args, **kwargs)
        assert isinstance(path, list) and isinstance(parms, dict)
        address = "/".join([cls.domain, "/".join(path)])
        parameters = dict(parms)
        instance = super(WebURL, cls).__call__(address, parameters)
        return instance

    @property
    def domain(cls): return cls.__domain__
    @staticmethod
    def path(*args, **kwargs): return []
    @staticmethod
    def parms(*args, **kwargs): return {}


class WebURL(ntuple("URL", "address parameters"), ABC, metaclass=WebURLMeta):
    def __str__(self):
        parameters = [[str(key), str(value)] for key, value in self.parameters.items()]
        parameters = [str("=").join(items) for items in parameters]
        parameters = str("&").join(parameters)
        return (str("?") + str(parameters)) if bool(parameters) else str("")



