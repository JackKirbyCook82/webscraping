# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDriver Objects
@author: Jack Kirby Cook

"""

import lxml.html
import multiprocessing
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService

from support.mixins import Logging, Delayer

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebDriver"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebDriver(Logging):
    def __bool__(self): return self.driver is not None
    def __init__(self, *args, executable, delay, timeout=60, **kwargs):
        super().__init__(*args, **kwargs)
        self.__mutex = multiprocessing.Lock()
        self.__delayer = Delayer(delay)
        self.__timeout = int(timeout)
        self.__executable = executable
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
        self.setup(options)
        service = ChromeService(executable)
        driver = selenium.webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(self.timeout)
        self.driver = driver

    def stop(self):
        self.driver.quit()
        self.driver = None

    def load(self, url, *args, **kwargs):
        self.driver.get(str(url))

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
    def refresh(self): self.driver.refresh()
    def forward(self): self.driver.foward()
    def back(self): self.driver.back()

    @staticmethod
    def setup(options, *args, **kwargs):
        options.add_argument("log-level=3")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
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
    def browser(self): return self.__browser
    @property
    def profile(self): return self.__profile
    @property
    def delayer(self): return self.__delayer
    @property
    def element(self): return self.__driver
    @property
    def timeout(self): return self.__timeout
    @property
    def mutex(self): return self.__mutex




