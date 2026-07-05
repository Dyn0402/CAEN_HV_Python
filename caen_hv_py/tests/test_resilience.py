#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware-free tests for CAENHVController's session resilience, using FakeHVLib
(which reproduces the ~15 s idle session drop) and a manual clock.

Run:  python -m unittest caen_hv_py.tests.test_resilience -v
"""
import threading
import unittest

from caen_hv_py.CAENHVController import CAENHVController
from caen_hv_py.exceptions import CAENConnectionError, CAENCommandError
from caen_hv_py.tests.fake_lib import FakeHVLib, FakeClock


def make(clock=None, **lib_kwargs):
    """Controller wired to a fresh FakeHVLib on a shared clock."""
    clock = clock or FakeClock()
    lib = FakeHVLib(clock=clock, **lib_kwargs)
    ctrl = CAENHVController("1.2.3.4", "user", "pw", library=lib,
                            reconnect_backoff_s=0)
    return ctrl, lib, clock


class TestBasics(unittest.TestCase):
    def test_context_manager_roundtrip(self):
        ctrl, lib, clock = make()
        with ctrl:
            self.assertTrue(ctrl.is_alive())
            ctrl.set_ch_pw(5, 1, 1)
            ctrl.set_ch_v0(5, 1, 480.0)
            self.assertEqual(ctrl.get_ch_power(5, 1), 1)
            self.assertAlmostEqual(ctrl.get_ch_vmon(5, 1), 480.0)
        # closed -> logged out
        self.assertIsNone(ctrl.sys_handle)

    def test_connect_failure_raises(self):
        ctrl, lib, clock = make(fail_logins=99)
        with self.assertRaises(CAENConnectionError):
            ctrl.connect()


class TestReconnect(unittest.TestCase):
    def test_idle_drop_autoreconnects_transparently(self):
        ctrl, lib, clock = make()
        with ctrl:
            ctrl.set_ch_pw(5, 1, 1)
            ctrl.set_ch_v0(5, 1, 500.0)
            clock.advance(20)                      # > 15 s idle -> session dies
            # Caller sees a normal value; the drop was healed under the hood.
            self.assertAlmostEqual(ctrl.get_ch_vmon(5, 1), 500.0)
            self.assertEqual(ctrl.reconnect_count, 1)
            self.assertEqual(lib.login_calls, 2)   # initial + one reconnect

    def test_no_autoreconnect_raises_connection_error(self):
        ctrl, lib, clock = make()
        ctrl.auto_reconnect = False
        with ctrl:
            clock.advance(20)
            with self.assertRaises(CAENConnectionError):
                ctrl.get_ch_vmon(5, 1)

    def test_legacy_sentinel_mode(self):
        ctrl, lib, clock = make()
        ctrl.auto_reconnect = False
        ctrl.raise_on_error = False
        with ctrl:
            clock.advance(20)
            self.assertEqual(ctrl.get_ch_vmon(5, 1), -1.0)   # legacy behaviour

    def test_reconnect_exhaustion_raises(self):
        # session dies, and every re-login also fails -> give up with an error
        ctrl, lib, clock = make(fail_logins=0)
        with ctrl:
            clock.advance(20)
            lib._fail_logins = 99          # all future logins fail
            ctrl.max_reconnect_attempts = 3
            with self.assertRaises(CAENConnectionError):
                ctrl.get_ch_vmon(5, 1)
            self.assertGreaterEqual(lib.login_calls, 1 + 3)

    def test_command_error_when_session_alive(self):
        # A failing call while the session is healthy -> CAENCommandError,
        # NOT a reconnect (no session churn).
        class BadChannelLib(FakeHVLib):
            def get_ch_vmon(self, h, slot, chan):
                if not self._alive(h):
                    return -1.0
                self._touch()
                return -1.0  # alive but this read "fails"
        clock = FakeClock()
        lib = BadChannelLib(clock=clock)
        ctrl = CAENHVController("1.2.3.4", "u", "p", library=lib, reconnect_backoff_s=0)
        with ctrl:
            with self.assertRaises(CAENCommandError):
                ctrl.get_ch_vmon(5, 1)
            self.assertEqual(ctrl.reconnect_count, 0)


class TestKeepalive(unittest.TestCase):
    # These drive _keepalive_tick() directly (instead of the background thread)
    # so the timing is deterministic and no real sleeping happens.
    def test_keepalive_prevents_drop(self):
        ctrl, lib, clock = make()
        ctrl.connect()
        try:
            # Tick every 10 s (< 15 s timeout) across a span that would
            # otherwise drop the session many times.
            for _ in range(10):
                clock.advance(10)
                ctrl._keepalive_tick()
            self.assertTrue(ctrl.is_alive())
            self.assertEqual(ctrl.reconnect_count, 0)   # never had to reconnect
        finally:
            ctrl.close()

    def test_keepalive_reconnects_if_dead(self):
        ctrl, lib, clock = make()
        ctrl.connect()
        try:
            clock.advance(20)          # miss a beat -> session dies
            ctrl._keepalive_tick()     # keepalive notices and heals it
            self.assertTrue(ctrl.is_alive())
            self.assertEqual(ctrl.reconnect_count, 1)
        finally:
            ctrl.close()


class TestThreadSafety(unittest.TestCase):
    def test_concurrent_calls_do_not_crash(self):
        ctrl, lib, clock = make()
        errors = []

        def worker():
            try:
                for _ in range(200):
                    ctrl.set_ch_v0(5, 1, 500.0)
                    ctrl.get_ch_vmon(5, 1)
                    ctrl.get_ch_power(5, 1)
            except Exception as e:  # pragma: no cover
                errors.append(e)

        with ctrl:
            ctrl.set_ch_pw(5, 1, 1)
            threads = [threading.Thread(target=worker) for _ in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
