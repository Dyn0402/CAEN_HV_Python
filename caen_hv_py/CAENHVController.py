#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 25 1:12 PM 2024
Created in PyCharm
Created as CAEN_HV_Python/CAENHVController.py

@author: Dylan Neff, Dylan

Resilient Python wrapper around the CAEN HV C library (hv_c_lib/libhv_c.so).

Why this exists / what changed
------------------------------
The CAEN HV Wrapper session drops after ~15 s with no calls: the sys_handle
goes invalid and every subsequent C call returns a failure sentinel (-1 for
reads, 0 for sets) while the C layer prints e.g. "CFE server down". The old
wrapper returned those sentinels verbatim, so a caller could not distinguish a
dead session from a real reading (VMon == -1.0 is truthy, a set "succeeds" as
0, etc.) and would hang or misbehave.

This controller owns the session lifecycle and makes it self-healing:

  * auto_reconnect (default on): if a call fails because the session died, it
    transparently re-logs-in and retries once, so callers never see the blip.
  * keepalive_s (opt-in): a background thread touches the crate every keepalive_s
    seconds so the handle never goes stale in the first place.
  * typed errors: unrecoverable failures raise CAENConnectionError /
    CAENCommandError instead of returning ambiguous sentinels
    (set raise_on_error=False for the legacy sentinel-returning behaviour).
  * thread-safe: all C calls are serialised on an internal RLock, so a keepalive
    tick, a monitor read and a set can interleave safely.

