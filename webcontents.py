# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 2024
@name:   WebContents Objects
@author: Jack Kirby Cook

"""

import json
import lxml.html
import pandas as pd
from abc import ABC, abstractmethod
from selenium.webdriver.support.ui import Select

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMTs", "WebHTMLs", "WebJSONs"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebContents(ABC):
    def __init_subclass__(cls, *args, **kwargs): pass

    def __str__(self): return str(self.string)
    def __init__(self, content, *args, **kwargs):
        self.__content = content

    @property
    def content(self): return self.__content

    @property
    @abstractmethod
    def string(self): pass


class WebELMTs(WebContents, ABC):
    @property
    def string(self): return self.element.get_attribute("outerHTML")
    @property
    def html(self): return lxml.html.fromstring(self.string)
    @property
    def element(self): return self.content


class WebElMTText(WebELMTs, ABC, attribute="Text"): pass
class WebELMTCaptcha(WebELMTs, ABC, attribute="Captcha"): pass
class WebELMTClickable(WebELMTs, ABC, attribute="Clickable"):
    def click(self): self.element.click()


class WebELMTCheckBox(WebELMTClickable, ABC, attribute="CheckBox"):
    @property
    def unchecked(self): return self.element.get_attribute("ariaChecked") not in ("true", "mixed")
    @property
    def checked(self): return self.element.get_attribute("ariaChecked") in ("true", "mixed")


class WebELMTButton(WebELMTClickable, ABC, attribute="Button"): pass
class WebELMTInput(WebELMTClickable, ABC, attribute="Input"):
    def fill(self, value): self.element.send_keys(value)
    def send(self): self.element.submit()
    def clear(self): self.element.clear()


class WebELMTSelect(WebELMTClickable, ABC, attribute="Select"):
    def __init__(self, contents, *args, **kwargs):
        super().__init__(contents, *args, **kwargs)
        self.__select = Select(contents)

    def sel(self, key): self.select.select_by_value(key)
    def isel(self, key): self.select.select_by_index(key)
    def clear(self): self.select.deselect_all()

    @property
    def select(self): return self.__select


class WebHTMLs(WebContents, ABC):
    @property
    def string(self): return lxml.html.tostring(self.html)
    @property
    def html(self): return self.content


class WebHTMLText(WebHTMLs, ABC, attribute="Text"):
    @property
    def text(self): return self.html.attrib["text"]

class WebHTMLLink(WebHTMLs, ABC, attribute="Link"):
    @property
    def link(self): return self.html.attrib["href"]

class WebHTMLTable(WebHTMLs, ABC, attribute="Table"):
    @property
    def table(self): return pd.concat(pd.read_html(self.string, header=0), axis=0)


class WebJSONs(WebContents, ABC):
    @property
    def string(self): return json.dumps(self.json, sort_keys=True, indent=3, separators=(',', ' : '), default=str)
    @property
    def json(self): return self.content





