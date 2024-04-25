#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 25 7:09 PM 2024
Created in PyCharm
Created as CAEN_HV_Python/setup.py

@author: Dylan Neff, Dylan
"""

from setuptools import setup

setup(
    name='CAEN_HV_Python',
    version='1.0',
    description='Python wrapper for CAEN High Voltage C library.',
    author='Dylan Neff',
    author_email='dneff@ucla.edu',
    url='https://github.com/Dyn0402/CAEN_HV_Python',
    # packages=['CAEN_HV_Python'],
    data_files=[('libs', ['hv_c_lib/libhv_c.so'])],
)
