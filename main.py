#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 25 1:03 PM 2024
Created in PyCharm
Created as CAEN_HV_Python/main.py

@author: Dylan Neff, Dylan
"""

from HVPyWrapper import HVPyWrapper


def main():
    lib_path = 'hv_c_lib/libhv_c.so'
    ip_address = '192.168.10.81'
    username = 'admin'
    password = 'admin'

    slot = 0
    channels = [0, 1, 2, 3, 4]

    hv_c_lib = HVPyWrapper(lib_path)
    sys_handle = hv_c_lib.log_in_wrapper(ip_address, username, password)
    print(f'sys_handle: {sys_handle}')
    for channel in channels:
        power = hv_c_lib.get_ch_power_wrapper(sys_handle, slot, channel)
        vmon = hv_c_lib.get_ch_vmon_wrapper(sys_handle, slot, channel)
        print(f'Channel {channel} power: {power} Vmon: {vmon}')
    hv_c_lib.log_out_wrapper(sys_handle)

    print('donzo')


if __name__ == '__main__':
    main()
