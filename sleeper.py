# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 2019
@name:   Sleeper Object
@author: Jack Kirby Cook

"""

import time
from functools import update_wrapper

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Sleeper']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class Sleeper(object):
    def __init__(self, delay=None): self.__delay, self.__lasttime = delay if delay else 0, None        
    def ready(self, currenttime): return currenttime - self.__lasttime  > self.__delay if self.__lasttime else True
    def wait(self, currenttime): return max([self.__delay - int(currenttime - self.__lasttime), 0]) if self.__lasttime else 0
    def record(self, lasttime): self.__lasttime = lasttime
    
    def __call__(self, function):
        def wrapper(*args, **kwargs):
            starttime = time.time()
            if not self.ready(starttime):
                waittime = self.wait(starttime)
                print('Download Waiting: {} Seconds'.format(waittime))
                time.sleep(waittime)
            response = function(*args, **kwargs)
            self.record(time.time())
            return response
        update_wrapper(wrapper, function)
        return wrapper