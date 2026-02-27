# -*- coding: utf-8 -*-
"""
Created on Thurs Feb 26 2026
@name:   WebSource Objects
@author: Jack Kirby Cook

"""

import multiprocessing
from abc import ABC, abstractmethod

from support.mixins import Logging, Counting

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebSource", "WebDelayer"]
__copyright__ = "Copyright 2026, Jack Kirby Cook"
__license__ = "MIT License"


class WebDelayer(Logging, title="Waiting"):
    def __init__(self, delay, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert isinstance(delay, int)
        self.__timer = time.monotonic()
        self.__delay = int(delay)

    def __enter__(self):
        elapsed = time.monotonic() - self.timer
        delay = max(self.delay - elapsed, 0)
        self.console(f"{delay:.2f} seconds")
        time.sleep(delay)
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.timer = time.monotonic()

    @property
    def delay(self): return self.__delay
    @property
    def timer(self): return self.__timer
    @timer.setter
    def timer(self, timer): self.__timer = timer


class WebSource(Counting, Logging, ABC):
    def __bool__(self): return self.source is not None
    def __init__(self, *args, account=None, authenticator=None, delayer=None, **kwargs):
        if account is not None: assert all([hasattr(account, attr) for attr in ["identity", "username", "password"]])
        if authenticator is not None: assert all([hasattr(account, attr) for attr in ["identity", "code"]])
        super().__init__(*args, **kwargs)
        self.__mutex = multiprocessing.Lock()
        self.__authenticator = authenticator
        self.__account = account
        self.__delayer = delayer
        self.__source = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.stop()

    @abstractmethod
    def start(self): pass
    @abstractmethod
    def stop(self): pass

    @property
    def source(self): return self.__source
    @source.setter
    def source(self, source): self.__source = source

    @property
    def authenticator(self): return self.__authenticator
    @property
    def account(self): return self.__account
    @property
    def delayer(self): return self.__delayer
    @property
    def mutex(self): return self.__mutex

