# -*- coding: utf-8 -*-
"""
Created on Tues May 19 2026
@name:   WebPayload Objects
@author: Jack Kirby Cook

"""

from abc import ABC, ABCMeta

from support.meta import AttributeMeta, TreeMeta

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebPayload", "WebPayloadError"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = "MIT License"


class WebPayloadError(Exception): pass
class WebPayloadMissingError(WebPayloadError): pass
class WebPayloadMultipleError(WebPayloadError): pass


class WebPayloadMeta(AttributeMeta, TreeMeta, ABCMeta):
    pass


class WebPayload(ABC, metaclass=WebPayloadMeta):
    pass


class WebPayloadCollection(WebPayload, ABC, attribute="Collection"):
    pass


class WebPayloadMapping(WebPayload, ABC, attribute="Mapping"):
    pass


class WebPayloadText(WebPayload, ABC, attribute="Parser"):
    pass



