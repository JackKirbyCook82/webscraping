# -*- coding: utf-8 -*-
"""
Created on Sat Aug 5 2023
@name:   WebPayload Objects
@author: Jack Kirby Cook

"""

import inspect
import lxml.etree
from abc import ABC, ABCMeta
from collections import namedtuple as ntuple

from support.mixins import Node
from support.custom import StackOrderedDict as SODict

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebPayload"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


Style = ntuple("Style", "branch terminate run blank")
Field = ntuple("Field", "key locator")
aslist = lambda x: [x] if not isinstance(x, (list, tuple)) else list(x)
asdunder = lambda x: "__{}__".format(x)
double = Style("╠══", "╚══", "║  ", "   ")
single = Style("├──", "└──", "│  ", "   ")
curved = Style("├──", "╰──", "│  ", "   ")


class WebField(Field):
    def __init__(self, *args, **kwargs): self.__value = None
    def __bool__(self): return self.__value is not None

    @property
    def json(self):
        locators = [str(locator) for locator in str(self.locator).strip("//").split("/")]
        element = self.value
        for locator in locators:
            locator, collection = str(locator).strip("[]"), str(locator).endswith("[]")
            element = SODict([(locator, [element] if bool(collection) else element)])
        return element

    @property
    def xml(self):
        locators = [str(locator) for locator in str(self.locator).strip("//").split("/")]
        root = lxml.etree.Element(str(locators.pop(0)).strip("[]"))
        element = root
        for locator in locators:
            element = lxml.etree.SubElement(element, str(locator).strip("[]"))
        element.text = str(self.value)
        return root

    @property
    def value(self): return self.__value
    @value.setter
    def value(self, value): self.__value = value


class WebPayloadError(Exception): pass
class WebPayloadEmptyError(WebPayloadError): pass
class WebPayloadMultipleError(WebPayloadError): pass


class WebPayloadMeta(ABCMeta):
    def __new__(mcs, name, bases, attrs, *args, **kwargs):
        cls = super(WebPayloadMeta, mcs).__new__(mcs, name, bases, attrs)
        if not any([type(base) is WebPayloadMeta for base in bases]):
            return cls
        assert type(bases[0]) is WebPayloadMeta
        assert all([type(base) is not WebPayloadMeta for base in bases[1:]])
        if ABC in bases:
            return cls
        children = getattr(cls, "__children__", []) + kwargs.get("payloads", [])
        fields = {key: field for key, field in getattr(cls, "__fields__", {}).items()}
        fields.update({key: WebField(key, locator) for key, locator in kwargs.get("fields", {}).items()})
        for key, field in fields.items():
            if key in kwargs.keys():
                field.value = kwargs[key]
        assert all([type(child) is WebPayloadMeta for child in children if inspect.isclass(child)])
        assert all([isinstance(mapping, dict) for mapping in children if not inspect.isclass(mapping)])
        assert all([all([type(child) is WebPayloadMeta for child in mapping.values()]) for mapping in children if not inspect.isclass(mapping)])
        setattr(cls, "__children__", children)
        setattr(cls, "__fields__", fields)
        return cls

    def __init__(cls, name, bases, attrs, *args, **kwargs):
        if not any([type(base) is WebPayloadMeta for base in bases]):
            return
        assert type(bases[0]) is WebPayloadMeta
        assert all([type(base) is not WebPayloadMeta for base in bases[1:]])
        if ABC in bases:
            return
        cls.__collection__ = kwargs.get("collection", getattr(cls, "__collection__", False))
        cls.__locator__ = kwargs.pop("locator", getattr(cls, "__locator__", None))
        cls.__style__ = kwargs.pop("style", getattr(cls, "__style__", single))
        cls.__key__ = kwargs.pop("key", getattr(cls, "__key__", None))

    def __call__(cls, source, **parameters):
        assert isinstance(source, (dict, list))
        attributes = {attr: getattr(cls, asdunder(attr)) for attr in ("locator", "key", "style")}
        optional, collection = cls.__optional__, cls.__collection__
        static = [field for field in cls.__fields__.values() if bool(field)]
        dynamic = [field for field in cls.__fields__.values() if not bool(field)]
        elements = [element for element in cls.create(source, fields=dynamic)]
        if not bool(elements) and not optional:
            raise WebPayloadEmptyError()
        if len(elements) > 1 and not collection:
            raise WebPayloadMultipleError()
        instances = [super(WebPayloadMeta, cls).__call__(static + element, **attributes) for element in elements]
        for instance in instances:
            pass
        return instances

#        instance = super(WebPayloadMeta, cls).__call__(fields, **attributes)
#        for child in cls.__children__:
#            if inspect.isclass(child):
#                assert type(child) is WebPayloadMeta
#                subinstance = child(*args, **kwargs)
#                instance[subinstance.key] = subinstance
#                continue
#            assert isinstance(child, dict)
#            assert all([type(value) is WebPayloadMeta for value in child.values()])
#            for key, value in child.items():
#                if key not in kwargs.keys():
#                    continue
#                parameters = kwargs[key]
#                assert isinstance(parameters, dict)
#                subinstance = value(*args, **parameters, **kwargs)
#                instance[subinstance.key] = subinstance
#        return instance

    @staticmethod
    def create(source, *args, fields=[], **kwargs):
        for element in aslist(source):
            assert isinstance(element, dict)
            fields = [WebField(field.key, field.locator, source.get(field.key, None)) for field in fields]
            yield fields


class WebPayload(Node, metaclass=WebPayloadMeta):
    def __init__(self, fields, *args, key, locator, style, **kwargs):
        super().__init__(style=style)
        self.__fields = fields
        self.__locator = locator
        self.__key = key

    def __setitem__(self, key, value): self.set(key, value)
    def __getitem__(self, key): return self.get(key)
    def __reversed__(self): return reversed(self.items())
    def __iter__(self): return iter(self.items())

    @property
    def json(self):
        locators = [str(locator) for locator in str(self.locator).strip("//").split("/")]
        element = SODict()
        for field in self.fields:
            element[field.key] = field.json
        for locator in locators:
            locator, collection = str(locator).strip("[]"), str(locator).endswith("{}")
            element = SODict([(locator, [element] if bool(collection) else element)])
        return element

    @property
    def xml(self):
        locators = [str(locator) for locator in str(self.locator).strip("//").split("/")]
        root = lxml.etree.Element(str(locators.pop(0)).strip("[]"))
        element = root
        for locator in locators:
            element = lxml.etree.SubElement(element, str(locator).strip("[]"))
        for field in self.fields:
            element.append(field.xml)
        return root

    @property
    def fields(self): return self.__fields
    @property
    def locator(self): return self.__locator
    @property
    def key(self): return self.__key

