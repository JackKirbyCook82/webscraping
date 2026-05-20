# -*- coding: utf-8 -*-
"""
Created on Tues May 19 2026
@name:   WebPayload Objects
@author: Jack Kirby Cook

"""

from abc import ABC, ABCMeta

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


class WebPayloadMeta(AttributeMeta, TreeMeta, ABCMeta):
    def __init__(cls, *args, **kwargs):
        function = lambda name, base, locator: type(repr(cls) + str(name).title(), tuple([base]), dict(), locator=locator)
        modified = [function(key, cls.dependents[key], locator) for key, locator in kwargs.get("locators", {}).items()]
        dependents = list(kwargs.pop("dependents", [])) + list(modified)
        super(WebPayloadMeta, cls).__init__(*args, dependents, **kwargs)

        cls.__payloads__ = kwargs.get("payloads", {}) | getattr(cls, "__payloads__", {})
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))
        cls.__parser__ = kwargs.get("parser", getattr(cls, "__parser__", str))

    def __call__(cls, sources, *args, **kwargs):
        if not bool(sources) and not cls.optional: raise WebPayloadMissingError()
        if not isinstance(sources, list) and cls.multiple: raise WebPayloadSingleError()
        if isinstance(sources, list) and not cls.multiple: raise WebPayloadMultipleError()

    @property
    def payloads(cls): return cls.__payloads__
    @property
    def optional(cls): return cls.__optional__
    @property
    def multiple(cls): return cls.__multiple__
    @property
    def locator(cls): return cls.__locator__
    @property
    def parser(cls): return cls.__parser__


class WebPayload(ABC, metaclass=WebPayloadMeta):
    pass


class WebPayloadMapping(WebPayload, ABC, attribute="Mapping"):
    pass


class WebPayloadText(WebPayload, ABC, attribute="Text"):
    pass



