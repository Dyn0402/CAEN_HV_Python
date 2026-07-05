#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
caen_hv_py — Python wrapper for the CAEN High Voltage C library.

See CAENHVController for the resilient (auto-reconnecting) session wrapper.
"""

from .CAENHVController import CAENHVController
from .exceptions import CAENHVError, CAENConnectionError, CAENCommandError

__version__ = "2.0.0"

__all__ = [
    "CAENHVController",
    "CAENHVError",
    "CAENConnectionError",
    "CAENCommandError",
    "__version__",
]
