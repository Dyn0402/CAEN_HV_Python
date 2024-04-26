#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 25 7:09 PM 2024
Created in PyCharm
Created as CAEN_HV_Python/setup.py

@author: Dylan Neff, Dylan
"""

from setuptools import setup

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='caen_hv_py',
    version='1.6',
    description='Python wrapper for CAEN High Voltage C library.',
    author='Dylan Neff',
    author_email='dneff@ucla.edu',
    url='https://github.com/Dyn0402/CAEN_HV_Python',
    packages=['caen_hv_py'],
    package_data={'caen_hv_py': ['hv_c_lib/libhv_c.so', 'tests/*.py']},
    long_description=long_description,
    long_description_content_type='text/markdown'
)
