# -*- coding: utf-8 -*-
"""
Created on Sat Feb 28 2026
@name:   WebSupport Objects
@author: Jack Kirby Cook

"""

import time
import multiprocessing
from abc import ABC, abstractmethod
from functools import update_wrapper

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebSource", "WebDelayer"]
__copyright__ = "Copyright 2026, Jack Kirby Cook"
__license__ = "MIT License"


class WebDelayer(object):
    def __init__(self, *args, delay, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(delay, int)
        self.__timer = time.monotonic()
        self.__delay = int(delay)

    def __enter__(self):
        elapsed = time.monotonic() - self.timer
        delay = max(self.delay - elapsed, 0)
        time.sleep(delay)
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.timer = time.monotonic()

    @staticmethod
    def register(method):
        def wrapper(instance, *args, **kwargs):
            if instance.delayer is None: return method(instance, *args, **kwargs)
            with instance.delayer: return method(instance, *args, **kwargs)
        update_wrapper(wrapper, method)
        return wrapper

    @property
    def delay(self): return self.__delay
    @property
    def timer(self): return self.__timer
    @timer.setter
    def timer(self, timer): self.__timer = timer


class WebSource(ABC):
    def __bool__(self): return self.source is not None
    def __init__(self, *args, delay=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__delayer = WebDelayer(delay=delay) if delay is not None else None
        self.__mutex = multiprocessing.Lock()
        self.__timer = time.monotonic()
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
    @property
    def delayer(self): return self.__delayer


