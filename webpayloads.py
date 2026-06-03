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
class WebPayloadTypingError(WebPayloadError): pass


class WebPayloadMeta(AttributeMeta, TreeMeta, ABCMeta):
    def __init__(cls, *args, **kwargs):
        super(WebPayloadMeta, cls).__init__(*args, **kwargs)
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))

    def __call__(cls, sources, *args, **kwargs):
        default = [] if cls.multiple else None
        sources = sources.get(cls.key, default) if cls.key is not None else sources
        initialize = lambda source: super(WebPayloadMeta, cls).__call__(source, *args, **kwargs)
        if cls.multiple:
            if not isinstance(sources, list): raise WebPayloadSingleError()
            if not cls.optional and not sources: raise WebPayloadMissingError()
            instance = [initialize(source) for source in sources]
        else:
            if isinstance(sources, list): raise WebPayloadMultipleError()
            if not cls.optional and sources is None: raise WebPayloadMissingError()
            instance = initialize(sources)
        return instance

    @property
    def multiple(cls): return cls.__multiple__
    @property
    def optional(cls): return cls.__optional__
    @property
    def locator(cls): return cls.__locator__


class WebPayload(ABC, metaclass=WebPayloadMeta):
    pass


class WebPayloadMapping(WebPayload, attribute="Mapping"):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.static = getattr(cls, "static", {}) | kwargs.get("static", {})

    def __new__(cls, source, *args, **kwargs):
        if not isinstance(source, dict): raise WebPayloadTypingError()
        dependents = cls.dependents.values()
        dynamic = {dependent.locator: dependent(source) for dependent in dependents}
        return cls.static | dynamic


class WebPayloadText(WebPayload, attribute="Text"):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.parser = kwargs.get("parser", getattr(cls, "parser", str))

    def __new__(cls, source, *args, **kwargs):
        return cls.parser(source)



