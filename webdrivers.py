# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDriver Objects
@author: Jack Kirby Cook

"""

import logging
import os.path
import lxml.html
import multiprocessing
import selenium.webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from support.meta import DelayerMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebDriver"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


LOGGER = logging.getLogger(__name__)
DRIVERS = {"chrome": selenium.webdriver.Chrome, "firefox": selenium.webdriver.Firefox}
CAPABILITIES = {"chrome": DesiredCapabilities.CHROME, "firefox": DesiredCapabilities.FIREFOX}
OPTIONS = {"chrome": selenium.webdriver.ChromeOptions, "firefox": selenium.webdriver.FirefoxOptions}


class WebDriver(object, metaclass=DelayerMeta):
    def __init_subclass__(cls, *args, browser, file, **kwargs):
        assert os.path.isfile(file)
        cls.__browser__ = browser
        cls.__file__ = file

    def __repr__(self): return "{}|{}".format(self.name, self.browser.title())
    def __init__(self, *args, timeout=60, **kwargs):
        self.__name = kwargs.get("name", self.__class__.__name__)
        self.__browser = self.__class__.__browser__
        self.__file = self.__class__.__file__
        self.__mutex = multiprocessing.Lock()
        self.__timeout = int(timeout)
        self.__driver = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, error_type, error_value, error_traceback):
        self.stop()

    def start(self):
        options = OPTIONS[self.browser]()
        self.setup(options)
        driver = DRIVERS[self.browser](executable_path=self.file, options=options)
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
    def forward(self): self.source.foward()
    @DelayerMeta.delayer
    def back(self): self.source.back()
    @DelayerMeta.delayer
    def refresh(self): self.source.refresh()
    @DelayerMeta.delayer
    def maximize(self): self.source.maximize_window()
    @DelayerMeta.delayer
    def minimize(self): self.source.minimize_window()
    @DelayerMeta.delayer
    def pageUp(self): self.source.find_element_by_tag_name("html").send_keys(Keys.PAGE_UP)
    @DelayerMeta.delayer
    def pageDown(self): self.source.find_element_by_tag_name("html").send_keys(Keys.PAGE_DOWN)
    @DelayerMeta.delayer
    def pageHome(self): self.source.find_element_by_tag_name("html").send_keys(Keys.HOME)
    @DelayerMeta.delayer
    def pageEnd(self): self.source.find_element_by_tag_name("html").send_keys(Keys.END)

    @staticmethod
    def urlparse(url, params={}):
        params = "&".join(["=".join([str(key), str(value)]) for key, value in params.items()])
        string = ("?" + params) if "?" not in str(url) else ("&" + params)
        url = str(url) + (str(string) if bool(params) else "")
        return url

    @staticmethod
    def setup(options, *args, **kwargs):
        options.add_argument("log-level=3")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--ignore-certificate-errors-spki-list")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

    @property
    def mutex(self): return self.__mutex
    @property
    def browser(self): return self.__browser
    @property
    def file(self): return self.__file
    @property
    def timeout(self): return self.__timeout
    @property
    def name(self): return self.__name

    @property
    def source(self): return self.driver
    @property
    def url(self): return self.source.current_url
    @property
    def pretty(self): return lxml.etree.tostring(self.html, pretty_print=True, encoding="unicode")
    @property
    def html(self): return lxml.html.fromstring(self.source.page_source)
    @property
    def text(self): return self.source.page_source

    @property
    def response(self): return [request.response for request in self.driver.requests]
    @property
    def request(self): return [request for request in self.driver.requests]

    @property
    def driver(self): return self.__driver
    @driver.setter
    def driver(self, driver): self.__driver = driver



