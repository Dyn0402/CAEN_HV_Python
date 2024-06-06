#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 25 1:12 PM 2024
Created in PyCharm
Created as CAEN_HV_Python/CAENHVController.py

@author: Dylan Neff, Dylan
"""

import ctypes
import ctypes.util
from pkg_resources import resource_filename


class CAENHVController:
    """
    Wrapper class for the CAEN HV C library. This class loads the shared library and defines the function prototypes
    Needed to call the functions in the shared library. The class has methods that call the C functions with the proper
    parameters and return the results.

    Need to make a call within 15 seconds of the last, otherwise the connection will be lost and the sys_handle will be
    invalid. This is a limitation of the C library.
    """
    def __init__(self, ip_address, username, password):
        self.library_path = resource_filename('caen_hv_py', 'hv_c_lib/libhv_c.so')
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.sys_handle = None

    def __enter__(self):
        # Load the shared library
        self.library = ctypes.CDLL(self.library_path)
        self.sys_handle = self.log_in()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sys_handle is not None:
            self.log_out()
            self.sys_handle = None

    def log_in(self):
        """
        Log into the HV system. This function calls the C function log_in with the ip_address, username, and password
        parameters and returns the result.
        :return:
        """

        # Convert Python strings to bytes
        ip_bytes = self.ip_address.encode('utf-8')
        username_bytes = self.username.encode('utf-8')
        password_bytes = self.password.encode('utf-8')

        # Define the function prototype for log_in
        log_in = self.library.log_in
        log_in.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        log_in.restype = ctypes.c_int

        # Call the C function with the bytes and integer parameters
        sys_handle = log_in(ip_bytes, username_bytes, password_bytes)

        # Return the result value
        return sys_handle

    def log_out(self):
        """
        Log out of the HV system. This function calls the C function log_out with the sys_handle parameter and returns
        the result.
        :return: Status of the log_out function.
        """
        log_out = self.library.log_out
        log_out.argtypes = [ctypes.c_int]
        log_out.restype = ctypes.c_int

        return log_out(self.sys_handle)

    def get_crate_map(self, verbose=True):
        """
        Get the crate map from the HV system. This function calls the C function get_crate_map with the sys_handle
        parameter and returns the result.
        :param verbose: Boolean, if True print the crate map to the console.
        :return:
        """
        get_crate_map = self.library.get_crate_map
        get_crate_map.argtypes = [ctypes.c_int, ctypes.c_int]
        get_crate_map.restype = ctypes.c_int

        return get_crate_map(self.sys_handle, verbose)

    def get_ch_power(self, slot, channel):
        """
        Get the power status of a channel. This function calls the C function get_ch_power with the sys_handle, slot,
        and channel parameters and returns the result.
        :param slot:
        :param channel:
        :return:
        """
        get_ch_power = self.library.get_ch_power
        get_ch_power.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        power = get_ch_power(self.sys_handle, slot, channel)
        return power

    def get_ch_vmon(self, slot, channel):
        get_ch_vmon = self.library.get_ch_vmon
        get_ch_vmon.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        get_ch_vmon.restype = ctypes.c_float
        vmon = get_ch_vmon(self.sys_handle, slot, channel)
        return vmon

    def get_ch_imon(self, slot, channel):
        get_ch_imon = self.library.get_ch_imon
        get_ch_imon.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        get_ch_imon.restype = ctypes.c_float
        imon = get_ch_imon(self.sys_handle, slot, channel)
        return imon

    def set_ch_v0(self, slot, channel, voltage):
        set_ch_v0 = self.library.set_ch_v0
        set_ch_v0.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_float]
        set_ch_v0.restype = ctypes.c_int
        return set_ch_v0(self.sys_handle, slot, channel, voltage)

    def set_ch_pw(self, slot, channel, pw):
        set_ch_pw = self.library.set_ch_pw
        set_ch_pw.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        set_ch_pw.restype = ctypes.c_int
        return set_ch_pw(self.sys_handle, slot, channel, pw)
