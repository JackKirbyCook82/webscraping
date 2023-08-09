# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 2019
@name:   WebPayload Objects
@author: Jack Kirby Cook

"""

from lxml import etree

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebPayload"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


class WebPayloadMeta(type):
    def __init__(cls, *args, **kwargs):
        if not any([type(base) is WebPayloadMeta for base in cls.__bases__]):
            return
        aslist = lambda content: [content] if not isinstance(content, list) else content
        locator = kwargs.get("locator", getattr(cls, "__locator__", None))
        locators = {key: value for key, value in getattr(cls, "__locators__", {}).items()}
        locators.update(kwargs.get("locators", {}))
        contents = {key: value for key, value in getattr(cls, "__contents__", {}).items()}
        contents.update({key: value for key, value in kwargs.get("contents", {}).items() if key in locators.keys()})
        payloads = aslist(kwargs.get("payload", None)) + aslist(kwargs.get("payloads", None))
        payloads = filter(None, payloads)
        assert all([isinstance(payload, dict) or type(payload) is WebPayloadMeta for payload in payloads])
        direct = getattr(cls, "__direct__", [])
        extend = [payload for payload in payloads if type(payload) is WebPayloadMeta]
        direct.extend(extend)
        indirect = getattr(cls, "__indirect__", {})
        updates = [payload for payload in payloads if isinstance(payload, dict)]
        for update in updates:
            indirect.update(update)
        cls.__locator__ = locator
        cls.__locators__ = locators
        cls.__contents__ = contents
        cls.__direct__ = direct
        cls.__indirect__ = indirect

    def __call__(cls, *args, **kwargs):
        aslist = lambda content: [content] if not isinstance(content, list) else content
        contents = {value: kwargs.get(key, None) for key, value in cls.__locators__.items() if key not in cls.__contents__.keys()}
        contents.update({value: cls.__contents__[key] for key, value in cls.__locators__.items() if key in cls.__contents__.keys()})
        instance = super(WebPayloadMeta, cls).__call__(cls.__locator__, contents)
        for key, subcls in cls.__indirect__.items():
            parms = aslist(kwargs.pop(key, {}))
            assert all([isinstance(subparms, dict) for subparms in parms])
            subinstances = [subcls(*args, **subparms, **kwargs) for subparms in parms]
            instance[key] = subinstances
        for subcls in cls.__direct__:
            subinstance = subcls(*args, **kwargs)
            instance.append(subinstance)
        return instance


class WebPayload(object, metaclass=WebPayloadMeta):
    def __init_subclass__(cls, *args, **kwargs): pass

    def __init__(self, locator, contents):
        self.__contents = {key: value for key, value in contents.items()}
        self.__locator = locator
        self.__direct = {}
        self.__indirect = []

    def __str__(self): return str(etree.tostring(self.xml, pretty_print=True, encoding="unicode"))
    def __contains__(self, key): return key in self.indirect
    def __getitem__(self, key): return self.indirect[key]
    def __setitem__(self, key, value): self.indirect[key] = value

    def append(self, payload): self.direct.append(payload)
    def extend(self, payloads): self.direct.extend(payloads)

    @property
    def locator(self): return self.__locator
    @property
    def contents(self): return self.__contents
    @property
    def direct(self): return self.__direct
    @property
    def indirect(self): return self.__indirect

    def toXML(self):
        root = etree.Element(self.locator)
        for locator, value in self.contents.items():
            etree.SubElement(root, str(locator)).text = str(value)
        for instance in self.direct:
            root.append(instance.xml)
        for key, instances in self.indirect.items():
            for instance in instances:
                root.append(instance.xml)
        return root

