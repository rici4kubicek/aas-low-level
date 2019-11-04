#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" timer measurements
"""

from tools.monotonic import monotonic

__author__ = "Richard Kubicek"
__copyright__ = "Copyright 2019, ELEDIO"
__credits__ = ["Pavel Brychta", "Richard Kubicek"]
__license__ = "TBD"
__version__ = "1.0.0"
__maintainer__ = "Richard Kubicek"
__email__ = "richard.kubicek@eledio.com"
__status__ = "Production"

__all__ = ["Timer"]


class Timer(object):
    def __init__(self, value=0):
        self._startTime = int(monotonic())
        self._reload = value

    def __str__(self):
        return '<Period {}>'.format(self._reload)

    def set(self, value):
        self._reload = value
        self._startTime = int(monotonic())

    def reset(self):
        self._startTime = int(monotonic())

    @property
    def expired(self):
        art = False
        if int(monotonic()) >= self._startTime + self._reload:
            art = True
        return art