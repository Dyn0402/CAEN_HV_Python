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
        self.log_in.restype = ctypes.POINTER(ctypes.c_int)

        # Define the function prototype for log_out
        self.log_out = self.library.log_out
        self.log_out.argtypes = [ctypes.c_int]

        # Define the function prototype for free
        self.free = self.library.free
        self.free.argtypes = [ctypes.c_void_p]

    def log_in_wrapper(self, ip_address, username, password):
        # Convert Python strings to bytes
        ip_bytes = ip_address.encode('utf-8')
        username_bytes = username.encode('utf-8')
        password_bytes = password.encode('utf-8')

        # Call the C function with the bytes and integer parameters
        result_ptr = self.log_in(ip_bytes, username_bytes, password_bytes)

        # Get the result value from the pointer
        sys_handle = result_ptr.contents.value

        # Free the memory allocated by the C function
        # self.free(result_ptr)

        # Return the result value
        return sys_handle

    def log_out_wrapper(self, sys_handle):
        # Call the C function with the integer parameter
        self.log_out(sys_handle)
