# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDriver Objects
@author: Jack Kirby Cook

"""

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from webscraping.webdata import EmptyWebDataError
from webscraping.webpages import EmptyWebPageError, CaptchaError, RefusalError
from webscraping.webactions import EmptyWebActionsError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebDriverError(Exception):
    def __str__(self): return "{}|{}".format(self.__class__.__name__, self.args[0].__class__.__name__)   

class MaxWebDriverRetryError(WebDriverError): pass
class FailureWebDriverError(WebDriverError): pass


class WebDriver(object):
    def __init_subclass__(cls, *args, page=None, pages=[], options={}, **kwargs):
        assert isinstance(options, dict)
        assert isinstance(pages, list)
        setattr(cls, 'WebPages', [item for item in [page, *pages] if item is not None])
        setattr(cls, 'options', options) 
        
    def __str__(self): return self.__class__.__name__
    def __repr__(self): 
        content = {'loadtime':self.__loadtime, 'attempts':self.__attempts, **self.options}
        string = ', '.join(['='.join([key, str(value)]) for key, value in content.items()])
        return "{}(file='{}', {})".format(self.__class__.__name__, self.__file, string)    
    
    def __init__(self, file, *args, loadtime=50, attempts=3, wait=5, **kwargs): 
        self.__loadtime, self.__attempts = loadtime, attempts
        self.__headers = kwargs.get('headers', {})
        try: self.__options = self.options
        except AttributeError: self.__options = {}
        self.__file = file
        self.__wait = wait
                
    def __call__(self, *args, **kwargs):
        try: yield from self.controller(*args, **kwargs)
        except MaxWebDriverRetryError: raise FailureWebDriverError(self)       
    
    def controller(self, *args, attempt=0, **kwargs):
        try: 
            print("WebDriver Running: {}".format(self.__class__.__name__))
            print("Attempt: {}|{}".format(str(attempt+1), str(self.__attempts+1)))            
            options, capabilities = self.setup(*args, **kwargs)
            driver = self.start(options, capabilities)               
            homewebpage = self.WebPages[0](driver, *args, wait=self.__wait, **kwargs)
            homewebpage.load(*args, **kwargs)
            yield from homewebpage(*args, **kwargs)
            for WebPage in self.WebPages[1:]: 
                webpage = WebPage(driver, *args, wait=self.__wait, **kwargs) 
                yield from webpage(*args, **kwargs)             
            print("WebDriver Success: {}".format(self.__class__.__name__))
            try: self.stop(driver)
            except NameError: pass   
        except (EmptyWebPageError, EmptyWebActionsError, EmptyWebDataError, CaptchaError, RefusalError) as error:
            print("WebDriver Failure: {}".format(self.__class__.__name__))
            print(str(error))
            try: self.stop(driver)
            except NameError: pass       
            if attempt < self.__attempts: yield from self.controller(*args, attempt=attempt+1, **kwargs)
            else: raise MaxWebDriverRetryError(attempt) 
        
    def stop(self, driver): driver.quit()        
    def start(self, options, capabilities): 
        driver = Chrome(executable_path=self.__file, chrome_options=options, desired_capabilities=capabilities) 
        driver.set_page_load_timeout(self.__loadtime)
        driver.delete_all_cookies()
        return driver 
           
    def setup(self, *args, **kwargs):   
        capabilities = DesiredCapabilities.CHROME.copy()
        headers = self.getHeaders(*args, **kwargs)
        options = self.getOptions(*args, **self.__options, useragent=headers.get('useragent', None), **kwargs)
        return options, capabilities            

    @classmethod
    def addOptions(cls, options): setattr(cls, 'options', options)  
    def getOptions(self, *args, useragent=None, incognito=False, headless=False, images=True, **kwargs): 
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-gpu")
        if useragent is not None: options.add_argument("user-agent={}".format(useragent))
        if incognito: options.add_argument("--incognito")
        if headless: 
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")     
        if not images: options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        return options
       
    def getHeaders(self, *args, **kwargs):
        try: headers = next(self.__headers)
        except TypeError: headers = self.__headers
        assert isinstance(headers, dict)
        return headers



    


    







    