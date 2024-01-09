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
aslist = lambda x: [x] if not isinstance(x, (list, tuple)) else list(x)
asdunder = lambda x: f"__{x}__"
double = Style("╠══", "╚══", "║  ", "   ")
single = Style("├──", "└──", "│  ", "   ")
curved = Style("├──", "╰──", "│  ", "   ")


def renderer(node, layers=[], style=single):
    last = lambda i, x: i == x
    func = lambda i, x: "".join([pads(), pre(i, x)])
    pre = lambda i, x: style.terminate if last(i, x) else style.blank
    pads = lambda: "".join([style.blank if layer else style.run for layer in layers])
    if not layers:
        yield "", None, node
    children = iter(node.__children__.items())
    size = len(list(children))
    for index, (key, values) in enumerate(children):
        for value in aslist(values):
            yield func(index, size - 1), key, value
            yield from renderer(value, layers=[*layers, last(index, size - 1)], style=style)


class WebField(ntuple("Field", "key locator")):
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
    def __repr__(cls): return str(cls.__name__)
    def __new__(mcs, name, bases, attrs, *args, key, payloads={}, **kwargs):
        cls = super(WebPayloadMeta, mcs).__new__(mcs, name, bases, attrs)
        if not any([type(base) is WebPayloadMeta for base in bases]):
            return cls
        assert type(bases[0]) is WebPayloadMeta
        assert all([type(base) is not WebPayloadMeta for base in bases[1:]])
        if ABC in bases:
            return cls
        assert isinstance(payloads, dict)
        assert all([inspect.isclass(payload) for payload in payloads.values()])
        assert all([type(payload) is WebPayloadMeta for payload in payloads.values()])
        children = {key: payload for key, payload in getattr(cls, "__children__", {}).items()}
        children.update(payloads)
        fields = {key: field for key, field in getattr(cls, "__fields__", {}).items()}
        update = {key: WebField(key, locator) for key, locator in kwargs.get("fields", {}).items()}
        fields.update(update)
        for key, field in fields.items():
            if key in kwargs.keys():
                field.value = kwargs[key]
        setattr(cls, "__children__", children)
        setattr(cls, "__fields__", fields)
        setattr(cls, "__key__", key)
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

    def __and__(cls, payloads):
        assert all([inspect.isclass(payload) for payload in aslist(payloads)])
        assert all([type(payload) is WebPayloadMeta for payload in aslist(payloads)])
        rootkey = str(cls.__key__)
        childkeys = "|".join([str(payload.__key__) for payload in aslist(payloads)])
        key = f"{rootkey}[{childkeys}]"
        payloads = {str(payload.__key__): payload for payload in aslist(payloads)}
        return type(cls.__name__, (cls,), {}, key=key, payloads=payloads)

    def __getitem__(cls, key): return cls.subclasses[key]
    def __call__(cls, sources, *args, **kwargs):
        assert isinstance(sources, (dict, list))
        assert not any([attr in kwargs.keys() for attr in ("locator", "key", "style")])
        attributes = {attr: getattr(cls, asdunder(attr)) for attr in ("locator", "key", "style")}
        optional, collection = cls.__optional__, cls.__collection__
        defined = [field for field in cls.__fields__.values() if bool(field)]
        undefined = [field for field in cls.__fields__.values() if not bool(field)]
        define = lambda fields, element: [WebField(field.key, field.locator, element.get(field.key, None)) for field in fields]
        elements = [defined + define(undefined, element) for element in aslist(sources)]
        if not bool(elements) and not optional:
            raise WebPayloadEmptyError()
        if len(elements) > 1 and not collection:
            raise WebPayloadMultipleError()
        instances = [super(WebPayloadMeta, cls).__call__(element, *args, **attributes, **kwargs) for element in elements]
        for source, instance in zip(aslist(sources), aslist(instances)):
            for key, subcls in cls.__children__.items():
                subsources = aslist(source.get(key, []))
                subinstances = subcls(subsources, *args, **kwargs)
                instance[key] = subinstances
        return instances

    @property
    def hierarchy(cls):
        generator = renderer(cls, style=cls.__style__)
        rows = [pre + repr(value) for pre, key, value in iter(generator)]
        return "\n".format(rows)

    @property
    def subclasses(cls):
        subclasses = {subcls.__key__: subcls for subcls in cls.__subclasses__}
        for subcls in subclasses:
            subclasses.update(subcls.subclasses)
        return subclasses


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
            element[field.key].append(field.json)
        for payload in self.children:
            element[payload.key].append(payload.json)
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
        for payload in self.children:
            element.append(payload.xml)
        return root

    @property
    def fields(self): return self.__fields
    @property
    def locator(self): return self.__locator
    @property
    def key(self): return self.__key

