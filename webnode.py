# -*- coding: utf-8 -*-
"""
Created on Sat Aug 5 2023
@name:   WebNode Objects
@author: Jack Kirby Cook

"""

from abc import ABC, ABCMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebNodeMeta(ABCMeta):
    pass


class WebNode(ABC):
    pass


class WebElement(WebNode):
    pass


class WebHTML(WebNode):
    pass


class WebJSON(WebNode):
    pass




