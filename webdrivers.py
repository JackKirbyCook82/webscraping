# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDriver Objects
@author: Jack Kirby Cook

"""

import lxml.html
import multiprocessing
import selenium.webdriver
from collections import namedtuple as ntuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

from support.meta import DelayerMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebDriver", "WebBrowser"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebBrowser(object):
    Browser = ntuple("Browser", "name service driver options")
    CHROME = Browser("Chrome", ChromeService, selenium.webdriver.Chrome, selenium.webdriver.ChromeOptions)
    FIREFOX = Browser("Firefox", FirefoxService, selenium.webdriver.Firefox, selenium.webdriver.FirefoxOptions)


class WebDriver(object, metaclass=DelayerMeta):
    def __init_subclass__(cls, *args, browser, executable, **kwargs):
        cls.__executable__ = executable
        cls.__browser__ = browser

    def __repr__(self): return f"{self.name}|{self.browser.name}"
    def __init__(self, *args, timeout=60, port=None, **kwargs):
        self.__name = kwargs.get("name", self.__class__.__name__)
        self.__executable = self.__class__.__executable__
        self.__browser = self.__class__.__browser__
        self.__mutex = multiprocessing.Lock()
        self.__timeout = int(timeout)
        self.__driver = None
        self.__port = port

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.stop()

    def start(self):
        executable = self.executable
        options = self.browser.options()
        self.setup(options, port=self.port)
        service = self.browser.service(executable)
        driver = self.browser.driver(service=service, options=options)
        driver.set_page_load_timeout(int(self.timeout))
        driver.delete_all_cookies()
        self.driver = driver

    def stop(self):
        self.driver.quit()

    @DelayerMeta.delayer
    def load(self, url, *args, params={}, **kwargs):
        url = self.urlparse(url, params)
        with self.mutex:
            self.driver.get(url)

    @DelayerMeta.delayer
    def forward(self): self.driver.foward()
    @DelayerMeta.delayer
    def back(self): self.driver.back()
    @DelayerMeta.delayer
    def refresh(self): self.driver.refresh()
    @DelayerMeta.delayer
    def maximize(self): self.driver.maximize_window()
    @DelayerMeta.delayer
    def minimize(self): self.driver.minimize_window()
    @DelayerMeta.delayer
    def pageup(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.PAGE_UP)
    @DelayerMeta.delayer
    def pagedown(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.PAGE_DOWN)
    @DelayerMeta.delayer
    def pagehome(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.HOME)
    @DelayerMeta.delayer
    def pageend(self): self.driver.find_element(By.TAG_NAME, "html").send_keys(Keys.END)

    @staticmethod
    def urlparse(url, params={}):
        params = "&".join(["=".join([str(key), str(value)]) for key, value in params.items()])
        string = ("?" + params) if "?" not in str(url) else ("&" + params)
        url = str(url) + (str(string) if bool(params) else "")
        return url

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
    def pretty(self): return lxml.etree.tostring(self.html, pretty_print=True, encoding="unicode")
    @property
    def html(self): return lxml.html.fromstring(self.driver.page_source)
    @property
    def url(self): return self.driver.current_url
    @property
    def text(self): return self.driver.page_source

    @property
    def response(self): return [request.response for request in self.driver.requests]
    @property
    def request(self): return [request for request in self.driver.requests]

    @property
    def driver(self): return self.__driver
    @driver.setter
    def driver(self, driver): self.__driver = driver

    @property
    def mutex(self): return self.__mutex
    @property
    def browser(self): return self.__browser
    @property
    def executable(self): return self.__executable
    @property
    def timeout(self): return self.__timeout
    @property
    def port(self): return self.__port
    @property
    def name(self): return self.__name



