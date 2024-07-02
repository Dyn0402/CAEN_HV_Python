#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on July 02 11:05 AM 2024
Created in PyCharm
Created as CAEN_HV_Python/get_set_param_test.py

@author: Dylan Neff, Dylan
"""

from caen_hv_py.CAENHVController import CAENHVController


def main():
    ip_address = '192.168.10.81'
    username = 'admin'
    password = 'admin'

    with CAENHVController(ip_address, username, password) as hv_wrapper:
        print(hv_wrapper.get_ch_param_float(3, 2, 'VMon'))
        print(hv_wrapper.get_ch_param_ushort(3, 2, 'Pw'))

    print('donzo')


if __name__ == '__main__':
    main()
