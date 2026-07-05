#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exception hierarchy for caen_hv_py.

The underlying C layer signals failures by returning sentinel values (-1 for
reads, 0 for sets) and printing to stdout, which makes it impossible for a
caller to tell a real reading from a dead session (e.g. VMon == -1.0). The
controller now translates those sentinels into these typed exceptions so
callers can react appropriately:

  * CAENConnectionError — the session handle is invalid / the crate is
    unreachable and could not be re-established. Recoverable in principle
    (re-login), raised only when auto-reconnect is off or has been exhausted.
  * CAENCommandError    — a specific get/set failed while the session is still
    alive (bad slot/channel/param, channel tripped, etc.). Not a connection
    problem.
"""


class CAENHVError(Exception):
    """Base class for all caen_hv_py errors."""


class CAENConnectionError(CAENHVError):
    """Login failed, or the session handle went stale and could not be recovered."""


class CAENCommandError(CAENHVError):
    """A channel/parameter get or set failed on an otherwise-live session."""
