# -*- coding: utf-8 -*-
"""
Created on Mon Mar 2 2026
@name:   WebSubscription Objects
@author: Jack Kirby Cook

"""

from abc import ABC
from collections import OrderedDict as ODict

from webscraping.websupport import WebSource, WebDelayer

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebSubscription"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebSubscription(WebSource, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__subscription = ODict()

    def __bool__(self): return bool(self.subscription)
    def __len__(self): return len(self.subscription)

    def __setitem__(self, key, value): self.subscription[key] = value
    def __contains__(self, key): return key in self.subscription
    def __getitem__(self, key): return self.subscription[key]
    def __delitem__(self, key): del self.subscription[key]

    @property
    def subscription(self): return self.__subscription
    @response.setter
    def subscription(self, subscription): self.__subscription = subscription



