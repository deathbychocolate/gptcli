#!/usr/bin/env python

from glob import glob

from mypyc.build import mypycify
from setuptools import find_packages, setup

paths: list[str] = glob("gptcli/**.py")
paths += glob("gptcli/src/**.py")

setup(
    packages=find_packages(exclude=["*tests*"]),
    # ext_modules=mypycify(paths),  # uncomment to generate wheel with platform specific C code
)
