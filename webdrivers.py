# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDriver Objects
@author: Jack Kirby Cook

"""

import time
import types
import lxml.html
import multiprocessing
import selenium.webdriver
from datetime import datetime as Datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService

from support.mixins import Logging

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebDriver"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebDriver(Logging):
    def __bool__(self): return self.driver is not None
    def __init__(self, *args, executable, delay=5, timeout=60, port=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__executable = executable
        self.__mutex = multiprocessing.Lock()
        self.__timeout = int(timeout)
        self.__delay = int(delay)
        self.__timer = None
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
        options = selenium.webdriver.ChromeOptions()
        self.setup(options, port=self.port)
        service = ChromeService(executable)
        driver = selenium.webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(self.timeout)
        driver.delete_all_cookies()
        self.driver = driver

    def stop(self):
        self.driver.quit()
        self.driver = None

    def load(self, url, *args, **kwargs):
        function = lambda: self.driver.get(str(url))
        self.execute(function)

    def navigate(self, value):
        if isinstance(value, int): handle = list(self.driver.window_handles)[value]
        elif isinstance(value, str): handle = dict(self)[value]
        else: raise TypeError(type(value))
        self.driver.switch_to.window(handle)

    def pageup(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.PAGE_UP)
    def pagedown(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.PAGE_DOWN)
    def pagehome(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.HOME)
    def pageend(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.END)
    def maximize(self): self.driver.maximize_window()
    def minimize(self): self.driver.minimize_window()

    def refresh(self):
        function = lambda: self.driver.refresh()
        self.execute(function)

    def forward(self):
        function = lambda: self.driver.foward()
        self.execute(function)

    def back(self):
        function = lambda: self.driver.back()
        self.execute(function)

    def execute(self, function, *args, **kwargs):
        assert isinstance(function, types.LambdaType)
        with self.mutex:
            elapsed = (Datetime.now() - self.timer).total_seconds() if bool(self.timer) else self.delay
            wait = max(self.delay - elapsed, 0)
            if bool(wait):
                self.console(f"{elapsed:.02f} seconds", title="Waiting")
                time.sleep(wait)
            function(*args, **kwargs)
            self.timer = Datetime.now()

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
    def elmt(self): return self.driver

    @property
    def driver(self): return self.__driver
    @driver.setter
    def driver(self, driver): self.__driver = driver

    @property
    def executable(self): return self.__executable
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

    @property
    def timer(self): return self.__timer
    @timer.setter
    def timer(self, timer): self.__timer = timer




