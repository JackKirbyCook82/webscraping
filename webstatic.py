# -*- coding: utf-8 -*-
"""
Created on Sat Dec 28 2024
@name:   WebStatic Objects
@author: Jack Kirby Cook

"""

import json
import logging
import lxml.html
import pandas as pd
from abc import ABC, ABCMeta, abstractmethod

from support.meta import ParametersMeta, AttributeMeta, TreeMeta
from support.trees import MixedNode

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebHTML", "WebJSON"]
__copyright__ = "Copyright 2024, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebStaticErrorMeta(type):
    def __init__(cls, name, bases, attrs, *args, title=None, **kwargs):
        assert str(name).endswith("Error")
        super(WebStaticErrorMeta, cls).__init__(name, bases, attrs)
        cls.__logger__ = __logger__
        cls.__title__ = title

    def __call__(cls, source):
        instance = super(WebStaticErrorMeta, cls).__call__(source)
        cls.logger.info(f"{cls.title}: {repr(source)}")
        return instance

    @property
    def logger(cls): return cls.__logger__
    @property
    def title(cls): return cls.__title__
    @property
    def name(cls): return cls.__name__


class WebStaticError(Exception, metaclass=WebStaticErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return f"{type(self).name}|{repr(self.source)}"
    def __init__(self, source): self.__source = source

    @property
    def source(self): return self.__source


class WebStaticMissingError(WebStaticError, title="Missing"): pass
class WebStaticMultipleError(WebStaticError, title="Multiple"): pass


class WebStaticMeta(ParametersMeta, AttributeMeta, TreeMeta, ABCMeta):
    def __init__(cls, name, bases, attrs, *args, **kwargs):
        super(WebStaticMeta, cls).__init__(name, bases, attrs, *args, **kwargs)
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))

    def __call__(cls, sources, *args, **kwargs):
        sources = [source for source in cls.locate(sources, *args, **kwargs)]
        if not bool(sources) and not cls.optional: raise WebStaticMissingError(cls)
        if len(sources) > 1 and not cls.multiple: raise WebStaticMultipleError(cls)
        instances = [super(WebStaticMeta, cls).__call__(source, *args, **kwargs) for source in sources]
        for source, instance in zip(sources, instances):
            for key, dependent in cls.dependents.items():
                instance[key] = dependent(source, *args, **kwargs)
        if bool(cls.multiple): return list(instances)
        else: return instances[0] if bool(instances) else None

    @property
    def optional(cls): return cls.__optional__
    @property
    def multiple(cls): return cls.__multiple__
    @property
    def locator(cls): return cls.__locator__


class WebStatic(MixedNode, ABC, metaclass=WebStaticMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __init__(self, source, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__source = source

    @abstractmethod
    def execute(self, *args, **kwargs): pass
    @classmethod
    @abstractmethod
    def locate(cls, source, *args, **kwargs): pass
    @property
    @abstractmethod
    def string(self): pass

    @property
    def source(self): return self.__source


class WebContents(WebStatic, ABC):
    def execute(self, *args, **kwargs): return {key: value(*args, **kwargs) for key, value in iter(self)}


class WebHTML(WebContents, ABC, root=True):
    @classmethod
    def locate(cls, source, *args, **kwargs):
        contents = list(source.xpath(cls.locator))
        yield from iter(contents)

    @property
    def string(self): return lxml.html.tostring(self.html)
    @property
    def html(self): return self.source


class WebJSON(WebContents, ABC, root=True):
    @classmethod
    def locate(cls, source, *args, **kwargs):
        locators = str(cls.locator).lstrip("//").rstrip("[]").split("/")
        contents = source[str(locators.pop(0))]
        for locator in locators: contents = contents[str(locator)]
        if isinstance(contents, (tuple, list)): yield from iter(contents)
        elif isinstance(contents, (str, int, float)): yield contents
        elif isinstance(contents, dict): yield contents
        else: raise TypeError(type(contents))

    @property
    def string(self): return json.dumps(self.json, sort_keys=True, indent=3, separators=(',', ' : '), default=str)
    @property
    def json(self): return self.source


class WebContent(WebStatic, ABC, parameters=["parser"]):
    def __init__(self, *args, parser, **kwargs):
        super().__init__(*args, **kwargs)
        self.__parser = parser

    def parse(self, content, *args, **kwargs): return self.parser(content)
    def execute(self, *args, **kwargs):
        arguments = tuple([self.content] + list(args))
        parameters = dict(kwargs)
        return self.parse(*arguments, **parameters)

    @property
    @abstractmethod
    def content(self): pass
    @property
    def parser(self): return self.__parser


class WebHTMLText(WebContent, WebHTML, ABC, attribute="Text"):
    @property
    def text(self): return str(self.html.attrib["text"])
    @property
    def content(self): return self.text

class WebHTMLLink(WebContent, WebHTML, ABC, attribute="Link"):
    @property
    def link(self): return str(self.html.attrib["href"])
    @property
    def content(self): return self.link

class WebHTMLTable(WebContent, WebHTML, ABC, attribute="Table"):
    @property
    def table(self): return pd.concat(pd.read_html(self.string, header=0, index_col=None), axis=0)
    @property
    def content(self): return self.table

class WebJsonMapping(WebContent, WebJSON, attribute="Mapping"):
    @property
    def mapping(self): return dict(self.json)
    @property
    def content(self): return self.mapping

class WebJsonText(WebContent, WebJSON, ABC, attribute="Text"):
    @property
    def text(self): return str(self.json)
    @property
    def content(self): return self.text







