#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Shutdown handler
"""

import signal

__all__ = ["EShutdown"]


class EShutdown:
    killed = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.killed = True
