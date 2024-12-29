# -*- coding: utf-8 -*-
"""
Created on Sat Dec 28 2024
@name:   WebDynamic Objects
@author: Jack Kirby Cook

"""

import logging
from abc import ABC, ABCMeta, abstractmethod

from support.meta import ParametersMeta, AttributeMeta, TreeMeta
from support.trees import MixedNode

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebELMT"]
__copyright__ = "Copyright 2024, Jack Kirby Cook"
__license__ = "MIT License"
__logger__ = logging.getLogger(__name__)


class WebDynamicMeta(ParametersMeta, AttributeMeta, TreeMeta, ABCMeta):
    def __init__(cls, name, bases, attrs, *args, **kwargs):
        super(WebDynamicMeta, cls).__init__(name, bases, attrs, *args, **kwargs)

    def __call__(cls, *args, **kwargs):
        pass


class WebDynamic(MixedNode, ABC, metaclass=WebDynamicMeta, parameters=["locator", "multiple", "optional"]):
    def __init_subclass__(cls, *args, **kwargs): pass
    def __init__(self, *args, locator, multiple, optional, **kwargs):
        super().__init__(*args, **kwargs)
        self.__optional = optional
        self.__multiple = multiple
        self.__locator = locator

    @property
    def optional(self): return self.__optional
    @property
    def multiple(self): return self.__multiple
    @property
    def locator(self): return self.__locator

















