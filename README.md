# CAEN_HV_Python
Python wrapper around C wrapper for CAEN HV crate control, whose manual is included in the git repository.
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