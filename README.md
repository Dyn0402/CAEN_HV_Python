# CAEN_HV_Python
Python wrapper around C wrapper for CAEN HV crate control.
Currently only impelements functions for logging into and out of a CAEN HV crate over IP, reading and setting power status, setting HV target values, and reading HV monitor values.
An example implementation is shown below.

```python
from caen_hv_python.CAENHVController import CAENHVController
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
        print(f'Channel {channel} power: {power} Vmon: {vmon}')

    sleep(5)

    print('Turning off channels')
    for channel in channels:
        power = hv_wrapper.get_ch_power(slot, channel)
        if power:
            hv_wrapper.set_ch_pw(slot, channel, 0)

print('Finshed')
