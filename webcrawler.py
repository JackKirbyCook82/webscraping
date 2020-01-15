# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   Webcrawler Objects
@author: Jack Kirby Cook

"""

from abc import ABC, abstractmethod
from lxml import etree

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['WebCrawler']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebCrawler(ABC):
    keyformat = lambda mainnum, pagenum: '{name}{mainnum}|{pagenum}'
    treeparsers = {'html': etree.HTMLParser()}
    
    def __init__(self, name, webreader, crawlxpath, pagexpath, *args, treeparser='html', maxcrawl=None, maxpage=None, **kwargs):
        self.__webreader = webreader
        self.__crawlxpath, self.__pagexpath = crawlxpath, pagexpath
        self.__maxcrawl, self.__maxpage = maxcrawl, maxpage
        self.__treeparser = treeparser
        self.__name = name

    @abstractmethod
    def pageparser(self, htmltree, *args, **kwargs): pass
    @abstractmethod
    def dataparser(self, htmldatas, *args, **kwargs): pass  
    
    def __maxrequest(self, crawlnum, pagenum): 
        maxcrawl = crawlnum >= self.maxcrawl if self.__maxcrawl else False 
        maxpage = pagenum >= self.maxpage if self.__maxpage else False
        return maxcrawl or maxpage

    def __call__(self, mainurl, *args, **kwargs):
        for mainnum, pagenum, pageurl in self.execute(mainurl, *args, **kwargs):
            htmlpage = self.__webreader(pageurl, *args, method='get', datatype='html',  **kwargs)
            if self.__maxrequest(mainnum, pagenum): break
            else: yield self.keyformat(name=self.name, mainnum=mainnum, pagenum=pagenum), htmlpage 

    def execute(self, mainurl, *args, crawlnum=0, pagenum=0, datatype='html', **kwargs):
        mainhtmlpage = self.__webreader(mainurl, *args, method='get', datatype=datatype, **kwargs)
        mainhtmltree = etree.parse(mainhtmlpage, self.treeparsers[self.__treeparser])
        
        for pageurl in mainhtmltree.xpath(self.__pagexpath):    
            pagenum = pagenum + 1
            yield crawlnum, pagenum, pageurl        
        
        nexturl = mainhtmltree.xpath(self.__crawlxpath)[0] 
        yield from self.execute(nexturl, *args, crawlnum=crawlnum+1, pagenum=pagenum, **kwargs)
        


    












