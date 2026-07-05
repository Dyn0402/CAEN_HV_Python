#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A pure-Python stand-in for hv_c_lib/libhv_c.so, used by the unit tests so the
session/reconnect/keepalive logic can be exercised on a laptop with no CAEN
hardware. It mimics the C ABI seen by CAENHVController (same function names,
same int/float return values and failure sentinels) and, crucially, reproduces
the real quirk this package exists to handle: the session handle goes invalid
after `idle_timeout` seconds with no successful call.

Time is driven by an injected `clock` callable (default: a manual counter the
test advances) so tests are deterministic and instant — no real sleeping.
"""


class FakeClock:
    """Deterministic monotonic clock the tests advance by hand."""
    def __init__(self, t=0.0):
        self.t = float(t)

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += float(seconds)
        return self.t


class FakeHVLib:
    """Duck-typed stand-in for a ctypes.CDLL of libhv_c.so.

    Models one mainframe with a handful of channels. A call made more than
    `idle_timeout` s after the last *successful* activity finds the session
    dead (matching the CAEN 15 s drop): it returns the failure sentinel, and
    stays dead until a fresh log_in. `fail_logins` forces log_in to fail a set
    number of times (to test reconnect exhaustion).
    """

    def __init__(self, clock=None, idle_timeout=15.0, fail_logins=0,
                 v0=500.0):
        self._clock = clock if clock is not None else FakeClock()
        self.idle_timeout = idle_timeout
        self._fail_logins = fail_logins

        self._next_handle = 1
        self._handle = None          # current valid handle, or None
        self._last_activity = None   # clock() at last successful call
        self._v0 = {}                # (slot, chan) -> V0 setpoint
        self._pw = {}                # (slot, chan) -> power 0/1
        self._default_v0 = v0

        # instrumentation for assertions
        self.login_calls = 0
        self.total_calls = 0

    # -- helpers -----------------------------------------------------------
    def _expire_if_idle(self):
        """Kill the session if it has been idle past the timeout."""
        if self._handle is not None and self._last_activity is not None:
            if self._clock() - self._last_activity > self.idle_timeout:
                self._handle = None  # session dropped
        return self._handle is not None

    def _touch(self):
        self._last_activity = self._clock()

    def _alive(self, sys_handle):
        self.total_calls += 1
        if not self._expire_if_idle():
            return False
        return sys_handle == self._handle

    # -- C ABI surface -----------------------------------------------------
    def log_in(self, ip, user, pw):
        self.login_calls += 1
        if self._fail_logins > 0:
            self._fail_logins -= 1
            return -1
        self._handle = self._next_handle
        self._next_handle += 1
        self._touch()
        return self._handle

    def log_out(self, sys_handle):
        if sys_handle == self._handle:
            self._handle = None
            return 1
        return 0

    def get_crate_map(self, sys_handle, verbose):
        # Liveness probe. Counts as activity when it succeeds.
        if not self._alive(sys_handle):
            return 0
        self._touch()
        return 1

    def get_ch_power(self, sys_handle, slot, chan):
        if not self._alive(sys_handle):
            return -1
        self._touch()
        return self._pw.get((slot, chan), 0)

    def get_ch_vmon(self, sys_handle, slot, chan):
        if not self._alive(sys_handle):
            return -1.0
        self._touch()
        # "ramped" reading == setpoint if powered, else 0
        if self._pw.get((slot, chan), 0):
            return self._v0.get((slot, chan), self._default_v0)
        return 0.0

    def get_ch_imon(self, sys_handle, slot, chan):
        if not self._alive(sys_handle):
            return -1.0
        self._touch()
        return 0.5

    def set_ch_v0(self, sys_handle, slot, chan, value):
        if not self._alive(sys_handle):
            return 0
        self._touch()
        self._v0[(slot, chan)] = value
        return 1

    def set_ch_pw(self, sys_handle, slot, chan, value):
        if not self._alive(sys_handle):
            return 0
        self._touch()
        self._pw[(slot, chan)] = value
        return 1

    def get_ch_param_float(self, sys_handle, slot, chan, name):
        if not self._alive(sys_handle):
            return -1.0
        self._touch()
        return 1.0

    def set_ch_param_float(self, sys_handle, slot, chan, name, value):
        if not self._alive(sys_handle):
            return 0
        self._touch()
        return 1

    def get_ch_param_ushort(self, sys_handle, slot, chan, name):
        if not self._alive(sys_handle):
            return 0xFFFF
        self._touch()
        return 3

    def set_ch_param_ushort(self, sys_handle, slot, chan, name, value):
        if not self._alive(sys_handle):
            return 0
        self._touch()
        return 1
