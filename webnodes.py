# -*- coding: utf-8 -*-
"""
Created on Sat Aug 5 2023
@name:   WebNode Objects
@author: Jack Kirby Cook

"""

from copy import copy
from abc import ABC, ABCMeta, abstractmethod
from collections import namedtuple as ntuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebJSON", "WebHTML", "WebELMT"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


Style = ntuple("Style", "branch terminate run blank")
double = Style("╠══", "╚══",  "║  ", "   ")
single = Style("├──", "└──", "│  ", "   ")
curved = Style("├──", "╰──", "│  ", "   ")


class WebNodeError(Exception): pass
class WebNodeEmptyError(WebNodeError): pass
class WebNodeMultipleError(WebNodeError): pass


class WebNodeMeta(ABCMeta):
    def __repr__(cls):
        renderer = cls.renderer(style=cls.__style__)
        rows = [pre + "|".join(key, value) for pre, key, value in renderer]
        return "\n".format(rows)

    def __new__(mcs, name, bases, attrs, *args, **kwargs):
        cls = super(WebNodeMeta, mcs).__new__(mcs, name, bases, attrs)
        if not any([type(base) is WebNodeMeta for base in bases]):
            return cls
        assert type(bases[0]) is WebNodeMeta
        assert all([type(base) is not WebNodeMeta for base in bases])
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
            setattr(bases[0], kwargs["key"], cls)
            return
        cls.__collection__ = kwargs.get("collection", getattr(cls, "__collection__", False))
        cls.__parameters__ = kwargs.get("parameters", getattr(cls, "__parameters__", {}))
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))
        cls.__parser__ = kwargs.get("parser", getattr(cls, "__parser__", None))
        cls.__style__ = kwargs.get("style", getattr(cls, "__style__", single))
        cls.__key__ = kwargs.get("key", getattr(cls, "__key__", None))

    def locate(cls, source):
        pass

    def create(cls, contents):
        pass

    def renderer(cls, layers=[], style=single):
        aslist = lambda x: [x] if not isinstance(x, list) else x
        last = lambda i, x: i == x
        pre = lambda i, x: style.terminate if last(i, x) else style.blank
        pads = lambda: ''.join([style.blank if layer else style.run for layer in layers])
        func = lambda i, x: "".join([pads(), pre(index, count)])
        if not layers:
            yield "", None, str(cls.__name__)
        count = len(cls.__children__) - 1
        for index, (key, values) in enumerate(cls.__children__.items()):
            for value in aslist(values):
                yield func(index, count), str(key), str(value.__name__)
                yield from value.renderer(layers=[*layers, last(index, count)], style=style)


class WebNode(ABC, metaclass=WebNodeMeta):
    def __setitem__(self, key, value): self.set(key, value)
    def __getitem__(self, key): return self.get(key)
    def __reversed__(self): return reversed(self.items())
    def __iter__(self): return iter(self.items())

    @staticmethod
    @abstractmethod
    def locator(source, *args, locator, **kwargs): pass


class WebELMT(WebNode, ABC, key="Element"):
    @staticmethod
    def locator(source, *args, locator, timeout=5, **kwargs):
        try:
            elements = WebDriverWait(source, timeout).until(EC.presence_of_all_elements_located((By.XPATH, locator)))
        except (NoSuchElementException, TimeoutException, WebDriverException):
            elements = []
        yield from iter(elements)


class WebELMTInput(WebELMT, ABC, key="Input"): pass
class WebELMTSelect(WebELMT, ABC, key="Select"): pass
class WebELMTCaptcha(WebELMT, ABC, key="Captcha"): pass
class WebELMTCheckBox(WebELMT, ABC, key="CheckBox"): pass
class WebELMTClickable(WebELMT, ABC, key="Clickable"): pass


class WebHTML(WebNode, ABC, key="Html"):
    @staticmethod
    def locator(source, *args, locator, removal=None, **kwargs):
        elements = [element.remove(removal) if bool(removal) else element for element in source.xpath(locator)]
        yield from iter(elements)


class WebHTMLText(WebHTML, ABC, key="Text"): pass
class WebHTMLLink(WebHTML, ABC, key="Link"): pass
class WebHTMLTable(WebHTML, ABC, key="Table"): pass


class WebJSON(WebNode, ABC, key="Json"):
    @staticmethod
    def locator(source, locator):
        aslist = lambda x: [x] if not isinstance(x, list) else x
        elements = copy(source)
        for key in str(locator).strip("/").split("/"):
            if isinstance(elements, list):
                elements = [element[key] for element in elements if (key in element.keys() if isinstance(element, dict) else False)]
                if not elements:
                    return
            elif isinstance(elements, dict):
                elements = elements[key] if key in elements else None
                if elements is None:
                    return
        yield from iter(aslist(elements))


class WebJSONText(WebJSON, ABC, key="Text"): pass
class WebJSONDict(WebJSON, ABC, key="Dict"): pass








