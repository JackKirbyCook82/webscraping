# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebDriver Objects
@author: Jack Kirby Cook

"""

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from webscraping.webdata import EmptyWebDataError, EmptyWebCollectionError, CaptchaError
from webscraping.webactions import EmptyWebActionsError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebDriver']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebDriverError(Exception):
    def __str__(self): return "{}: {}".format(self.__class__.__name__, self.args[0].__class__.__name__)   

class MaxWebDriverRetryError(WebDriverError): pass
class FailureWebDriverError(WebDriverError): pass


class WebDriver(object):
    def __init_subclass__(cls, *args, options={}, **kwargs):
        assert isinstance(options, dict)
        if 'webpage' in kwargs.keys(): 
            assert 'webpages' not in kwargs.keys()
            webpages = [kwargs['webpage']]
        elif 'webpages' in kwargs.keys(): 
            assert 'webpage' not in kwargs.keys()
            webpages = kwargs['webpages']
        else: raise ValueError(kwargs)
        assert isinstance(webpages, list)
        setattr(cls, 'WebPages', webpages)
        setattr(cls, 'options', options) 
        
    def __str__(self): return self.__class__.__name__
    def __repr__(self): 
        content = {'loadtime':self.__loadtime, 'timeout':self.__timeout, 'retrys':self.__retrys, **self.options}
        string = ', '.join(['='.join([key, str(value)]) for key, value in content.items()])
        return "{}(file='{}', {})".format(self.__class__.__name__, self.__file, string)    
    
    def __init__(self, file, *args, loadtime=50, timeout=10, retrys=5, **kwargs): 
        assert timeout is not None and loadtime is not None
        self.__loadtime, self.__timeout, self.__retrys = loadtime, timeout, retrys
        self.__headers = kwargs.get('headers', {})
        try: self.__options = self.options
        except AttributeError: self.__options = {}
        self.__file = file
                
    def __call__(self, url, *args, **kwargs):
        try: yield from self.controller(url, *args, **kwargs)
        except MaxWebDriverRetryError: raise FailureWebDriverError(self)       
    
    def controller(self, url, *args, retry=0, **kwargs):
        try: 
            print("WebDriver Running: {}".format(self.__class__.__name__))
            print("Attempt: {}|{}".format(str(retry+1), str(self.__retrys+1)))            
            options, capabilities = self.setup(*args, **kwargs)
            driver = self.start(options, capabilities)               
            loadwebpage = self.WebPages[0](driver, self.timeout)
            loadwebpage.load(url, *args, **kwargs)
            yield from loadwebpage(*args, **kwargs)
            for WebPage in self.WebPages[1:]: 
                webpage = WebPage(driver, self.timeout) 
                yield from webpage(*args, **kwargs)             
            self.stop(driver)  
            print("WebDriver Success: {}".format(self.__class__.__name__))
        except (EmptyWebActionsError, EmptyWebDataError, EmptyWebCollectionError, CaptchaError) as error:
            try: self.stop(driver)
            except NameError: pass
            print("WebDriver Failure: {}".format(self.__class__.__name__))
            print(str(error))
            if retry < self.__retrys: yield from self.controller(url, *args, retry=retry+1, **kwargs)
            else: raise MaxWebDriverRetryError(retry)  
        
    def start(self, options, capabilities): 
        driver = Chrome(executable_path=self.__file, chrome_options=options, desired_capabilities=capabilities) 
        driver.set_page_load_timeout(self.loadtime)
        return driver 
        
    def stop(self, driver):
        driver.quit()     
        
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

    @property
    def loadtime(self): return self.__loadtime
    @property
    def timeout(self): return self.__timeout    

    def __url(self, driver): return driver.current_url
    def __html(self, driver): return driver.page_source
    def __back(self, driver): driver.back
    def __forward(self, driver): driver.forward
    def __refresh(self, driver): driver.refresh

    


    







    