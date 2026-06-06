# -*- coding: utf-8 -*-
"""
Created on Tues May 19 2026
@name:   WebPayload Objects
@author: Jack Kirby Cook

"""

from abc import ABC, ABCMeta, abstractmethod

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
        initialize = lambda value: super(WebPayloadMeta, cls).__call__(value, *args, **kwargs)
        if cls.multiple:
            if not isinstance(sources, list): raise WebPayloadSingleError()
            if not cls.optional and not sources: raise WebPayloadMissingError()
            contents = [cls.create(source) for source in sources]
            instances = [initialize(content) for content in contents]
        else:
            if isinstance(sources, list): raise WebPayloadMultipleError()
            if not cls.optional and sources is None: raise WebPayloadMissingError()
            contents = cls.create(sources)
            instances = initialize(contents)
        return instances

    @abstractmethod
    def create(cls, source): pass

    @property
    def multiple(cls): return cls.__multiple__
    @property
    def optional(cls): return cls.__optional__
    @property
    def locator(cls): return cls.__locator__


class WebPayloadMappingMeta(WebPayloadMeta):
    def __init__(cls, *args, **kwargs):
        super(WebPayloadMappingMeta, cls).__init__(*args, **kwargs)
        cls.__mapping__ = getattr(cls, "__mapping__", {}) | kwargs.get("mapping", {})

    def create(cls, source):
        if not isinstance(source, dict): raise WebPayloadTypingError()
        dependents = cls.dependents.values()
        dynamic = {dependent.locator: dependent(source) for dependent in dependents}
        static = dict(cls.mapping)
        return dynamic | static

    @property
    def mapping(cls): return cls.__mapping__


class WebPayloadValueMeta(WebPayloadMeta):
    def __init__(cls, *args, **kwargs):
        super(WebPayloadValueMeta, cls).__init__(*args, **kwargs)
        cls.__parser__ = kwargs.get("parser", getattr(cls, "__parser__", lambda value: value))

    def create(cls, source):
        return cls.parser(source)

    @property
    def parser(cls): return cls.__parser__


class WebPayload(ABC, metaclass=WebPayloadMeta): pass
class WebPayloadMapping(WebPayload, dict, attribute="Mapping", metaclass=WebPayloadMappingMeta): pass
class WebPayloadValue(WebPayload, str, attribute="Value", metaclass=WebPayloadValueMeta): pass



