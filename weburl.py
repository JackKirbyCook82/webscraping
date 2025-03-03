# -*- coding: utf-8 -*-
"""
Created on Weds Jul 29 2020
@name:   WebURL Objects
@author: Jack Kirby Cook

"""

import json
from functools import reduce
from collections import Mapping
from collections import namedtuple as ntuple
from collections import OrderedDict as ODict

from support.meta import TreeMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebURL", "WebPayload", "WebField"]
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = "MIT License"


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


class WebAddress(ntuple("Address", "domain path")):
    def __str__(self): return "/".join([self.domain, "/".join(self.path)])

class WebParameters(ODict):
    def __str__(self):
        parameters = [list(map(str, parameter)) for parameter in self.items()]
        parameters = str("&").join([str("=").join(parameter) for parameter in parameters])
        return parameters

class WebCURL(ntuple("CURL", "address parameters headers")):
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
        return WebCURL(address, parameters, headers)

    @staticmethod
    def path(*args, **kwargs): return []
    @staticmethod
    def parameters(*args, **kwargs): return {}
    @staticmethod
    def headers(*args, **kwargs): return {}


class WebField(ntuple("Field", "locator formatter")):
    def __call__(self, source, *args, **kwargs):
        return {self.locator: self.formatter(source)}


class WebPayloadMeta(TreeMeta, ABCMeta):
    def __new__(mcs, name, bases, attrs, *args, **kwargs):
        exclude = [key for key, value in attrs.items() if isinstance(value, WebField)]
        attrs = {key: value for key, value in attrs.items() if key not in exclude}
        cls = super(WebPayloadMeta, mcs).__new__(mcs, name, bases, attrs, *args, **kwargs)
        return cls

    def __init__(cls, name, bases, attrs, *args, dependents=[], **kwargs):
        super(WebPayloadMeta, cls).__init__(name, bases, attrs, *args, dependents=dependents, **kwargs)
        fields = {key: field for key, field in attrs.items() if isinstance(field, WebField)}
        cls.__invariant__ = getattr(cls, "__invariant__", {}) | kwargs.get("fields", {})
        cls.__variant__ = getattr(cls, "__variant__", {}) | dict(fields)
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__"), None)

    def __call__(cls, sources, *args, **kwargs):
        sources = list(sources) if isinstance(sources, list) else [sources]
        if not bool(sources) and not cls.optional: raise WebPayloadMissingError()
        if len(sources) > 1 and not cls.multiple: raise WebPayloadMultipleError()
        function = lambda attribute, dependent, source: dependent(getattr(source, attribute), *args, **kwargs)
        childrens = [[function(key, dependent, source) for key, dependent in cls.dependents.items()] for source in sources]
        childrens = [reduce(lambda lead, lag: lead | lag, children) for children in childrens]
        fields = [[field(source, *args, **kwargs) for field in cls.variant.values()] for source in sources]
        fields = [reduce(lambda lead, lag: lead | lag, contents) for contents in fields]
        fields = [dict(contents) | dict(cls.invariant) for contents in fields]
        initialize = lambda contents, children: super(WebPayloadMeta, cls).__call__(contents | children, *args, **kwargs)
        instances = [initialize(contents, children) for contents, children in zip(fields, childrens)]
        if bool(cls.multiple): return {cls.locator: list(instances)}
        else: return {cls.locator: instances[0]} if bool(instances) else {}

    @property
    def optional(cls): return cls.__optional__
    @property
    def multiple(cls): return cls.__multiple__
    @property
    def locator(cls): return cls.__locator__
    @property
    def invariant(cls): return cls.__invariant__
    @property
    def variant(cls): return cls.__variant__


class WebPayload(Mapping, metaclass=WebPayloadMeta):
    def __init__(self, contents, *args, **kwargs):
        assert isinstance(contents, dict)
        self.__contents = contents

    def __getitem__(self, key): return self.contents[key]
    def __hash__(self): return hash(self.contents.iteritems())
    def __iter__(self): return iter(self.contents.items())
    def __len__(self): return len(self.contents)
    def __str__(self): return str(self.string)

    @property
    def string(self): return json.dumps(self.contents, sort_keys=False, indent=3, separators=(',', ' : '))
    @property
    def json(self): return json.dumps(self.contents)

    @property
    def contents(self): return self.__contents





