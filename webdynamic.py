# -*- coding: utf-8 -*-
"""
Created on Sat Dec 28 2024
@name:   WebDynamic Objects
@author: Jack Kirby Cook

"""

import types
import lxml.html
from abc import ABC, abstractmethod
from selenium.common.exceptions import StaleElementReferenceException

from webscraping.websourcing import WebContents, WebSourcing, SourcingType
from support.meta import AttributeMeta, RegistryMeta, TreeMeta
from support.trees import ParentalNode
from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMT"]
__copyright__ = "Copyright 2024, Jack Kirby Cook"
__license__ = "MIT License"


class WebDynamicMeta(RegistryMeta, AttributeMeta, TreeMeta):
    def __init__(cls, name, bases, attrs, *args, **kwargs):
#        dependents = list(cls.revise(*args, **kwargs))
#        parameters = dict(dependents=dependents)
#        super(WebDynamicMeta, cls).__init__(name, bases, attrs, *args, **parameters, **kwargs)
        super(WebDynamicMeta, cls).__init__(name, bases, attrs, *args, **kwargs)
        if ABC in bases: cls.__sourcing__ = cls.customize(*args, **kwargs)
        else: cls.__sourcing__ = cls.finalize(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        multiple = bool(cls.sourcing.multiple)
        cls = type(cls.__name__, (cls[multiple], *cls.__bases__), {})
        parameters = dict(sourcing=cls.sourcing, dependents=cls.dependents)
        instance = super(WebDynamicMeta, cls).__call__(*args, **parameters, **kwargs)
        return instance

    def customize(cls, *args, sourcingtype=None, **kwargs):
        assert isinstance(sourcingtype, (SourcingType, types.NoneType))
        if isinstance(sourcingtype, SourcingType): return WebSourcing[sourcingtype]
        else: return getattr(cls, "__sourcing__", None)

    def finalize(cls, *args, **kwargs):
        assert not isinstance(cls.sourcing, types.NoneType)
        return cls.sourcing(*args, **kwargs)

    @property
    def sourcing(cls): return cls.__sourcing__

#    def revise(cls, *args, locators={}, **kwargs):
#        for key, locator in locators.items():
#            try: dependent = cls.dependents[key]
#            except KeyError: continue
#            name = f"{repr(dependent)}{str(key).title()}"
#            multiple = dependent.sourcing.multiple
#            optional = dependent.sourcing.optional
#            parameters = dict(locator=locator, multiple=multiple, optional=optional)
#            dependent = type(name, tuple([dependent]), {}, **parameters)
#            yield dependent


class WebDynamic(ParentalNode, Logging, ABC, metaclass=WebDynamicMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return self.string
    def __init__(self, *args, sourcing, dependents, timeout=10, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dependents = dependents
        self.__sourcing = sourcing
        self.__timeout = timeout

    @property
    @abstractmethod
    def string(self): pass

    @property
    def dependents(self): return self.__dependents
    @property
    def sourcing(self): return self.__sourcing
    @property
    def timeout(self): return self.__timeout


class WebDynamicMultiple(WebDynamic, ABC, register=True):
    pass

#    def __getitem__(self, index):
#        assert isinstance(index, int)
#        generator = self.sourcing(self.source, timeout=self.timeout)
#        source = list(generator)[index]
#        children = {key: dependent(source) for key, dependent in self.dependents.items()}
#        for key, child in children.items(): self[key] = child
#        return children

class WebDynamicSingle(WebDynamic, ABC, register=False):
    pass

#    def __getitem__(self, key):
#        assert isinstance(key, str)
#        generator = self.sourcing(self.source, timeout=self.timeout)
#        source = list(generator)[0]
#        child = self.dependents[key](source)
#        self[key] = child
#        return child


class WebELMT(WebContents.Multiple, WebDynamic, ABC, sourcing=WebSourcing.ELMT, root=True):
    @property
    def stale(self):
        try: self.element.is_displayed()
        except StaleElementReferenceException: return True
        else: return False

    @property
    def string(self): return self.element.get_attribute("outerHTML")
    @property
    def html(self): return lxml.html.fromstring(self.string)
    @property
    def element(self): return self.source


class WebELMTText(WebContents.Single, WebELMT, ABC, attribute="Text"):
    @property
    def text(self): return self.element.get_attribute("text")
    @property
    def content(self): return self.content


class WebELMTClickable(WebELMTText, ABC, attribute="Clickable"):
    def click(self): self.element.click()


class WebELMTButton(WebELMTClickable, ABC, attribute="Button"): pass
class WebELMTInput(WebELMTClickable, ABC, attribute="Input"):
    def fill(self, value): self.element.send_keys(str(value))
    def send(self): self.element.submit()
    def clear(self): self.element.clear()


class WebELMTToggle(WebELMTClickable, ABC, attribute="Toggle"):
    def select(self, value):
        if not str(self.content) != str(value): self.element.click()
        assert str(self.content) == str(value)


# class WebELMTMenu(WebELMTClickable, key="menu", multiple=True, optional=False): pass
# class WebELMTDropdown(WebELMTClickable, ABC, attribute="Dropdown", dependents=[WebELMTMenu]):
#     def select(self, value):
#         pass


# def select(self, value):
#     self.click()
#     dropdown = type(self).Dropdown(self.source, timeout=self.timeout)
#     generator = self.sourcing(self.source, timeout=self.timeout)
#     sources = list(generator)
#     source = sources[index]
#     children = self.create(source)
#     return children
#     elements = [element for element in self.locate(self.element, locator=self.locator[1], timeout=self.timeout)]
#     text = lambda element: self.parser(element.get_attribute("text"))
#     elements = {text(element): element for element in elements}
#     elements[value].click()


