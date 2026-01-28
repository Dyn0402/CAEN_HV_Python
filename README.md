# CAEN_HV_Python
Python wrapper around C wrapper for CAEN HV crate control, whose manual is included in the git repository.
**You must download and install the CAEN C wrapper from CAEN's website before using this package.**
Website Link: https://www.caen.it/download/?filter=CAEN%20HV%20Wrapper%20Library
Currently only impelements functions for logging into and out of a CAEN HV crate over IP, reading and setting power status, setting HV target values, reading HV monitor values, and reading current monitor values.
All reads and writes are currently implemented one channel at a time, though the C wrapper supports reading and writing to multiple channels at once.

The user must specify and pass the crate IP address, username, and password to the CAENHVController initialization.
It is noted in CAEN C wrapper manual that some models will disconnect if there has been no communication for 15 seconds.

An example implementation is shown below.

```python
from caen_hv_py.CAENHVController import CAENHVController
from time import sleep

ip_address = '192.168.20.20'  # Enter your CAEN HV Crate IP address
username = 'user'  # Enter your CAEN HV Crate Username
password = 'pass'  # Enter your CAEN HV Crate Password

slot = 1
channels = [0, 1, 2, 3, 4]
v0s = [50, 100, 150, 200, 250]

with CAENHVController(ip_address, username, password) as hv_wrapper:
    print('Turning off channels')
    for channel in channels:
        power = hv_wrapper.get_ch_power(slot, channel)
        if power:
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
        power = hv_wrapper.get_ch_power(slot, channel)
        if not power:
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
        power = hv_wrapper.get_ch_power(slot, channel)
        if power:
            hv_wrapper.set_ch_pw(slot, channel, 0)

print('Finshed')
```

The predefined functions in the example above are tailored to a specific board. 
A new set of generic functions were added which should allow the user to get and set any parameter by name. 
There are separate functions for each data type. Unsigned short and float are the only two currently implemented. 

NOTE: If the parameter name is incorrect or not found, these functions will simply retrun their error codes. 
For the get functions, the error code is -1. For the set functions, the error code is 0 (success is 1).

An example of how to use these functions is shown below.

```python
from caen_hv_py.CAENHVController import CAENHVController
from time import sleep

ip_address = '192.168.20.20'  # Enter your CAEN HV Crate IP address
username = 'user'  # Enter your CAEN HV Crate Username
password = 'pass'  # Enter your CAEN HV Crate Password

slot = 1
channel = 2

with CAENHVController(ip_address, username, password) as hv_wrapper:
    print('Read status')
    status = hv_wrapper.get_ch_param_ushort(slot, channel, 'Status')
    print(f'Status: {status}')

    print('Read "Imax Set" float parameter')
    imax_set = hv_wrapper.get_ch_param_float(slot, channel, 'Imax Set')
    print(f'Imax Set: {imax_set}')
    
    print('Set "Imax Set" float parameter')
    hv_wrapper.set_ch_param_float(slot, channel, 'Imax Set', 1.2)
    
print('Finshed')
```

# Ubuntu 24 Note!
Many of the dependencies for CAEN's HV Wrapper library are not directly available in Ubuntu 24:
- libncurses.so.5 is now version 6
- libtinfo.so.5 is now version 6
- libcrypto.so.1.1 is now version 3

In addition, when installed with CAENHVWrapper, libcaenhvwrapper.so is installed in /usr/lib64, which is not a library path by default.

## To fix
The correct versions of the dependencies need to be installed manually and the path updated. AI summary below.


#Ubuntu 24.04 (Noble Numbat) Compatibility Note
Ubuntu 24.04 has deprecated several legacy libraries required by the CAEN HV Wrapper (notably OpenSSL 1.1 and Ncurses 5). To run this software on Ubuntu 24.04, you must manually install the legacy versions from the Ubuntu 22.04 (Jammy) archives and register the CAEN library path.

1. Install Legacy Dependencies
Run the following commands to download and install the required versions of libssl, libtinfo, and libncurses.


# Create a temporary directory for compatibility packages
mkdir caen_compat && cd caen_compat

# Download OpenSSL 1.1 (Required for libcrypto.so.1.1)
wget http://security.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.24_amd64.deb

# Download Ncurses 5 and Tinfo 5
wget http://mirrors.kernel.org/ubuntu/pool/universe/n/ncurses/libtinfo5_6.3-2ubuntu0.1_amd64.deb
wget http://mirrors.kernel.org/ubuntu/pool/universe/n/ncurses/libncurses5_6.3-2ubuntu0.1_amd64.deb

# Install packages
sudo dpkg -i libssl1.1_1.1.1f-1ubuntu2.24_amd64.deb
sudo dpkg -i libtinfo5_6.3-2ubuntu0.1_amd64.deb
sudo dpkg -i libncurses5_6.3-2ubuntu0.1_amd64.deb

cd ..
2. Configure CAEN Library Path
The CAEN HV Wrapper installer places libraries in /usr/lib64, which is not searched by default in Ubuntu. You must add this path to the dynamic linker configuration:

Bash
# Add /usr/lib64 to the ld configuration
sudo sh -c 'echo "/usr/lib64" > /etc/ld.so.conf.d/caen.conf'

# Update the linker cache
sudo ldconfig
3. Verify Installation
Ensure all dependencies are resolved and the CAEN library is recognized:

Bash
# Check if the CAEN wrapper is mapped correctly
ldconfig -p | grep caenhv

# Check the binary dependencies (run this in your build folder)
ldd <your_executable_name> | grep -E "ncurses|tinfo|crypto|caen"
Warning: These manual installations bypass the standard Ubuntu 24.04 package manager tracking. Keep these .deb files or this documentation handy, as system upgrades may occasionally remove legacy libraries.