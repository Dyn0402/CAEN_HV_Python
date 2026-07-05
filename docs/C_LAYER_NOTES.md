# C layer (hv_c_lib) — follow-up improvements

The v2 resilience fix is **pure Python** on purpose: rebuilding `libhv_c.so`
needs the CAEN HV Wrapper SDK (`CAENHVWrapper.h`, `libcaenhvwrapper.so`), which
is only installed on the DAQ host. Everything below should be done there, then
recompiled (`make` in `caen_hv_py/hv_c_lib/`) and tested against the crate.

None of these are required for correctness — the Python layer papers over them —
but they make the wrapper cleaner and remove one real bug.

## 1. Memory leak in `get_crate_map` (real bug — fix this)
`CAENHV_GetCrateMap` allocates `ModelList`, `DescriptionList`, `SerNumList`,
`NrOfChList`, `FmwRelMinList`, `FmwRelMaxList`; the caller must free them with
`CAENHV_Free`. `get_crate_map()` never does, so every call leaks. The Python
layer uses `get_crate_map` as its liveness probe (on the failure path, and for
keepalive), so over long runs this accumulates. Add, before returning:

```c
CAENHV_Free(ModelList); CAENHV_Free(DescriptionList); CAENHV_Free(SerNumList);
CAENHV_Free(NrOfCh);   CAENHV_Free(FmwRelMinList);    CAENHV_Free(FmwRelMaxList);
```
(Confirm the exact set/semantics against the installed `CAENHVWrapper.h`.)

## 2. Return the real status instead of ambiguous sentinels
Today every function collapses failure into `-1` / `0` and `printf`s. That is
what forced the Python layer to disambiguate with a `get_crate_map` probe.
Cleaner: expose the `CAENHVRESULT`, e.g. give getters an out-parameter for the
value and return the status code, or add a `caen_last_result()` accessor. Then
the Python `_guard` can branch on the actual code (e.g. distinguish
`CFE server down`/comms from a bad channel) without the extra probe.

## 3. Add a cheap, allocation-free `is_alive()` probe
`get_crate_map` is relatively heavy and (see #1) allocates. A lightweight
`int is_alive(int sys_handle)` that reads a single system property
(`CAENHV_GetSysProp`, or one `CAENHV_GetChParam` on a known channel) and returns
1/0 would be a better keepalive/liveness call. Wire it into
`CAENHVController._probe_alive_locked()` in place of `get_crate_map` once present.

## 4. Stop printing to stdout from the library
`printf("Voltage read bad\n")` etc. belongs to the application, not a library —
it's what produced the noisy "CFE server down" spam in the DAQ pane. Prefer
returning status (#2) and letting the Python layer log via the `caen_hv_py`
logger.

## Testing the C changes
After recompiling on the DAQ host, the Python `test_resilience.py` suite still
runs against the *fake* lib (no hardware). For the real lib, add a small
hardware smoke test (behind an env flag) that logs in, idles >15 s, and confirms
`ensure_alive()` / a normal call transparently recovers.
