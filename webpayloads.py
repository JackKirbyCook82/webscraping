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
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))

    def extract(cls, source):
        if cls.key is not None: return source
        if not isinstance(source, dict): raise WebPayloadTypingError()
        if cls.optional and cls.key not in source: raise WebPayloadMissingError()
        return source[cls.key]

    @property
    def optional(cls): return cls.__optional__
    @property
    def locator(cls): return cls.__locator__


class WebCollectionMeta(WebPayloadMeta):
    def __init__(cls, *args, **kwargs):
        super(WebCollectionMeta, cls).__init__(*args, **kwargs)
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))

    def __call__(cls, sources, *args, **kwargs):
        if cls.multiple and not isinstance(sources, list): raise WebPayloadSingleError()
        elif not cls.multiple and isinstance(sources, list): raise WebPayloadMultipleError()
        if cls.multiple and not cls.optional and not bool(sources): raise WebPayloadMissingError()
        initialize = lambda source: super(WebCollectionMeta, cls).__call__(source, *args, **kwargs)
        if cls.multiple: return [initialize(source) for source in sources]
        else: return initialize(sources)

    @property
    def multiple(cls): return cls.__multiple__


class WebMappingMeta(WebPayloadMeta):
    def __init__(cls, *args, **kwargs):
        super(WebMappingMeta, cls).__init__(*args, **kwargs)
        cls.__static__ = getattr(cls, "__static__", {}) | kwargs.get("static", {})

    def __call__(cls, source, *args, **kwargs):
        source = cls.extract(source)
        if not isinstance(source, dict): raise WebPayloadTypingError()
        if not cls.optional and not bool(source): raise WebPayloadMissingError()
        children = {dependent.locator: dependent(source, *args, **kwargs) for dependent in cls.dependents.values()}
        return cls.static | children

    @property
    def static(cls): return cls.__static__


class WebTextMeta(WebPayloadMeta):
    def __init__(cls, *args, **kwargs):
        super(WebTextMeta, cls).__init__(*args, **kwargs)
        cls.__parser__ = kwargs.get("parser", getattr(cls, "__parser__", str))

    def __call__(cls, source, *args, **kwargs):
        source = cls.extract(source)
        if not isinstance(source, (str, int, float)): raise WebPayloadTypingError()
        if not cls.optional and source is None: raise WebPayloadMissingError()
        return cls.parser(source)

    @property
    def parser(cls): return cls.__parser__


class WebPayloadMappingMeta(WebCollectionMeta, WebMappingMeta): pass
class WebPayloadTextMeta(WebCollectionMeta, WebTextMeta): pass


class WebPayload(ABC, metaclass=WebPayloadMeta): pass
class WebPayloadMapping(WebPayload, metaclass=WebPayloadMappingMeta, attribute="Mapping"): pass
class WebPayloadText(WebPayload, metaclass=WebPayloadTextMeta, attribute="Text"): pass





