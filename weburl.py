# -*- coding: utf-8 -*-
"""
Created on Weds Jul 29 2020
@name:   WebURL Objects
@author: Jack Kirby Cook

"""

from functools import reduce
from operator import
from collections import namedtuple as ntuple
from collections import OrderedDict as ODict

from support.meta import TreeMeta
from support.trees import Node

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebURL", "WebPayload"]
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = "MIT License"


class WebAddress(ntuple("Address", "domain path")):
    def __str__(self): return "/".join([self.domain, "/".join(self.path)])

class WebParameters(ODict):
    def __str__(self):
        parameters = [list(map(str, parameter)) for parameter in self.items()]
        parameters = str("&").join([str("=").join(parameter) for parameter in parameters])
        return parameters

class WebURLBase(ntuple("URL", "address parameters headers")):
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
        return WebURLBase(address, parameters, headers)

    @staticmethod
    def path(*args, **kwargs): return []
    @staticmethod
    def parameters(*args, **kwargs): return {}
    @staticmethod
    def headers(*args, **kwargs): return {}


class WebPayloadErrorMeta(type):
    def __init__(cls, *args, **kwargs):
        super(WebPayloadErrorMeta, cls).__init__(*args, **kwargs)
        cls.__title__ = kwargs.get("title", getattr(cls, "__title__", None))

    @property
    def title(cls): return cls.__title__
    @property
    def name(cls): return cls.__name__

class WebPayloadError(Exception, metaclass=WebPayloadErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass

class WebPayloadMissingError(WebPayloadError, title="Missing"): pass
class WebPayloadMultipleError(WebPayloadError, title="Multiple"): pass


class WebPayloadBase(Node):
    def __init__(self, contents, *args, **kwargs):
        assert isinstance(contents, dict)
        super().__init__(*args, **kwargs)
        self.__contents = contents


class WebPayload(TreeMeta):
    def __init__(cls, *args, **kwargs):
        super(WebPayload, cls).__init__(*args, **kwargs)
        cls.__parameters__ = getattr(cls, "__parameters__", {}) | kwargs.get("parameters", {})
        cls.__arguments__ = getattr(cls, "__arguments__", []) | kwargs.get("arguments", [])
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))

    def __call__(cls, sources, *args, **kwargs):
        assert isinstance(sources, (dict, list))
        sources = [dict(sources)] if isinstance(sources, dict) else list(sources)
        if not bool(sources) and not cls.optional: raise WebPayloadMissingError()
        if len(sources) > 1 and not cls.multiple: raise WebPayloadMultipleError()
        arguments = lambda source: reduce(lambda lead, lag: lead | lag, [getattr(cls, argument)(*args, **source, **kwargs) for argument in cls.arguments])
        initialize = lambda source: super(WebPayload, cls).__call__(arguments(source) | cls.parameters, *args, **kwargs)
        instances = list(map(initialize, sources))
        if bool(cls.multiple): return list(instances)
        else: return instances[0] if bool(instances) else None

    @property
    def parameters(cls): return cls.__parameters__
    @property
    def arguments(cls): return cls.__arguments__
    @property
    def optional(cls): return cls.__optional__
    @property
    def multiple(cls): return cls.__multiple__
    @property
    def locator(cls): return cls.__locator__







