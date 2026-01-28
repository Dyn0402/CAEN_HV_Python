#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 26 1:02 PM 2024
Created in PyCharm
Created as CAEN_HV_Python/power_test.py

@author: Dylan Neff, Dylan
"""

from caen_hv_py.CAENHVController import CAENHVController
from time import sleep


def main():
    ip_address = '192.168.10.81'
    username = 'admin'
    password = 'admin'

    with CAENHVController(ip_address, username, password) as hv_wrapper:
        print(f'Power before: {hv_wrapper.get_ch_power(1, 3)}')
        print(f'Turning channel on...')
        hv_wrapper.set_ch_pw(1, 3, 1)
        sleep(0.1)
        print(f'Power after: {hv_wrapper.get_ch_power(1, 3)}')
        print(f'Turning channel off...')
        hv_wrapper.set_ch_pw(1, 3, 0)
        sleep(0.1)
        print(f'Power after: {hv_wrapper.get_ch_power(1, 3)}')
    print('donzo')


if __name__ == '__main__':
    main()
