# Changelog

## 2.0.0 — resilient sessions

The CAEN HV Wrapper session drops after ~15 s idle: the `sys_handle` goes
invalid and every C call returns a failure sentinel (`-1` for reads, `0` for
sets). Previously those sentinels were returned verbatim, so callers could not
tell a dead session from a real reading and would hang or misbehave. This
release makes `CAENHVController` own the session and heal itself.

### Added
- **Auto-reconnect** (`auto_reconnect=True`, default): a call that fails because
  the session died transparently re-logs-in and retries once. Callers never see
  the drop.
- **Keepalive** (`keepalive_s=<seconds>`, opt-in): a daemon thread touches the
  crate every `keepalive_s` seconds (use e.g. `10`, below the ~15 s timeout) so
  the handle never goes stale in the first place.
- **Typed exceptions** (`raise_on_error=True`, default): `CAENConnectionError`
  (session dead / unreachable and not recovered) and `CAENCommandError`
  (a get/set failed on a live session). Set `raise_on_error=False` for the old
  sentinel-returning behaviour.
- **Thread safety**: all C calls are serialised on an internal `RLock`, so a
  keepalive tick, a monitor read and a set can interleave safely.
- New methods: `connect()`, `close()`, `reconnect()`, `is_alive()`,
  `ensure_alive()`, `start_keepalive()`, `stop_keepalive()`, and the
  `reconnect_count` diagnostic property.
- Package now exports `CAENHVController` and the exception types from the top
  level, plus `__version__`.
- Hardware-free unit tests (`caen_hv_py/tests/test_resilience.py`) using a fake
  C library (`fake_lib.py`) that reproduces the 15 s drop on a manual clock.
  Run: `python -m unittest caen_hv_py.tests.test_resilience -v`.

### Changed / backwards compatibility
- Existing usage — `with CAENHVController(ip, user, pw) as hv: hv.get_ch_vmon(...)`
  — keeps working, and now auto-reconnects for free.
- **Behaviour change:** on an *unrecoverable* failure the methods now raise
  instead of returning `-1`/`0`. Pass `raise_on_error=False` to restore the old
  contract. (This is why the major version bumped to 2.)
- Prototype `argtypes`/`restype` are now bound once at connect instead of on
  every call.

### Known follow-ups (C layer — require the CAEN SDK + recompile on the DAQ host)
See `docs/C_LAYER_NOTES.md`. Notably: `get_crate_map` leaks the buffers returned
by `CAENHV_GetCrateMap` (missing `CAENHV_Free`); the C functions swallow the
`CAENHVRESULT` into ambiguous sentinels instead of returning it; and a cheap,
allocation-free `is_alive()` probe would be better than reusing `get_crate_map`.
