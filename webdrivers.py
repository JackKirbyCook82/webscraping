# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDriver Objects
@author: Jack Kirby Cook

"""

import time
import lxml.html
import multiprocessing
import selenium.webdriver
from datetime import datetime as Datetime
from collections import namedtuple as ntuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

from support.decorators import Wrapper
from support.meta import SingletonMeta
from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebDriver", "WebBrowser"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebBrowser(object):
    Browser = ntuple("Browser", "name service driver options")
    Chrome = Browser("Chrome", ChromeService, selenium.webdriver.Chrome, selenium.webdriver.ChromeOptions)
    Firefox = Browser("Firefox", FirefoxService, selenium.webdriver.Firefox, selenium.webdriver.FirefoxOptions)


class WebDelayer(Wrapper):
    def wrapper(self, instance, *args, **kwargs):
        cls = type(instance)
        with cls.mutex: cls.wait(instance.delay)
        self.function(instance, *args, **kwargs)
        return self


class WebDriverMeta(SingletonMeta):
    def __init__(cls, *args, **kwargs):
        cls.__executable__ = kwargs.get("executable", getattr(cls, "__executable__", None))
        cls.__browser__ = kwargs.get("browser", getattr(cls, "__browser__", None))
        cls.__mutex__ = multiprocessing.RLock()
        cls.__timer__ = None

    def wait(cls, delay):
        assert isinstance(delay, int)
        if bool(cls.timer) and bool(delay):
            elapsed = (Datetime.now() - cls.timer).total_seconds()
            sleep = max(delay - elapsed, 0)
            time.sleep(sleep)
        cls.timer = Datetime.now()

    @property
    def timer(cls): return cls.__timer__
    @timer.setter
    def timer(cls, timer): cls.__timer__ = timer

    @property
    def executable(cls): return cls.__executable__
    @property
    def browser(cls): return cls.__browser__
    @property
    def delay(cls): return cls.__delay__
    @property
    def mutex(cls): return cls.__mutex__


class WebDriver(Logging, metaclass=WebDriverMeta):
    def __init_subclass__(cls, *args, **kwargs): pass

    def __repr__(self): return f"{self.name}|{self.browser.name}"
    def __bool__(self): return self.driver is not None

    def __init__(self, *args, timeout=60, delay=10, port=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__mutex = multiprocessing.Lock()
        self.__timeout = int(timeout)
        self.__delay = int(delay)
        self.__port = port
        self.__driver = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.stop()

    def __iter__(self):
        current = self.driver.current_window_handle
        for handle in list(self.driver.window_handles):
            self.driver.switch_to.window(handle)
            yield self.driver.title, handle
        self.driver.switch_to.window(current)

    def start(self):
        executable = self.executable
        options = self.browser.options()
        self.setup(options, port=self.port)
        service = self.browser.service(executable)
        driver = self.browser.driver(service=service, options=options)
        driver.set_page_load_timeout(self.timeout)
        driver.delete_all_cookies()
        self.driver = driver

    def stop(self):
        self.driver.quit()
        self.driver = None

    def load(self, url, *args, **kwargs):
        assert all([hasattr(url, attribute) for attribute in ("address", "parameters")])
        with self.mutex: self.driver.get(str(url))

    @staticmethod
    def setup(options, *args, port=None, **kwargs):
        if port is not None:
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{str(port)}")
        options.add_argument("log-level=3")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--ignore-certificate-errors-spki-list")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

    @WebDelayer
    def navigate(self, value):
        if isinstance(value, int): handle = list(self.driver.window_handles)[value]
        elif isinstance(value, str): handle = dict(self)[value]
        else: raise TypeError(type(value))
        self.driver.switch_to.window(handle)

    @WebDelayer
    def pageup(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.PAGE_UP)
    @WebDelayer
    def pagedown(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.PAGE_DOWN)
    @WebDelayer
    def pagehome(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.HOME)
    @WebDelayer
    def pageend(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.END)
    @WebDelayer
    def maximize(self): self.driver.maximize_window()
    @WebDelayer
    def minimize(self): self.driver.minimize_window()
    @WebDelayer
    def refresh(self): self.driver.refresh()
    @WebDelayer
    def forward(self): self.driver.foward()
    @WebDelayer
    def back(self): self.driver.back()

    @property
    def response(self): return [request.response for request in self.driver.requests]
    @property
    def request(self): return [request for request in self.driver.requests]
    @property
    def html(self): return lxml.html.fromstring(self.driver.page_source)
    @property
    def text(self): return self.driver.page_source
    @property
    def url(self): return self.driver.current_url

    @property
    def driver(self): return self.__driver
    @driver.setter
    def driver(self, driver): self.__driver = driver

    @property
    def executable(self): return type(self).__executable__
    @property
    def browser(self): return type(self).__browser__
    @property
    def element(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
    @property
    def delay(self): return self.__delay
    @property
    def mutex(self): return self.__mutex
    @property
    def port(self): return self.__port



