# -*- coding: utf-8 -*-
"""
Created on Sat Feb 28 2026
@name:   WebSupport Objects
@author: Jack Kirby Cook

"""

import multiprocessing
from abc import ABC, abstractmethod

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebSource"]
__copyright__ = "Copyright 2026, Jack Kirby Cook"
__license__ = "MIT License"


class WebSource(ABC):
    def __bool__(self): return self.source is not None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__mutex = multiprocessing.Lock()
        self.__source = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.stop()

    @abstractmethod
    def load(self, *args, **kwargs): pass
    @abstractmethod
    def start(self): pass
    @abstractmethod
    def stop(self): pass

    @property
    def source(self): return self.__source
    @source.setter
    def source(self, source): self.__source = source
    @property
    def mutex(self): return self.__mutex


