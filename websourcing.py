# -*- coding: utf-8 -*-
"""
Created on Sat Jan 4 2025
@name:   WebSourcing Objects
@author: Jack Kirby Cook

"""

import types
from enum import StrEnum
from abc import ABC, abstractmethod
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from support.meta import RegistryMeta, AttributeMeta
from support.trees import ParentalNode
from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebSourcing", "WebContents", "SourcingType", "ContentsType"]
__copyright__ = "Copyright 2024, Jack Kirby Cook"
__license__ = "MIT License"


SourcingType = StrEnum("SourcingType", "ELMT HTML JSON")
ContentsType = StrEnum("ContentsType", "SINGLE MULTIPLE")


class WebSourcingErrorMeta(type):
    def __init__(cls, name, bases, attrs, *args, title=None, **kwargs):
        assert str(name).endswith("Error")
        super(WebSourcingErrorMeta, cls).__init__(name, bases, attrs)
        cls.__title__ = title

    def __call__(cls, source):
        instance = super(WebSourcingErrorMeta, cls).__call__(source)
        source.logger.info(f"{cls.title}: {repr(source)}")
        return instance

    @property
    def title(cls): return cls.__title__
    @property
    def name(cls): return cls.__name__


class WebSourcingError(Exception, metaclass=WebSourcingErrorMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __str__(self): return f"{type(self).name}|{repr(self.source)}"
    def __init__(self, source): self.__source = source

    @property
    def source(self): return self.__source


class WebSourcingMissingError(WebSourcingError, title="Missing"): pass
class WebSourcingMultipleError(WebSourcingError, title="Multiple"): pass


class WebSourcing(Logging, ABC, metaclass=RegistryMeta):
    def __init__(self, *args, locator, multiple=False, optional=False, **kwargs):
        assert not isinstance(locator, types.NoneType)
        super().__init__(*args, **kwargs)
        self.__optional = optional
        self.__multiple = multiple
        self.__locator = locator

    def __call__(self, source, *args, **kwargs):
        sources = [source for source in self.locate(source, *args, locator=self.locator, **kwargs)]
        if not bool(sources) and not self.optional: raise WebSourcingMissingError(self)
        if len(sources) > 1 and not self.multiple: raise WebSourcingMultipleError(self)
        yield from sources

    @abstractmethod
    def locate(self, source, *args, **kwargs): pass

    @property
    def optional(self): return self.__optional
    @property
    def multiple(self): return self.__multiple
    @property
    def locator(self): return self.__locator


class WebHTMLSourcing(WebSourcing, registry=SourcingType.HTML):
    def locate(self, source, *args, **kwargs):
        contents = list(source.xpath(self.locator))
        yield from iter(contents)


class WebJSONSourcing(WebSourcing, registry=SourcingType.JSON):
    def locate(self, source, *args, **kwargs):
        locators = str(self.locator).lstrip("//").rstrip("[]").split("/")
        contents = source[str(locators.pop(0))]
        for locator in locators: contents = contents[str(locator)]
        if isinstance(contents, (tuple, list)): yield from iter(contents)
        elif isinstance(contents, (str, int, float)): yield contents
        elif isinstance(contents, dict): yield contents
        else: raise TypeError(type(contents))


class WebELMTSourcing(WebSourcing, registry=SourcingType.ELMT):
    def locate(self, source, *args, timeout, **kwargs):
        locator = tuple([By.XPATH, self.locator])
        located = EC.presence_of_all_elements_located(locator)
        try: contents = WebDriverWait(source, timeout).until(located)
        except (NoSuchElementException, TimeoutException, WebDriverException): contents = []
        yield from iter(contents)


class WebContents(ParentalNode, ABC, metaclass=AttributeMeta):
    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)


class WebMultipleContents(WebContents, attribute=str(ContentsType.MULTIPLE).title()):
    def execute(self, *args, **kwargs): return {key: value(*args, **kwargs) for key, value in iter(self)}


class WebSingleContents(WebContents, attribute=str(ContentsType.SINGLE).title()):
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.parser = kwargs.get("parser", getattr(cls, "parser", lambda content: content))

    def execute(self, *args, **kwargs): return self.parse(self.content, *args, **kwargs)
    def parse(self, content, *args, **kwargs): return self.parser(content)

    @property
    @abstractmethod
    def content(self): pass

