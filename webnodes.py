# -*- coding: utf-8 -*-
"""
Created on Sat Aug 5 2023
@name:   WebNode Objects
@author: Jack Kirby Cook

"""

import json
import lxml.html
import lxml.etree
import pandas as pd
from abc import ABC, ABCMeta, abstractmethod
from collections import namedtuple as ntuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMT", "WebHTML", "WebJSON"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


Style = ntuple("Style", "branch terminate run blank")
aslist = lambda x: [x] if not isinstance(x, (list, tuple)) else list(x)
double = Style("╠══", "╚══", "║  ", "   ")
single = Style("├──", "└──", "│  ", "   ")
curved = Style("├──", "╰──", "│  ", "   ")


class WebNodeError(Exception): pass
class WebNodeEmptyError(WebNodeError): pass
class WebNodeMultipleError(WebNodeError): pass


class WebNodeMeta(ABCMeta):
    def __repr__(cls):
        renderer = cls.hierarchy(style=cls.__style__)
        rows = [pre + "|".join(key, value.__name__) for pre, key, value in iter(renderer)]
        return "\n".format(rows)

    def __new__(mcs, name, bases, attrs, *args, **kwargs):
        cls = super(WebNodeMeta, mcs).__new__(mcs, name, bases, attrs)
        if not any([type(base) is WebNodeMeta for base in bases]):
            return cls
        assert type(bases[0]) is WebNodeMeta
        assert all([type(base) is not WebNodeMeta for base in bases])
        if ABC in bases:
            setattr(bases[0], kwargs["register"], cls)
            return cls
        children = {key: value for key, value in getattr(cls, "__children__", {}).items()}
        update = {key: value for key, value in attrs.items() if type(value) is WebNodeMeta}
        children.update(update)
        setattr(cls, "__children__", children)
        return cls

    def __init__(cls, name, bases, attrs, *args, **kwargs):
        if not any([type(base) is WebNodeMeta for base in bases]):
            return
        assert type(bases[0]) is WebNodeMeta
        assert all([type(base) is not WebNodeMeta for base in bases])
        if ABC in bases:
            return
        cls.__collection__ = kwargs.get("collection", getattr(cls, "__collection__", False))
        cls.__parameters__ = kwargs.get("parameters", getattr(cls, "__parameters__", {}))
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))
        cls.__parser__ = kwargs.get("parser", getattr(cls, "__parser__", None))
        cls.__style__ = kwargs.get("style", getattr(cls, "__style__", single))
        cls.__key__ = kwargs.get("key", getattr(cls, "__key__", None))

    def __call__(cls, source):
        locator, optional, collection = cls.__locator__, cls.__optional__, cls.__collection__
        elements = [element for element in cls.locate(source, locator=locator)]
        if not bool(elements) and not optional:
            raise WebNodeEmptyError()
        if len(elements) > 1 and not collection:
            raise WebNodeMultipleError()
        instances = [super(WebNodeMeta, cls).__call__(content) for content in elements]
        for instance in instances:
            for key, subcls in cls.__children__.items():
                subinstances = subcls(instance.contents)
                instance[key] = subinstances
        return (instances[0] if bool(instances) else None) if collection else instances

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


class WebNode(ABC, metaclass=WebNodeMeta):
    def __init_subclass__(cls, *args, register=None, **kwargs):
        if register is not None:
            setattr(WebNode, register, cls)

    def __init__(self, contents, *args, **kwargs):
        style = self.__class__.__style__
        super().__init__(style=style)
        self.__contents = contents

    def __setitem__(self, key, value): self.set(key, value)
    def __getitem__(self, key): return self.get(key)
    def __reversed__(self): return reversed(self.items())
    def __iter__(self): return iter(self.items())

    def __call__(self, *args, **kwargs):
        parameters = {key: value for key, value in self.parameters.items()}
        parameters.update(kwargs)
        data = self.data(*args, **parameters)
        data = self.parser(data, *args, **parameters)
        return data

    @property
    @abstractmethod
    def string(self): pass
    @abstractmethod
    def data(self, *args, **kwargs): pass

    @staticmethod
    @abstractmethod
    def locate(source, *args, locator, **kwargs): pass
    @staticmethod
    def parser(contents, *args, **kwargs): return contents
    @staticmethod
    def extractor(contents, *args, **kwargs): return contents

    @property
    def parameters(self): return self.__class__.__parameters__
    @property
    def locator(self): return self.__class__.__locator__
    @property
    def parser(self): return self.__class__.__parser__
    @property
    def contents(self): return self.__contents


