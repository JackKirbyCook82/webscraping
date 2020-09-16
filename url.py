# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 2018
@name:   URL Objects
@author: Jack Kirby cook
"""

from collections import namedtuple as ntuple

from utilities.sgmts import value_segment, argument_segment, keyword_segment

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['URL', 'Protocol', 'Domain', 'Port', 'Path', 'Parms', 'Anchor', 'JSONPath', 'HTMLPath', 'CSVPath', 'ZIPPath', 'EXEPath']
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


Protocol = value_segment('Protocol', endchar='://')
Domain = value_segment('Domain')
Port = value_segment('Port', startchar=':')
Path = argument_segment('Path', '/', startchar='/', endchar='') 

JSONPath = argument_segment('JSONPath', '/', startchar='/', endchar='.json') 
HTMLPath = argument_segment('HTMLPath', '/', startchar='/', endchar='.html')  
CSVPath = argument_segment('CSVPath', '/', startchar='/', endchar='.csv') 
ZIPPath = argument_segment('FTPPath', '/', startchar='/', endchar='.zip')
EXEPath = argument_segment('EXEPath', '/', startchar='/', endchar='.exe')

Parms = keyword_segment('Parms', '&', '=', startchar='?') 
Anchor = value_segment('Port', startchar='#')

                                       
URLSGMTS = ('protocol', 'domain', 'port', 'path', 'parms', 'anchor')                               


class URL(ntuple('URL', ' '.join(URLSGMTS))  ):   
    def __new__(cls, protocol, domain, port=Port(), path=Path(), parms=Parms(), anchor=Anchor()): return super().__new__(cls, protocol, domain, port, path, parms, anchor)
    def __str__(self): return ''.join([str(value) for value in self._asdict().values() if value])    
    def __bool__(self): return bool(str(self))


    