# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 2024
@name:   WebDatas Objects
@author: Jack Kirby Cook

"""

import json
import logging
import lxml.html
import pandas as pd
from abc import ABC, ABCMeta, abstractmethod
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from support.meta import ParametersMeta
from support.trees import MixedNode

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMT", "WebHTML", "WebJSON"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebSourcingErrorMeta(type):
    def __init__(cls, name, bases, attrs, *args, title=None, **kwargs):
        assert str(name).endswith("Error")
        super(WebSourcingErrorMeta, cls).__init__(name, bases, attrs)
        cls.__logger__ = __logger__
        cls.__title__ = title

    def __call__(cls, source):
        instance = super(WebSourcingErrorMeta, cls).__call__(source)
        cls.logger.info(f"{cls.title}: {repr(source)}")
        return instance

    @property
    def logger(cls): return cls.__logger__
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


class WebSourcingMeta(ParametersMeta, ABCMeta):
    def __repr__(cls): return str(cls.__name__)
    def __str__(cls): return str(cls.__key__)

    def __init__(cls, name, bases, attrs, *args, **kwargs):
        super(WebSourcingMeta, cls).__init__(name, bases, attrs, *args, **kwargs)
        dependents = {str(dependent): dependent for dependent in attrs.values() if type(dependent) is WebSourcingMeta}
        cls.__dependents__ = getattr(cls, "__dependents__", {}) | dependents
        cls.__optional__ = kwargs.get("optional", getattr(cls, "__optional__", False))
        cls.__multiple__ = kwargs.get("multiple", getattr(cls, "__multiple__", False))
        cls.__locator__ = kwargs.get("locator", getattr(cls, "__locator__", None))
        cls.__key__ = kwargs.get("key", getattr(cls, "__key__", None))

    def __call__(cls, sources, *args, **kwargs):
        sources = [source for source in cls.locate(sources, *args, **kwargs)]
        if not bool(sources) and not cls.optional: raise WebSourcingMissingError(cls)
        if len(sources) > 1 and not cls.multiple: raise WebSourcingMultipleError(cls)
        instances = [super(WebSourcingMeta, cls).__call__(source, *args, **kwargs) for source in sources]
        for source, instance in zip(sources, instances):
            for key, dependent in cls.dependents.items():
                instance[key] = dependent(source, *args, **kwargs)
        return (instances[0] if bool(instances) else None) if not bool(cls.multiple) else list(instances)

    @property
    def dependents(cls): return cls.__dependents__
    @property
    def optional(cls): return cls.__optional__
    @property
    def multiple(cls): return cls.__multiple__
    @property
    def locator(cls): return cls.__locator__


class WebSourcing(MixedNode, ABC, metaclass=WebSourcingMeta):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, source, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__source = source

    def __call__(self, *args, **kwargs): return self.execute(*args, **kwargs)
    def __str__(self): return str(self.string)

    @classmethod
    @abstractmethod
    def locate(cls, source, *args, **kwargs): pass
    @abstractmethod
    def execute(self, *args, **kwargs): pass
    @property
    @abstractmethod
    def string(self): pass

    @property
    def source(self): return self.__source


class WebData(WebSourcing, ABC):
    def execute(self, *args, **kwargs): return {key: value(*args, **kwargs) for key, value in self.children.items()}

class WebAction(WebSourcing, ABC):
    def execute(self, *args, **kwargs): pass

class WebContent(WebSourcing, ABC, parameters=["parser"]):
    def __init__(self, *args, parser, **kwargs):
        super().__init__(*args, **kwargs)
        self.__parser = parser

    def execute(self, *args, **kwargs): return self.parse(self.data)
    def parse(self, data): return self.parser(data)

    @property
    @abstractmethod
    def data(self): pass
    @property
    def parser(self): return self.__parser


class WebELMT(WebData, ABC):
    def __init_subclass__(cls, *args, attribute=None, **kwargs):
        if attribute is not None: setattr(WebELMT, attribute, cls)

    @classmethod
    def locate(cls, source, *args, timeout=5, **kwargs):
        located = EC.presence_of_all_elements_located((By.XPATH, cls.locator))
        try: contents = WebDriverWait(source, timeout).until(located)
        except (NoSuchElementException, TimeoutException, WebDriverException): contents = []
        yield from iter(contents)

    @property
    def string(self): return self.element.get_attribute("outerHTML")
    @property
    def html(self): return lxml.html.fromstring(self.string)
    @property
    def element(self): return self.source


class WebHTML(WebData, ABC):
    def __init_subclass__(cls, *args, attribute=None, **kwargs):
        if attribute is not None: setattr(WebHTML, attribute, cls)

    @classmethod
    def locate(cls, source, *args, **kwargs):
        contents = list(source.xpath(cls.locator))
        yield from iter(contents)

    @property
    def string(self): return lxml.html.tostring(self.html)
    @property
    def html(self): return self.source


class WebJSON(WebData, ABC):
    def __init_subclass__(cls, *args, attribute=None, **kwargs):
        if attribute is not None: setattr(WebJSON, attribute, cls)

    @classmethod
    def locate(cls, source, *args, **kwargs):
        locators = str(cls.locator).lstrip("//").rstrip("[]").split("/")
        contents = source[str(locators.pop(0))]
        for locator in locators: contents = contents[str(locator)]
        if isinstance(contents, dict): yield from iter(contents.items())
        elif isinstance(contents, (tuple, list)): yield from iter(contents)
        elif isinstance(contents, (str, int, float)): yield contents
        else: raise TypeError(type(contents))

    @property
    def string(self): return json.dumps(self.json, sort_keys=True, indent=3, separators=(',', ' : '), default=str)
    @property
    def json(self): return self.source


class WebELMTClickable(WebAction, WebELMT, attribute="Clickable"):
    def click(self): self.element.click()


class WebELMTButton(WebELMTClickable, attribute="Button"): pass
class WebELMTInput(WebELMTClickable, attribute="Input"):
    def fill(self, value): self.element.send_keys(value)
    def send(self): self.element.submit()
    def clear(self): self.element.clear()


class WebELMTCaptcha(WebAction, WebELMT, ABC, attribute="Captcha"): pass
class WebElMTText(WebContent, WebELMT, ABC, attribute="Text"):
    @property
    def text(self): return self.element.get_attribute("text")
    @property
    def data(self): return self.text


class WebHTMLText(WebContent, WebHTML, ABC, attribute="Text"):
    @property
    def text(self): return self.html.attrib["text"]
    @property
    def data(self): return self.text

class WebHTMLLink(WebContent, WebHTML, ABC, attribute="Link"):
    @property
    def link(self): return self.html.attrib["href"]
    @property
    def data(self): return self.link

class WebHTMLTable(WebContent, WebHTML, ABC, attribute="Table"):
    @property
    def table(self): return pd.concat(pd.read_html(self.string, header=0, index_col=None), axis=0)
    @property
    def data(self): return self.table

class WebJsonText(WebContent, WebJSON, ABC, attribute="Text"):
    @property
    def text(self): return str(self.json)
    @property
    def data(self): return self.text