class WebELMT(WebNode, ABC, register="Element"):
    def data(self, *args, **kwargs): return str(self.string)
    def click(self): self.element.click()

    @staticmethod
    def locate(source, *args, locator, timeout=5, **kwargs):
        try:
            elements = WebDriverWait(source, timeout).until(EC.presence_of_all_elements_located((By.XPATH, locator)))
        except (NoSuchElementException, TimeoutException, WebDriverException):
            elements = []
        yield from iter(elements)

    @property
    def html(self): return lxml.html.fromstring(self.string)
    @property
    def string(self): return self.element.get_attribute("outerHTML")
    @property
    def element(self): return self.contents


class WebELMTCaptcha(WebELMT, ABC, register="Captcha"):
    pass


class WebELMTInput(WebELMT, ABC, register="Input"):
    def fill(self, value): self.element.send_keys(value)
    def send(self): self.element.submit()
    def clear(self): self.element.clear()


class WebELMTSelect(WebELMT, ABC, register="Select"):
    def __init__(self, contents, *args, **kwargs):
        super().__init__(contents, *args, **kwargs)
        self.__select = Select(contents)

    def sel(self, key): self.select.select_by_value(key)
    def isel(self, key): self.select.select_by_index(key)
    def clear(self): self.select.deselect_all()

    @property
    def select(self): return self.__select


class WebELMTCheckBox(WebELMT, ABC, register="CheckBox"):
    @property
    def checked(self): return True if self.element.get_attribute("ariaChecked") in ("true", "mixed") else False


class WebHTML(WebNode, ABC, register="Html"):
    def data(self, *args, **kwargs): return str(self.string)

    @staticmethod
    def locate(source, *args, locator, removal=None, **kwargs):
        elements = [element.remove(removal) if bool(removal) else element for element in source.xpath(locator)]
        yield from iter(elements)

    @property
    def text(self): return self.contents.attrib["text"]
    @property
    def link(self): return self.contents.attrib["href"]
    @property
    def string(self): return lxml.html.tostring(self.html)
    @property
    def html(self): return self.contents


class WebHTMLText(WebHTML, ABC, register="Text"):
    def data(self, *args, **kwargs): return str(self.text)


class WebHTMLLink(WebHTML, ABC, register="Link"):
    def data(self, *args, **kwargs): return str(self.link)


class WebHTMLTable(WebHTML, ABC, register="Table"):
    def data(self, *args, header=None, index=None, **kwargs):
        return pd.concat(pd.read_html(self.string, header=header, index_col=index), axis=0)


class WebJSON(WebNode, ABC, register="Json"):
    @property
    def string(self): return str(json.dumps(self.contents, sort_keys=True, indent=3, separators=(',', ' : '), default=str))
    def data(self, *args, **kwargs): return self.contents

    @classmethod
    def locate(cls, source, *args, locator, **kwargs):
        assert isinstance(source, (list, dict)) and isinstance(locator, (list, str))
        locator = str(locator).strip("/").split("/") if isinstance(locator, str) else locator
        source = [source] if isinstance(source, dict) else source
        generator = lambda key: (items[key] for items in source if key in items.keys())
        elements = generator(locator.pop(0))
        for element in iter(elements):
            if bool(locator):
                yield from cls.locate(element, *args, locator=locator, **kwargs)
            else:
                yield element

    def toJSON(self, *args, **kwargs):
        root = dict()
        layer = lambda content, path: {path[0]: layer(path[1:], value)} if bool(path) else value
        for child in self.children:
            locator = str(child.locator).strip("/").split("/")
            key = locator.pop(0)
            if bool(child.collection):
                root[key] = []
                for value in child:
                    root.append(layer(value.toJSON(*args, **kwargs), locator))
            else:
                root[key] = layer(value.toJSON(*args, **kwargs), locator)
        return root

    def toXML(self, *args, **kwargs):
        locator = str(self.locator).strip("/").split("/")
        root = lxml.etree.Element(locator.pop(0))
        element = root
        while bool(locator):
            element = lxml.etree.SubElement(element, locator.pop(0))
        for child in self.children:
            element.append(child.toXML(*args, **kwargs))
        return root


class WebJsonText(WebJSON, ABC, register="Text"):
    @property
    def string(self): return str(self.contents)
    def data(self, *args, **kwargs): return self.contents

    def toJSON(self, *args, **kwargs):
        parameters = {key: value for key, value in self.parameters.items()}
        parameters.update(kwargs)
        data = self.data(*args, **parameters)
        data = self.parser(data, *args, **parameters)
        return data

    def toXML(self, *args, **kwargs):
        locator = str(self.locator).strip("/").split("/")
        root = lxml.etree.Element(locator.pop(0))
        element = root
        while bool(locator):
            element = lxml.etree.SubElement(element, locator.pop(0))
        parameters = {key: value for key, value in self.parameters.items()}
        parameters.update(kwargs)
        data = self.data(*args, **parameters)
        data = self.parser(data, *args, **parameters)
        element.text = str(data)
        return root

