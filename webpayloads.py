# -*- coding: utf-8 -*-
"""
Created on Tues May 19 2026
@name:   WebPayload Objects
@author: Jack Kirby Cook

"""

from abc import ABC, ABCMeta
from collections import OrderedDict as ODict

from support.meta import AttributeMeta, TreeMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebPayload", "WebPayloadError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"

class WebPayloadError(Exception): pass
class WebPayloadMissingError(WebPayloadError): pass
class WebPayloadSingleError(WebPayloadError): pass
class WebPayloadMultipleError(WebPayloadError): pass
class WebPayloadTypingError(WebPayloadError): pass


class WebPayloadMeta(AttributeMeta, TreeMeta, ABCMeta):
    def __init__(cls, *args, **kwargs):
        super(WebPayloadMeta, cls).__init__(*args, **kwargs)
        cls.__mapping__ = getattr(cls, "__mapping__", {}) | kwargs.get("mapping", {})
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))

    def __call__(cls, sources, *args, **kwargs):
        if cls.multiple:
            if not isinstance(sources, list): raise WebPayloadSingleError()
            if not bool(sources) and not cls.optional: raise WebPayloadMissingError()
            instances = []
            for source in sources:
                children = {dependent.locator: dependent(source, *args, **kwargs) for dependent in cls.dependents}
                attributes = dict(children=children) | cls.mapping
                instance = super(WebPayloadMeta, cls).__call__(source, *args, **attributes, **kwargs)
                instances.append(instance)
            return instances
        else:
            if isinstance(sources, list): raise WebPayloadMultipleError()
            if not bool(sources) and not cls.optional: raise WebPayloadMissingError()
            source = sources
            children = {dependent.locator: dependent(source, *args, **kwargs) for dependent in cls.dependents}
            attributes = dict(children=children)
            instance = super(WebPayloadMeta, cls).__call__(source, *args, **attributes, **kwargs)
            return instance

    @property
    def optional(cls): return cls.__optional__
    @property
    def multiple(cls): return cls.__multiple__
    @property
    def mapping(cls): return cls.__mapping__
    @property
    def locator(cls): return cls.__locator__


class WebPayload(ABC, metaclass=WebPayloadMeta):
    pass


class WebPayloadMapping(WebPayload, attribute="Mapping"):
    pass


class WebPayloadValue(WebPayload, attribute="Value"):
    pass



