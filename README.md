# CAEN_HV_Python

A thin Python wrapper around CAEN's HV Wrapper C library for controlling a CAEN High Voltage crate over IP.

The CAEN HV Wrapper manual (`HV Wrapper_REV17.pdf`) is included in this repository for reference.

## Features

- Log in / out of a CAEN HV crate over TCP/IP.
- Read and set channel power (on/off).
- Set target voltage (`V0Set`) and read voltage/current monitors (`VMon`, `IMon`).
- Set/read current limit (`I0Set`), ramp-up rate (`Rup`), ramp-down rate (`RDWn`), and trip time (`Trip`).
- Generic get/set helpers for **any** channel parameter by name (float and unsigned-short types).

All reads and writes are currently performed one channel at a time, though the underlying C wrapper supports operating on multiple channels in a single call.

## Requirements

> [!IMPORTANT]
> You must download and install the **CAEN HV Wrapper Library** from CAEN's website before using this package. This Python package links against CAEN's shared library at runtime.
>
> Download: https://www.caen.it/download/?filter=CAEN%20HV%20Wrapper%20Library

- Python 3.7+ (`importlib-resources` is pulled in automatically on 3.7–3.8).
- The CAEN HV Wrapper library installed and resolvable by the dynamic linker (see [Ubuntu 24.04 Compatibility](#ubuntu-2404-compatibility) if you are on Noble Numbat).

## Installation

Install from the project root:

```bash
pip install .
```

Or, for development (editable) installs:

```bash
pip install -e .
```

## Connecting

The crate IP address, username, and password are passed to `CAENHVController`. Use it as a context manager so login/logout are handled automatically:

```python
from caen_hv_py.CAENHVController import CAENHVController

with CAENHVController('192.168.20.20', 'user', 'pass') as hv:
    ...
```

> [!NOTE]
> Some crate models will **drop the connection after 15 seconds of inactivity**. If you need to hold a connection open, make a call (e.g. a monitor read) at least every ~15 seconds to keep it alive.

## Quick start

```python
from caen_hv_py.CAENHVController import CAENHVController
from time import sleep

ip_address = '192.168.20.20'  # Enter your CAEN HV Crate IP address
username = 'user'             # Enter your CAEN HV Crate Username
password = 'pass'             # Enter your CAEN HV Crate Password

slot = 1
channels = [0, 1, 2, 3, 4]
v0s = [50, 100, 150, 200, 250]

with CAENHVController(ip_address, username, password) as hv_wrapper:
    print('Turning off channels')
    for channel in channels:
        if hv_wrapper.get_ch_power(slot, channel):
            hv_wrapper.set_ch_pw(slot, channel, 0)
        sleep(1)

    sleep(5)

    print('Setting channels V0')
    for channel, v0 in zip(channels, v0s):
        hv_wrapper.set_ch_v0(slot, channel, v0)
        sleep(1)

    sleep(5)

    print('Turning on channels')
    for channel in channels:
        if not hv_wrapper.get_ch_power(slot, channel):
            hv_wrapper.set_ch_pw(slot, channel, 1)
        sleep(1)

    sleep(10)

    print('Getting channel power and Vmon')
    for channel in channels:
        power = hv_wrapper.get_ch_power(slot, channel)
        vmon = hv_wrapper.get_ch_vmon(slot, channel)
        imon = hv_wrapper.get_ch_imon(slot, channel)
        print(f'Channel {channel} power: {power} Vmon: {vmon}, Imon: {imon}')

    sleep(5)

    print('Turning off channels')
    for channel in channels:
        if hv_wrapper.get_ch_power(slot, channel):
            hv_wrapper.set_ch_pw(slot, channel, 0)

print('Finished')
```

## Channel limits and ramp control

Convenience methods are provided for the current limit, ramp rates, and trip time. These wrap the generic float helpers, so they work on any board that exposes the corresponding parameter.

```python
with CAENHVController(ip_address, username, password) as hv:
    slot, channel = 1, 2

    hv.set_ch_i0set(slot, channel, 5.0)   # current limit (board units, e.g. uA)
    hv.set_ch_rup(slot, channel, 50)      # ramp-up rate, V/s
    hv.set_ch_rdwn(slot, channel, 100)    # ramp-down rate, V/s
    hv.set_ch_trip(slot, channel, 2.0)    # trip time, seconds

    print(hv.get_ch_i0set(slot, channel))
    print(hv.get_ch_rup(slot, channel))
    print(hv.get_ch_rdwn(slot, channel))
    print(hv.get_ch_trip(slot, channel))
```

> [!NOTE]
> Units and resolution are **board-defined**. `Trip` is in seconds; `I0Set` may be in µA or nA depending on the board. Check your board's manual for exact units. The wrapper passes values through unchanged.

## Generic parameter access

The named methods above are tailored to common parameters. For anything else, use the generic get/set helpers, which can read or write any parameter by name. There is a separate function per data type — **float** and **unsigned short** are currently implemented.

```python
with CAENHVController(ip_address, username, password) as hv_wrapper:
    slot, channel = 1, 2

    print('Read status (unsigned short)')
    status = hv_wrapper.get_ch_param_ushort(slot, channel, 'Status')
    print(f'Status: {status}')

    print('Read "I0Set" float parameter')
    i0set = hv_wrapper.get_ch_param_float(slot, channel, 'I0Set')
    print(f'I0Set: {i0set}')

    print('Set "I0Set" float parameter')
    hv_wrapper.set_ch_param_float(slot, channel, 'I0Set', 1.2)
```

> [!WARNING]
> If a parameter name is wrong, unsupported by the board, or of the wrong type, these functions **return an error code rather than raising**:
> - **get** functions return `-1` on failure.
> - **set** functions return `0` on failure (and `1` on success).

## API reference

All channel methods take `slot` and `channel` (both 0-indexed integers) as their first arguments.

| Method | CAEN param | Returns / sets | Notes |
|--------|-----------|----------------|-------|
| `get_crate_map(verbose=True)` | — | crate info | Prints crate map when `verbose`. |
| `get_ch_power(slot, ch)` | `Pw` | int (0/1) | Power state; `-1` on error. |
| `set_ch_pw(slot, ch, pw)` | `Pw` | int (1/0) | `pw` = 1 (on) or 0 (off). |
| `get_ch_vmon(slot, ch)` | `VMon` | float | Voltage monitor. |
| `get_ch_imon(slot, ch)` | `IMon` | float | Current monitor. |
| `set_ch_v0(slot, ch, voltage)` | `V0Set` | int (1/0) | Target voltage. |
| `get_ch_i0set(slot, ch)` / `set_ch_i0set(slot, ch, current)` | `I0Set` | float | Current limit. |
| `get_ch_rup(slot, ch)` / `set_ch_rup(slot, ch, rate)` | `Rup` | float | Ramp-up rate, V/s. |
| `get_ch_rdwn(slot, ch)` / `set_ch_rdwn(slot, ch, rate)` | `RDWn` | float | Ramp-down rate, V/s. |
| `get_ch_trip(slot, ch)` / `set_ch_trip(slot, ch, seconds)` | `Trip` | float | Trip time, seconds. |
| `get_ch_param_float(slot, ch, name)` / `set_ch_param_float(slot, ch, name, value)` | any | float | Generic float access. |
| `get_ch_param_ushort(slot, ch, name)` / `set_ch_param_ushort(slot, ch, name, value)` | any | ushort | Generic unsigned-short access. |

### Common channel parameters (A1832 board)

Parameter names and types are **board-specific**. The table below lists the A1832 board's channel parameters as an example (see the manual / your board's user guide for others). Use a float helper for `Float` types and an unsigned-short helper for `Unsigned` types.

| Parameter | Type | Meaning |
|-----------|------|---------|
| `V0Set` | Float | Set V0 voltage limit |
| `I0Set` | Float | Set I0 current limit |
| `V1Set` | Float | Set V1 voltage limit |
| `I1Set` | Float | Set I1 current limit |
| `Rup` | Float | Ramp-up rate |
| `RDWn` | Float | Ramp-down rate |
| `Trip` | Float | Trip time |
| `SVMax` | Float | Software voltage limit |
| `VMon` | Float | Voltage monitor |
| `IMon` | Float | Current monitor |
| `Status` | Unsigned (bitfield) | Channel status |
| `Pw` | Unsigned (boolean) | Power ON/OFF |
| `Pon` | Unsigned (boolean) | Power-on options |
| `PDwn` | Unsigned (boolean) | Power-down options |
| `TripInt` | Unsigned | Internal trip connections |
| `TripExt` | Unsigned | External trip connections |

> [!NOTE]
> The ramp-up parameter is spelled `Rup` in the wrapper, even though the front panel / GUI column may display it as `RUp`.

## Ubuntu 24.04 Compatibility

Ubuntu 24.04 (Noble Numbat) has deprecated several legacy libraries required by the CAEN HV Wrapper:

- `libncurses.so.5` → now version 6
- `libtinfo.so.5` → now version 6
- `libcrypto.so.1.1` → now version 3 (OpenSSL 1.1 → 3)

In addition, the CAEN installer places `libcaenhvwrapper.so` in `/usr/lib64`, which is **not** a default library search path on Ubuntu.

To run on Ubuntu 24.04 you must manually install the legacy library versions from the Ubuntu 22.04 (Jammy) archives and register the CAEN library path.

### 1. Install legacy dependencies

```bash
# Create a temporary directory for compatibility packages
mkdir caen_compat && cd caen_compat

# Download OpenSSL 1.1 (provides libcrypto.so.1.1)
wget http://security.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.24_amd64.deb

# Download Ncurses 5 and Tinfo 5
wget http://mirrors.kernel.org/ubuntu/pool/universe/n/ncurses/libtinfo5_6.3-2ubuntu0.1_amd64.deb
wget http://mirrors.kernel.org/ubuntu/pool/universe/n/ncurses/libncurses5_6.3-2ubuntu0.1_amd64.deb

# Install packages
sudo dpkg -i libssl1.1_1.1.1f-1ubuntu2.24_amd64.deb
sudo dpkg -i libtinfo5_6.3-2ubuntu0.1_amd64.deb
sudo dpkg -i libncurses5_6.3-2ubuntu0.1_amd64.deb

cd ..
```

### 2. Configure the CAEN library path

```bash
# Add /usr/lib64 to the ld configuration
sudo sh -c 'echo "/usr/lib64" > /etc/ld.so.conf.d/caen.conf'

# Update the linker cache
sudo ldconfig
```

### 3. Verify the installation

```bash
# Check that the CAEN wrapper is mapped correctly
ldconfig -p | grep caenhv

# Check binary dependencies (run from your build folder)
ldd <your_executable_name> | grep -E "ncurses|tinfo|crypto|caen"
```

> [!WARNING]
> These manual installations bypass standard Ubuntu 24.04 package tracking. Keep these `.deb` files (or this documentation) handy, as system upgrades may remove the legacy libraries.

## Resilient sessions (v2.0)

The CAEN HV Wrapper session is dropped after **~15 s with no calls** — the
`sys_handle` goes invalid and subsequent calls fail (reads return `-1`, and the
library prints things like `CFE server down`). As of v2.0 `CAENHVController`
owns the session and heals itself, so you don't have to babysit it.

- **Auto-reconnect (default on):** a call that fails because the session died is
  transparently re-logged-in and retried once — the caller just gets the value.
- **Keepalive (opt-in):** pass `keepalive_s=10` and a background thread touches
  the crate every 10 s so the handle never goes stale in the first place.
- **Typed errors (default):** unrecoverable failures raise `CAENConnectionError`
  (session dead/unreachable) or `CAENCommandError` (a get/set failed on a live
  session) instead of returning an ambiguous `-1`. Pass `raise_on_error=False`
  for the legacy sentinel behaviour.
- **Thread-safe:** all calls are serialised internally, so a monitor loop, a
  keepalive tick and a set can run from different threads safely.

```python
from caen_hv_py import CAENHVController, CAENConnectionError

# Keep the handle warm and self-heal if it ever drops:
with CAENHVController(ip, user, pw, keepalive_s=10) as hv:
    hv.set_ch_v0(5, 1, 480.0)
    print(hv.get_ch_vmon(5, 1))   # never spuriously -1 across an idle gap

# Or probe/heal explicitly before a batch of operations:
with CAENHVController(ip, user, pw) as hv:
    hv.ensure_alive()             # reconnects if the session died
    ...
```

Existing code (`with CAENHVController(ip, user, pw) as hv: ...`) keeps working
unchanged and gains auto-reconnect for free.

### Tests

Session/reconnect/keepalive logic is covered by hardware-free unit tests that
use a fake C library reproducing the 15 s drop on a manual clock:

```bash
python -m unittest caen_hv_py.tests.test_resilience -v
```

See `CHANGELOG.md` for the full v2.0 notes and `docs/C_LAYER_NOTES.md` for the
remaining C-layer follow-ups (they require the CAEN SDK to recompile).
