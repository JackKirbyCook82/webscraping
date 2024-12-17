# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 2024
@name:   WebSource Objects
@author: Jack Kirby Cook

"""

import types
import inspect
import logging
from abc import ABC, ABCMeta, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC

from support.trees import LinearSingleNode

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMT", "WebHTML", "WebJSON"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebSourceErrorMeta(type):
    def __init__(cls, name, bases, attrs, *args, title=None, **kwargs):
        assert str(name).endswith("Error")
        super(WebSourceErrorMeta, cls).__init__(name, bases, attrs)
        cls.__logger__ = __logger__
        cls.__title__ = title

    def __call__(cls, source):
        instance = super(WebSourceErrorMeta, cls).__call__(cls.__name__, source)
        cls.logger.info(f"{cls.title}: {repr(instance.source)}")
        return instance

    @property
    def logger(cls): return cls.__logger__
    @property
    def title(cls): return cls.__title__


class WebSourceError(Exception, metaclass=WebSourceErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return f"{self.name}|{repr(self.source)}"
    def __init__(self, name, source):
        self.__source = source
        self.__name = name

    @property
    def source(self): return self.__source
    @property
    def name(self): return self.__name


class WebSourceMissingError(WebSourceError, title="Missing"): pass
class WebSourceMultipleError(WebSourceError, title="Multiple"): pass


class WebSourceMeta(ABCMeta):
    def __repr__(cls): return str(cls.__name__)
    def __str__(cls): return str(cls.__key__)

    def __init__(cls, name, bases, attrs, *args, **kwargs):
        super(WebSourceMeta, cls).__init__(name, bases, attrs, *args, **kwargs)
        if not any([type(base) is WebSourceMeta for base in bases]):
            return
        dependents = {str(dependent): dependent for dependent in attrs.values() if type(dependent) is WebSourceMeta}
        dependents = getattr(cls, "__dependents__", {}) | dependents
        parameters = dict(getattr(cls, "__parameters__", {}).items())
        locator = kwargs.get("locator", parameters.get("locator", None))
        multiple = kwargs.get("multiple", parameters.get("multiple", False))
        optional = kwargs.get("optional", parameters.get("optional", False))
        cls.__parameters__ = parameters | dict(locator=locator, multiple=multiple, optional=optional)
        cls.__dependents__ = getattr(cls, "__dependents__", {}) | dependents
        cls.__key__ = kwargs.get("key", getattr(cls, "__key__", None))

    def __call__(cls, *args, **kwargs):
        instance = super(WebSourceMeta, cls).__call__(*args, **cls.parameters, **kwargs)
        for key, dependent in cls.dependents.items():
            instance[key] = dependent(*args, **kwargs)
        return instance

    @property
    def parameters(cls): return cls.__parameters__
    @property
    def dependents(cls): return cls.__dependents__
    @property
    def key(cls): return cls.__key__


class WebSource(LinearSingleNode, ABC, metaclass=WebSourceMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, *args, locator, multiple, optional, **kwargs):
        self.__optional = optional
        self.__multiple = multiple
        self.__locator = locator

    def __call__(self, source, *args, **kwargs):
        pass

    @abstractmethod
    def execute(self, *args, **kwargs): pass

    @property
    def optional(self): return self.__optional
    @property
    def multiple(self): return self.__multiple
    @property
    def locator(self): return self.__locator


class WebELMT(WebSource, ABC):
    def execute(self, source, *args, **kwargs):
        try: contents = WebDriverWait(source, self.timeout).until(EC.presence_of_all_elements_located((By.XPATH, self.locator)))
        except (NoSuchElementException, TimeoutException, WebDriverException): contents = []
        yield from iter(contents)


class WebHTML(WebSource, ABC):
    def execute(self, source, *args, **kwargs):
        contents = list(source.xpath(self.locator))
        yield from iter(contents)


class WebJSON(WebSource, ABC):
    def execute(self, source, *args, **kwargs):
        locators = str(self.locator).lstrip("//").rstrip("[]").split("/")
        contents = source[str(locators.pop(0))]
        for locator in locators: contents = contents[str(locator)]
        if isinstance(contents, dict()): yield from iter(contents.items())
        elif isinstance(contents, (tuple, list)): yield from iter(contents)
        elif isinstance(contents, str): yield contents
        else: raise TypeError(type(contents))




