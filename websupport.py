# -*- coding: utf-8 -*-
"""
Created on Sat Feb 28 2026
@name:   WebSupport Objects
@author: Jack Kirby Cook

"""

import multiprocessing
from types import SimpleNamespace
from abc import ABC, abstractmethod

from support.mixins import Logging, Counting

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebDelayer", "WebDownloader"]
__copyright__ = "Copyright 2026, Jack Kirby Cook"
__license__ = "MIT License"


class WebSourceMissingError(Exception): pass
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
    def authenticator(self): return self.__authenticator
    @property
    def account(self): return self.__account
    @property
    def delayer(self): return self.__delayer
    @property
    def mutex(self): return self.__mutex


class WebDownloader(Sizing, Emptying, Partition, Logging, ABC, title="Downloaded"):
    def __init_subclass__(cls, *args, pages={}, page=None, **kwargs):
        assert isinstance(pages, dict)
        super().__init_subclass__(*args, **kwargs)
        cls.__Pages__ = pages
        cls.__Page__ = page

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__pages = SimpleNamespace(**{key: value(*args, **kwargs) for key, value in self.Pages.items()})
        self.__page = self.Page(*args, **kwargs) if self.Page is not None else None

    @staticmethod
    def querys(querys, querytype):
        assert isinstance(querys, (list, dict, querytype))
        assert all([isinstance(query, querytype) for query in querys]) if isinstance(querys, (list, dict)) else True
        if isinstance(querys, querytype): querys = [querys]
        elif isinstance(querys, dict): querys = SODict(querys)
        else: querys = list(querys)
        return querys

    @property
    def Pages(self): return self.__Pages
    @property
    def Page(self): return self.__Page

    @property
    def pages(self): return self.__pages
    @property
    def page(self): return self.__page


class WebDelayerMissingError(Exception): pass
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

    @staticmethod
    def register(method):
        def wrapper(instance, *args, **kwargs):
            if not isinstance(instance, WebSource): raise WebSourceMissingError()
            if not hasattr(instance, "delayer"): raise WebDelayerMissingError()
            with instance.delayer: return method(instance, *args, **kwargs)
        update_wrapper(wrapper, method)
        return wrapper

    @property
    def delay(self): return self.__delay
    @property
    def timer(self): return self.__timer
    @timer.setter
    def timer(self, timer): self.__timer = timer


