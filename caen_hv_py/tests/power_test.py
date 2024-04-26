#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 26 1:02 PM 2024
Created in PyCharm
Created as CAEN_HV_Python/power_test.py

@author: Dylan Neff, Dylan
"""

from caen_hv_py.CAENHVController import CAENHVController


def main():
    ip_address = '192.168.10.81'
    username = 'admin'
    password = 'admin'

    with CAENHVController(ip_address, username, password) as hv_wrapper:
        hv_wrapper.set_ch_pw(1, 3, 1)
    print('donzo')


if __name__ == '__main__':
    main()
