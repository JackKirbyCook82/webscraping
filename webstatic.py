# -*- coding: utf-8 -*-
"""
Created on Sat Dec 28 2024
@name:   WebStatic Objects
@author: Jack Kirby Cook

"""

import json
import types

import lxml.html
import pandas as pd
from abc import ABC, abstractmethod

from webscraping.websourcing import WebContents, WebSourcing, SourcingType
from support.meta import AttributeMeta, TreeMeta
from support.trees import ParentalNode
from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebHTML", "WebJSON"]
__copyright__ = "Copyright 2024, Jack Kirby Cook"
__license__ = "MIT License"


class WebStaticMeta(AttributeMeta, TreeMeta):
    def __init__(cls, name, bases, attrs, *args, **kwargs):
        super(WebStaticMeta, cls).__init__(name, bases, attrs, *args, **kwargs)
        if ABC in bases: cls.__sourcing__ = cls.customize(*args, **kwargs)
        else: cls.__sourcing__ = cls.finalized(*args, **kwargs)

    def __call__(cls, source, *args, **kwargs):
        sources = [value for value in cls.sourcing(source, *args, **kwargs)]
        instances = [super(WebStaticMeta, cls).__call__(value, *args, **kwargs) for value in sources]
        for value, instance in zip(sources, instances):
            children = {key: dependent(value, *args, **kwargs) for key, dependent in cls.dependents.items()}
            for key, child in children.items(): instance[key] = child
        if bool(cls.multiple): return list(instances)
        else: return instances[0] if bool(instances) else None

    def customize(cls, *args, sourcingtype=None, **kwargs):
        assert isinstance(sourcingtype, (SourcingType, types.NoneType))
        if isinstance(sourcingtype, SourcingType): return WebSourcing[sourcingtype]
        else: return getattr(cls, "__sourcing__", None)

    def finalize(cls, *args, **kwargs):
        assert not isinstance(cls.sourcing, types.NoneType)
        return cls.sourcing(*args, **kwargs)

    @property
    def sourcing(cls): return cls.__sourcing__


class WebStatic(ParentalNode, Logging, ABC, metaclass=WebStaticMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return self.string
    def __init__(self, source, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__source = source

    @property
    @abstractmethod
    def string(self): pass
    @property
    def source(self): return self.__source


class WebHTML(WebContents.Multiple, WebStatic, ABC, sourcingtype=SourcingType.HTML, root=True):
    @property
    def string(self): return lxml.html.tostring(self.html)
    @property
    def html(self): return self.source

class WebJSON(WebContents.Multiple, WebStatic, ABC, sourcingtype=SourcingType.JSON, root=True):
    @property
    def string(self): return json.dumps(self.json, sort_keys=True, indent=3, separators=(',', ' : '), default=str)
    @property
    def json(self): return self.source


class WebHTMLText(WebContents.Single, WebHTML, ABC, attribute="Text"):
    @property
    def text(self): return str(self.html.attrib["text"])
    @property
    def content(self): return self.text

class WebHTMLLink(WebContents.Single, WebHTML, ABC, attribute="Link"):
    @property
    def link(self): return str(self.html.attrib["href"])
    @property
    def content(self): return self.link

class WebHTMLTable(WebContents.Single, WebHTML, ABC, attribute="Table"):
    @property
    def table(self): return pd.concat(pd.read_html(self.string, header=0, index_col=None), axis=0)
    @property
    def content(self): return self.table


class WebJsonCollection(WebContents.Single, WebJSON, ABC, attribute="Collection"):
    @property
    def collection(self): return list(self.json)
    @property
    def content(self): return self.collection

class WebJsonMapping(WebContents.Single, WebJSON, ABC, attribute="Mapping"):
    @property
    def mapping(self): return dict(self.json)
    @property
    def content(self): return self.mapping

class WebJsonText(WebContents.Single, WebJSON, ABC, attribute="Text"):
    @property
    def text(self): return str(self.json)
    @property
    def content(self): return self.text





