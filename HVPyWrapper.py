#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 25 1:12 PM 2024
Created in PyCharm
Created as CAEN_HV_Python/HVPyWrapper.py

@author: Dylan Neff, Dylan
"""

import ctypes


class HVPyWrapper:
    def __init__(self, library_path):
        # Load the shared library
        self.library = ctypes.CDLL(library_path)

        # Define the function prototype for log_in
        self.log_in = self.library.log_in
        self.log_in.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        self.log_in.restype = ctypes.c_int

        # Define the function prototype for log_out
        self.log_out = self.library.log_out
        self.log_out.argtypes = [ctypes.c_int]

        # Define the function prototype for get_ch_power
        self.get_ch_power = self.library.get_ch_power
        self.get_ch_power.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]

        # Define the function prototype for get_ch_vmon
        self.get_ch_vmon = self.library.get_ch_vmon
        self.get_ch_vmon.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]

        # Define the function prototype for set_ch_v0
        self.set_ch_v0 = self.library.set_ch_v0
        self.set_ch_v0.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_float]

        # Define the function prototype for set_ch_pw
        self.set_ch_pw = self.library.set_ch_pw
        self.set_ch_pw.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

    def log_in_wrapper(self, ip_address, username, password):
        # Convert Python strings to bytes
        ip_bytes = ip_address.encode('utf-8')
        username_bytes = username.encode('utf-8')
        password_bytes = password.encode('utf-8')

        # Call the C function with the bytes and integer parameters
        sys_handle = self.log_in(ip_bytes, username_bytes, password_bytes)

        # Return the result value
        return sys_handle

    def log_out_wrapper(self, sys_handle):
        # Call the C function with the integer parameter
        self.log_out(sys_handle)

    def get_ch_power_wrapper(self, sys_handle, slot, channel):
        # Call the C function with the integer parameter
        power = self.get_ch_power(sys_handle, slot, channel)
        return power

    def get_ch_vmon_wrapper(self, sys_handle, slot, channel):
        # Call the C function with the integer parameter
        vmon = self.get_ch_vmon(sys_handle, slot, channel)
        return vmon

    def set_ch_v0_wrapper(self, sys_handle, slot, channel, voltage):
        # Call the C function with the integer parameter
        self.set_ch_v0(sys_handle, slot, channel, voltage)

    def set_ch_pw_wrapper(self, sys_handle, slot, channel, pw):
        # Call the C function with the integer parameter
        self.set_ch_pw(sys_handle, slot, channel, pw)
