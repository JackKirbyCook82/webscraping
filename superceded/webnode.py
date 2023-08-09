# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebNode Objects
@author: Jack Kirby Cook

"""

from copy import copy
from abc import ABC, ABCMeta
from collections import namedtuple as ntuple
from collections import OrderedDict as ODict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from lxml.html import HtmlElement as StaticElement
from selenium.webdriver.chrome.webdriver import WebDriver as DynamicDriver
from selenium.webdriver.remote.webelement import WebElement as DynamicElement

from utilities.mixins import Node
from utilities.dispatchers import typedispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebNode", "WebNodeError"]
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

    def __init__(cls, *args, children=[], kwargs):
        children = ODict([(child.__key__, child) for child in children])
        cls.__children__ = getattr(cls, "__children__", {})
        cls.__children__.update(children)
        cls.__iterable__ = kwargs.get("iterable", getattr(cls, "__iterable__", False))
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))
        cls.__style__ = kwargs.get("style", getattr(cls, "__style__", single))
        cls.__key__ = kwargs.get("key", getattr(cls, "__key__", None))
#        cls.__dom__ = kwargs.get("dom", getattr(cls, "__dom__", None))

    def __call__(cls, source):
        webdoms = [cls.create(element) for element in cls.locate(source)]
        if not bool(webdoms) and not cls.__optional__:
            raise WebNodeEmptyError()
        if len(webdoms) > 1 and not cls.__iterable__:
            raise WebNodeMultipleError()
        instances = [super(WebNodeMeta, cls).__call__(webdom, variant=type(source)) for webdom in webdoms]
        for instance in instances:
            for key, subcls in cls.__children__.items():
                subinstances = subcls(instance.dom)
                instance[key] = subinstances
        return (instances[0] if bool(instances) else None) if cls.__iterable__ else instances

    def renderer(cls, layers=[], style=single):
        aslist = lambda x: [x] if not isinstance(x, list) else x
        last = lambda i, x: i == x
        pre = lambda i, x: style.terminate if last(i, x) else style.blank
        pads = lambda: ''.join([style.blank if layer else style.run for layer in layers])
        func = lambda i, x: "".join([pads(), pre(index, count)])
        if not layers:
            yield "", None, cls.__name__
        count = len(cls.__children__) - 1
        for index, (key, values) in enumerate(cls.__children__.items()):
            for value in aslist(values):
                yield func(index, count), str(key), value.__name__
                yield from value.renderer(layers=[*layers, last(index, count)], style=style)

    @typedispatcher
    def locate(cls, source): raise TypeError(type(source).__name__)
    def create(cls, element): return cls.__dom__(element)

    @locate.register(StaticElement)
    def static(cls, source, *args, **kwargs):
        locator, removal = cls.__locator__, kwargs.get("removal", None)
        elements = [element.remove(removal) if bool(removal) else element for element in source.xpath(locator)]
        yield from iter(elements)

    @locate.register(DynamicElement, DynamicDriver)
    def dynamic(cls, source, *args, **kwargs):
        locator, timeout = cls.__locator__, kwargs.get("timeout", 5)
        try:
            elements = WebDriverWait(source, timeout).until(EC.presence_of_all_elements_located((By.XPATH, locator)))
        except (NoSuchElementException, TimeoutException, WebDriverException):
            elements = []
        yield from iter(elements)

    @locate.register(dict, list, str, float, int)
    def json(cls, source):
        locator = str(cls.__locator__).strip("/").split("/")
        aslist = lambda x: [x] if not isinstance(x, list) else x
        elements = copy(source)
        for key in locator:
            if isinstance(elements, list):
                elements = [element[key] for element in elements if
                            (key in element.keys() if isinstance(element, dict) else False)]
                if not elements:
                    return
            elif isinstance(elements, dict):
                elements = elements[key] if key in elements else None
                if elements is None:
                    return
        yield from iter(aslist(elements))


class WebNode(Node, ABC, metaclass=WebNodeMeta):
#    def __repr__(self): return "{}|{}".format(self.name, self.type)
#    def __str__(self): return str(self.webdom)

    def __getattr__(self, attr): return getattr(self.webdom, attr)
    def __setitem__(self, key, value): self.set(key, value)
    def __getitem__(self, key): return self.get(key)

    def __reversed__(self): return reversed(self.items())
    def __iter__(self): return iter(self.items())

#    @property
#    def name(self): return super().name
#    @property
#    def type(self): return self.webdom.type
#    @property
#    def dom(self): return self.webdom.dom

#    @property
#    def webdom(self): return self.__webdom



