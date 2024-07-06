#!/usr/bin/env python

from setuptools import find_packages, setup

__version__ = "0.16.2"

setup(packages=find_packages(exclude=["*tests*"]))
