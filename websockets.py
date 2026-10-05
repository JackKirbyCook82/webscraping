# -*- coding: utf-8 -*-
"""
Created on Sun Oct 4 2026
@name:   WebSocket Objects
@author: Jack Kirby Cook
@file:   webscraping\webreaders.py

"""

from abc import ABC

from webscraping.websources import WebSOCKSource

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebSocket"]
__copyright__ = "Copyright 2026, Jack Kirby Cook"
__license__ = "MIT License"


class WebSocket(WebSOCKSource, ABC):
    def __init__(self, *args, host, port, client=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__client = client
        self.__host = host
        self.__port = port

    @property
    def client(self): return self.__client
    @property
    def host(self): return self.__host
    @property
    def port(self): return self.__port