Backwards compatibility: the public methods (get_ch_vmon, set_ch_v0, ...),
success return values, and `with CAENHVController(ip, user, pw) as hv:` all keep
working. New behaviour (raising, reconnect, keepalive) is controlled by the new
keyword arguments below and defaults chosen to be safe for existing callers.
"""

import sys
import ctypes
import ctypes.util
import threading
import logging
import time

from .exceptions import CAENHVError, CAENConnectionError, CAENCommandError

# Handle version-agnostic resource loading
if sys.version_info >= (3, 9):
    from importlib.resources import files
else:  # pragma: no cover - legacy path
    from importlib.resources import path as resource_path

_logger = logging.getLogger("caen_hv_py")

# Failure sentinels returned by the C layer (hv_functions.c).
_FAIL_INT = -1            # get_ch_power, log_in
_FAIL_FLOAT = -1.0        # get_ch_vmon / get_ch_imon / get_ch_param_float
_FAIL_USHORT = 0xFFFF     # get_ch_param_ushort ((unsigned short)-1)
_SET_OK = 1               # set_* return 1 on success, 0 on failure


class CAENHVController:
    """
    Wrapper class for the CAEN HV C library. Loads the shared library, declares
    the C function prototypes, and exposes channel get/set helpers.

    Session robustness (see module docstring): the CAEN session is dropped after
    ~15 s idle; this controller detects the resulting failures, re-logs-in, and
    retries so the caller does not have to. Use keepalive_s to avoid the drop
    entirely.

    Parameters
    ----------
    ip_address, username, password : str
        CAEN mainframe connection credentials.
    auto_reconnect : bool, default True
        On a failed call, probe the session; if it is dead, re-login and retry
        the call once.
    keepalive_s : float or None, default None
        If set, a daemon thread touches the crate every keepalive_s seconds
        (must be < the ~15 s session timeout, e.g. 10) to keep the handle warm.
    raise_on_error : bool, default True
        Raise CAENConnectionError / CAENCommandError on failure instead of
        returning the raw sentinel. Set False for the legacy behaviour.
    max_reconnect_attempts : int, default 3
        Login attempts made by a single reconnect before giving up.
    reconnect_backoff_s : float, default 1.0
        Delay between reconnect attempts.
    library : ctypes.CDLL or duck-typed stand-in, optional
        Inject a pre-loaded library (used by the tests' fake). Defaults to
        loading hv_c_lib/libhv_c.so.
    """

    def __init__(self, ip_address, username, password, *,
                 auto_reconnect=True, keepalive_s=None, raise_on_error=True,
                 max_reconnect_attempts=3, reconnect_backoff_s=1.0, library=None):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.sys_handle = None

        self.auto_reconnect = auto_reconnect
        self.keepalive_s = keepalive_s
        self.raise_on_error = raise_on_error
        self.max_reconnect_attempts = max(1, int(max_reconnect_attempts))
        self.reconnect_backoff_s = reconnect_backoff_s

        self.library = library
        self._injected_library = library is not None
        self._lock = threading.RLock()
        self._closed = False
        self._reconnects = 0  # diagnostics: how many times the session was rebuilt

        # keepalive machinery
        self._ka_stop = threading.Event()
        self._ka_thread = None

        self.library_path = None
        if not self._injected_library:
            self.library_path = self._resolve_library_path()

    # ------------------------------------------------------------------ setup
    @staticmethod
    def _resolve_library_path():
        if sys.version_info >= (3, 9):
            return str(files("caen_hv_py").joinpath("hv_c_lib/libhv_c.so"))
        with resource_path("caen_hv_py.hv_c_lib", "libhv_c.so") as p:  # pragma: no cover
            return str(p)

    def _bind_prototypes(self):
        """Declare argtypes/restypes once (real ctypes CDLL only)."""
        lib = self.library
        lib.log_in.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        lib.log_in.restype = ctypes.c_int
        lib.log_out.argtypes = [ctypes.c_int]
        lib.log_out.restype = ctypes.c_int
        lib.get_crate_map.argtypes = [ctypes.c_int, ctypes.c_int]
        lib.get_crate_map.restype = ctypes.c_int
        lib.get_ch_power.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        lib.get_ch_power.restype = ctypes.c_int
        lib.get_ch_vmon.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        lib.get_ch_vmon.restype = ctypes.c_float
        lib.get_ch_imon.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        lib.get_ch_imon.restype = ctypes.c_float
        lib.set_ch_v0.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_float]
        lib.set_ch_v0.restype = ctypes.c_int
        lib.set_ch_pw.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        lib.set_ch_pw.restype = ctypes.c_int
        lib.get_ch_param_ushort.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
        lib.get_ch_param_ushort.restype = ctypes.c_ushort
        lib.set_ch_param_ushort.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_ushort]
        lib.set_ch_param_ushort.restype = ctypes.c_int
        lib.get_ch_param_float.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
        lib.get_ch_param_float.restype = ctypes.c_float
        lib.set_ch_param_float.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_float]
        lib.set_ch_param_float.restype = ctypes.c_int

    # ------------------------------------------------------ context management
    def __enter__(self):
        if not self._injected_library:
            self.library = ctypes.CDLL(self.library_path)
        if isinstance(self.library, ctypes.CDLL):
            self._bind_prototypes()
        self.connect()
        if self.keepalive_s:
            self.start_keepalive()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # --------------------------------------------------- connection lifecycle
    def connect(self):
        """(Re)establish the session. Raises CAENConnectionError on failure."""
        with self._lock:
            self._closed = False
            handle = self._raw_login()
            if handle is None or handle < 0:
                raise CAENConnectionError(
                    f"log_in to {self.ip_address} failed (handle={handle})")
            self.sys_handle = handle
            return handle

    def close(self):
        """Stop keepalive and log out. Idempotent."""
        self.stop_keepalive()
        with self._lock:
            if self.sys_handle is not None and not self._closed:
                try:
                    self.library.log_out(self.sys_handle)
                except Exception as e:  # pragma: no cover - shutdown best effort
                    _logger.debug("log_out during close failed: %s", e)
            self.sys_handle = None
            self._closed = True

    def reconnect(self):
        """Force a fresh login (thread-safe). Raises CAENConnectionError if it
        cannot be re-established within max_reconnect_attempts."""
        with self._lock:
            return self._reconnect_locked()

    def is_alive(self):
        """True if the current session answers a crate-map probe."""
        with self._lock:
            return self._probe_alive_locked()

    def ensure_alive(self):
        """Probe the session and reconnect if it is dead. Returns True if the
        session is usable afterwards. Cheap to call before a batch of ops."""
        with self._lock:
            if self._probe_alive_locked():
                return True
            if not self.auto_reconnect:
                if self.raise_on_error:
                    raise CAENConnectionError("session dead and auto_reconnect is off")
                return False
            self._reconnect_locked()
            return True

    @property
    def reconnect_count(self):
        """Number of times the session has been rebuilt (diagnostics)."""
        return self._reconnects

    # --------------------------------------------------------- keepalive
    def start_keepalive(self, interval_s=None):
        """Start the background keepalive thread (no-op if already running)."""
        with self._lock:
            if self._ka_thread and self._ka_thread.is_alive():
                return
            if interval_s is not None:
                self.keepalive_s = interval_s
            if not self.keepalive_s:
                return
            self._ka_stop.clear()
            self._ka_thread = threading.Thread(
                target=self._keepalive_loop, name="caen-hv-keepalive", daemon=True)
            self._ka_thread.start()

    def stop_keepalive(self):
        self._ka_stop.set()
        t = self._ka_thread
        if t and t.is_alive() and t is not threading.current_thread():
            t.join(timeout=2.0)
        self._ka_thread = None

    def _keepalive_loop(self):  # pragma: no cover - exercised via _keepalive_tick
        while not self._ka_stop.wait(self.keepalive_s):
            try:
                self._keepalive_tick()
            except Exception as e:
                _logger.warning("keepalive tick failed: %s", e)

    def _keepalive_tick(self):
        """One keepalive iteration: touch the crate, reconnect if it died.
        Factored out from the loop so it is unit-testable without timing."""
        with self._lock:
            if self._closed:
                return
            if not self._probe_alive_locked():
                if self.auto_reconnect:
                    _logger.info("keepalive: session dead, reconnecting")
                    self._reconnect_locked()

    # ----------------------------------------------------------- internals
    def _raw_login(self):
        """Call the C log_in directly (no guard). Returns the handle int."""
        return self.library.log_in(
            self.ip_address.encode("utf-8"),
            self.username.encode("utf-8"),
            self.password.encode("utf-8"),
        )

    def _reconnect_locked(self):
        last = None
        for attempt in range(1, self.max_reconnect_attempts + 1):
            try:
                handle = self._raw_login()
            except Exception as e:  # C/ctypes blew up
                last = e
                handle = None
            if handle is not None and handle >= 0:
                self.sys_handle = handle
                self._reconnects += 1
                _logger.info("reconnected to %s (handle=%s, attempt %d)",
                             self.ip_address, handle, attempt)
                return handle
            if attempt < self.max_reconnect_attempts:
                time.sleep(self.reconnect_backoff_s)
        raise CAENConnectionError(
            f"reconnect to {self.ip_address} failed after "
            f"{self.max_reconnect_attempts} attempt(s): {last}")

    def _probe_alive_locked(self):
        """Cheap liveness check: get_crate_map returns 1 alive / 0 dead."""
        if self.sys_handle is None or self._closed:
            return False
        try:
            return self.library.get_crate_map(self.sys_handle, 0) == 1
        except Exception:
            return False

    def _guard(self, op, cfunc, args, failed):
        """Run cfunc(handle, *args); on a failure sentinel, disambiguate a dead
        session (-> reconnect + retry) from a genuine command error, honouring
        auto_reconnect / raise_on_error."""
        with self._lock:
            if self._closed:
                raise CAENConnectionError(f"{op}: controller is closed")
            result = cfunc(self.sys_handle, *args)
            if not failed(result):
                return result

            # A sentinel came back. Is the session dead, or did the command fail?
            if self._probe_alive_locked():
                if self.raise_on_error:
                    raise CAENCommandError(f"{op} failed (slot/channel/param?)")
                return result

            # Session is dead.
            if not self.auto_reconnect:
                if self.raise_on_error:
                    raise CAENConnectionError(f"{op}: session dead")
                return result

            self._reconnect_locked()
            result = cfunc(self.sys_handle, *args)
            if failed(result):
                if self.raise_on_error:
                    raise CAENConnectionError(f"{op} still failing after reconnect")
                return result
            return result

    # ------------------------------------------------------- public: session
    def log_in(self):
        """Legacy entry point: (re)login and return the raw handle."""
        with self._lock:
            self.sys_handle = self._raw_login()
            return self.sys_handle

    def log_out(self):
        with self._lock:
            if self.sys_handle is None:
                return 1
            return self.library.log_out(self.sys_handle)

    def get_crate_map(self, verbose=True):
        with self._lock:
            return self.library.get_crate_map(self.sys_handle, 1 if verbose else 0)

    # -------------------------------------------------- public: channel get/set
    def get_ch_power(self, slot, channel):
        return self._guard("get_ch_power", self.library.get_ch_power,
                           (int(slot), int(channel)), lambda r: r == _FAIL_INT)

    def get_ch_vmon(self, slot, channel):
        return self._guard("get_ch_vmon", self.library.get_ch_vmon,
                           (int(slot), int(channel)), lambda r: r == _FAIL_FLOAT)

    def get_ch_imon(self, slot, channel):
        return self._guard("get_ch_imon", self.library.get_ch_imon,
                           (int(slot), int(channel)), lambda r: r == _FAIL_FLOAT)

    def set_ch_v0(self, slot, channel, voltage):
        return self._guard("set_ch_v0", self.library.set_ch_v0,
                           (int(slot), int(channel), float(voltage)),
                           lambda r: r != _SET_OK)

    def set_ch_pw(self, slot, channel, pw):
        return self._guard("set_ch_pw", self.library.set_ch_pw,
                           (int(slot), int(channel), int(pw)),
                           lambda r: r != _SET_OK)

    # ------------------------------------------ public: named-parameter get/set
    def get_ch_param_ushort(self, slot, channel, param_name):
        return self._guard(
            f"get_ch_param_ushort[{param_name}]", self.library.get_ch_param_ushort,
            (int(slot), int(channel), param_name.encode("utf-8")),
            lambda r: r == _FAIL_USHORT)

    def get_ch_param_float(self, slot, channel, param_name):
        return self._guard(
            f"get_ch_param_float[{param_name}]", self.library.get_ch_param_float,
            (int(slot), int(channel), param_name.encode("utf-8")),
            lambda r: r == _FAIL_FLOAT)

    def set_ch_param_ushort(self, slot, channel, param_name, value):
        return self._guard(
            f"set_ch_param_ushort[{param_name}]", self.library.set_ch_param_ushort,
            (int(slot), int(channel), param_name.encode("utf-8"), int(value)),
            lambda r: r != _SET_OK)

    def set_ch_param_float(self, slot, channel, param_name, value):
        return self._guard(
            f"set_ch_param_float[{param_name}]", self.library.set_ch_param_float,
            (int(slot), int(channel), param_name.encode("utf-8"), float(value)),
            lambda r: r != _SET_OK)

    # --------------------------------------------- convenience named parameters
    def get_ch_i0set(self, slot, channel):
        """Current limit (I0Set) of a channel."""
        return self.get_ch_param_float(slot, channel, "I0Set")

    def set_ch_i0set(self, slot, channel, current):
        return self.set_ch_param_float(slot, channel, "I0Set", current)

    def get_ch_rup(self, slot, channel):
        """Ramp-up rate (Rup, V/s)."""
        return self.get_ch_param_float(slot, channel, "Rup")

    def set_ch_rup(self, slot, channel, rate):
        return self.set_ch_param_float(slot, channel, "Rup", rate)

    def get_ch_rdwn(self, slot, channel):
        """Ramp-down rate (RDWn, V/s)."""
        return self.get_ch_param_float(slot, channel, "RDWn")

    def set_ch_rdwn(self, slot, channel, rate):
        return self.set_ch_param_float(slot, channel, "RDWn", rate)

    def get_ch_trip(self, slot, channel):
        """Trip time (Trip, s)."""
        return self.get_ch_param_float(slot, channel, "Trip")

    def set_ch_trip(self, slot, channel, seconds):
        return self.set_ch_param_float(slot, channel, "Trip", seconds)
