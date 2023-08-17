# -*- coding: utf-8 -*-
"""
Created on Sat Aug 5 2023
@name:   WebPayload Objects
@author: Jack Kirby Cook

"""

from abc import ABC, ABCMeta
from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ["WebPayload"]
__copyright__ = "Copyright 2018, Jack Kirby Cook"
__license__ = ""


Style = ntuple("Style", "branch terminate run blank")
aslist = lambda x: [x] if not isinstance(x, (list, tuple)) else list(x)
double = Style("╠══", "╚══", "║  ", "   ")
single = Style("├──", "└──", "│  ", "   ")
curved = Style("├──", "╰──", "│  ", "   ")


class WebPayloadMeta(ABCMeta):
    def __repr__(cls):
        renderer = cls.hierarchy(style=cls.__style__)
        rows = [pre + "|".join(key, value.__name__) for pre, key, value in iter(renderer)]
        return "\n".format(rows)

    def __new__(mcs, name, bases, attrs, *args, **kwargs):
        cls = super(WebPayloadMeta, mcs).__new__(mcs, name, bases, attrs)
        if not any([type(base) is WebPayloadMeta for base in bases]):
            return cls
        assert type(bases[0]) is WebPayloadMeta
        assert all([type(base) is not WebPayloadMeta for base in bases[1:]])
        if ABC in bases:
            return cls
        return cls

    def __init__(cls, name, bases, attrs, *args, **kwargs):
        if not any([type(base) is WebPayloadMeta for base in bases]):
            return
        assert type(bases[0]) is WebPayloadMeta
        assert all([type(base) is not WebPayloadMeta for base in bases[1:]])
        if ABC in bases:
            return

    def hierarchy(cls, layers=[], style=single):
        last = lambda i, x: i == x
        func = lambda i, x: "".join([pads(), pre(i, x)])
        pre = lambda i, x: style.terminate if last(i, x) else style.blank
        pads = lambda: "".join([style.blank if layer else style.run for layer in layers])
        if not layers:
            yield "", None, cls
        for index, (key, values) in enumerate(iter(cls.__children__)):
            for value in aslist(values):
                yield func(index, len(cls.__children__) - 1), key, value
                yield from value.renderer(layers=[*layers, last(index, len(cls.__children__) - 1)])


class WebPayload(ABC, metaclass=WebPayloadMeta):
    pass



