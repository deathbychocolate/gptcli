#!/usr/bin/env python

from setuptools import find_packages, setup

__version__ = "0.8.0"

setup(
    name="gptcli",
    version=__version__,
    description="A CLI tool for talking to the Openai API.",
    author="Damian Vonapartis",
    url="https://www.python.org/sigs/distutils-sig/",
    packages=find_packages(exclude=["*tests*"]),
    entry_points={"console_scripts": ["gptcli = gptcli.main:main"]},
)
