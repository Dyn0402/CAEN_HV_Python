#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 25 1:03 PM 2024
Created in PyCharm
Created as CAEN_HV_Python/main.py

@author: Dylan Neff, Dylan
"""

from HVPyWrapper import HVPyWrapper
from time import sleep


def main():
    lib_path = 'hv_c_lib/libhv_c.so'
    ip_address = '192.168.10.81'
    username = 'admin'
    password = 'admin'

    slot = 1
    channels = [0, 1, 2, 3, 4]
    v0s = [50, 100, 150, 200, 250]

    with HVPyWrapper(lib_path, ip_address, username, password) as hv_wrapper:
        print('Turning off channels')
        for channel in channels:
            hv_wrapper.set_ch_pw_wrapper(slot, channel, 0)
            sleep(1)

        sleep(5)

        print('Setting channels V0')
        for channel, v0 in zip(channels, v0s):
            hv_wrapper.set_ch_v0_wrapper(slot, channel, v0)
            sleep(1)

        sleep(5)

        print('Turning on channels')
        for channel in channels:
            hv_wrapper.set_ch_pw_wrapper(slot, channel, 1)
            sleep(1)

        sleep(10)

        print('Getting channel power and Vmon')
        for channel in channels:
            power = hv_wrapper.get_ch_power_wrapper(slot, channel)
            vmon = hv_wrapper.get_ch_vmon_wrapper(slot, channel)
            print(f'Channel {channel} power: {power} Vmon: {vmon}')

        sleep(5)

        print('Turning off channels')
        for channel in channels:
            hv_wrapper.set_ch_pw_wrapper(slot, channel, 0)

    print('donzo')


if __name__ == '__main__':
    main()
