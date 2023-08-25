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

    def toJSON(self, element, locators):
        assert isinstance(locators, list)
        locator = str(locators.pop(-1))
        locator, collection = str(locator).strip("[]"), str(locator).endswith("[]")
        root = [{locator: element}] if bool(collection) else {locator: element}
        return root if not bool(locators) else self.toJSON(root, locators)

    def toXML(self, element, locators):
        assert isinstance(locators, list)
        if not bool(locators):
            return element
        locator = str(locators.pop(-1)).strip("[]")
        root = lxml.etree.Element(locator)
        root.append(element)
        return self.toXML(root, locators)

    @property
    def json(self):
        locators = [str(locator) for locator in str(self.locator).strip("//").split("/")]
        element = str(self.value)
        return self.toJSON(element, locators)

    @property
    def xml(self):
        locators = [str(locator) for locator in str(self.locator).strip("//").split("/")]
        element = lxml.etree.Element(locators.pop(-1).strip("[]"))
        element.text = str(self.value)
        return self.toXML(element, locators)

    @property
    def value(self): return self.__value
    @value.setter
    def value(self, value): self.__value = value


class WebPayloadMeta(ABCMeta):
    def __repr__(cls):
        renderer = cls.hierarchy(style=cls.__style__)
        rows = [pre + "|".join(key, value.__name__) for pre, key, value in iter(renderer)]
        return "\n".format(rows)

    def __new__(mcs, name, bases, attrs, *args, **kwargs):
        cls = super(WebPayloadMeta, mcs).__new__(mcs, name, bases, attrs)
        if not any([type(base) is WebPayloadMeta for base in bases]):
            return cls
        assert type(bases[0]) is WebPayloadMeta
        assert all([type(base) is not WebPayloadMeta for base in bases[1:]])
        if ABC in bases:
            return cls
        children = [payload for payload in getattr(cls, "__children__", [])]
        children = children + kwargs.get("payloads", [])
        assert all([type(child) is WebPayloadMeta for child in children if inspect.isclass(child)])
        assert all([isinstance(child, dict) for child in children if not inspect.isclass(child)])
        assert all([all([type(value) is WebPayloadMeta for value in child.values()]) for child in children if not inspect.isclass(child)])
        setattr(cls, "__children__", children)
        return cls

    def __init__(cls, name, bases, attrs, *args, **kwargs):
        if not any([type(base) is WebPayloadMeta for base in bases]):
            return
        assert type(bases[0]) is WebPayloadMeta
        assert all([type(base) is not WebPayloadMeta for base in bases[1:]])
        if ABC in bases:
            return
        cls.__fields__ = {key: field for key, field in getattr(cls, "__fields__", {}).items()}
        cls.__fields__.update({key: WebField(key, locator) for key, locator in kwargs.get("fields", {}).items()})
        cls.__collection__ = kwargs.get("collection", getattr(cls, "__collection__", False))
        cls.__locator__ = kwargs.pop("locator", getattr(cls, "__locator__", None))
        cls.__style__ = kwargs.pop("style", getattr(cls, "__style__", single))
        cls.__key__ = kwargs.pop("key", getattr(cls, "__key__", None))
        for key, field in cls.__fields__.items():
            if key in kwargs.keys():
                field.value = kwargs[key]

    def __call__(cls, *args, **kwargs):
        fields, collection = (field for field in cls.__fields__.values()), cls.__collection__
        fields = [WebField(field.key, field.locator, field.value if bool(field) else kwargs.get(field.key, None)) for field in fields]
        attributes = {attr: getattr(cls, asdunder(attr)) for attr in ("locator", "key", "style")}
        instance = super(WebPayloadMeta, cls).__call__(fields, **attributes)
        for child in cls.__children__:
            if inspect.isclass(child):
                assert type(child) is WebPayloadMeta
                subinstance = child(*args, **kwargs)
                instance[subinstance.key] = subinstance
                continue
            assert isinstance(child, dict)
            assert all([type(value) is WebPayloadMeta for value in child.values()])
            for key, value in child.items():
                if key not in kwargs.keys():
                    continue
                parameters = kwargs[key]
                assert isinstance(parameters, dict)
                subinstance = value(*args, **parameters, **kwargs)
                instance[subinstance.key] = subinstance
        return instance

    def hierarchy(cls, layers=[], style=single):
        last = lambda i, x: i == x
        func = lambda i, x: "".join([pads(), pre(i, x)])
        pre = lambda i, x: style.terminate if last(i, x) else style.blank
        pads = lambda: "".join([style.blank if layer else style.run for layer in layers])
        if not layers:
            yield "", None, cls
        for index, (key, values) in enumerate(iter(cls.__children__)):
            for value in aslist(values):
                yield func(index, len(cls.__children__) - 1), key, value
                yield from value.renderer(layers=[*layers, last(index, len(cls.__children__) - 1)])


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
    def fields(self): return self.__fields
    @property
    def locator(self): return self.__locator
    @property
    def key(self): return self.__key

    @property
    def json(self):
        pass

    @property
    def xml(self):
        pass

#    @property
#    def xml(self):
#        locators = str(self.locator).strip("/").split("/")
#        root = lxml.etree.Element(locators.pop(0))
#        element = root
#        while bool(locators):
#            element = lxml.etree.SubElement(element, locators.pop(0))
#        for content in self.contents:
#            locators = str(content.locator).strip("/").split("/")
#            segment = lxml.etree.SubElement(element, locators.pop(0))
#            while bool(locators):
#                segment = lxml.etree.SubElement(segment, locators.pop(0))
#            segment.text = str(content.value)
#        for values in self.values():
#            for value in aslist(values):
#                element.append(value.xml)
#        return root



