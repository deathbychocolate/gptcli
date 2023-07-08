#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="gptcli",
    version="0.1.0",
    description="A CLI tool for talking to the Openai API.",
    author="Damian Vonapartis",
    url="https://www.python.org/sigs/distutils-sig/",
    packages=find_packages(),
    entry_points={"console_scripts": ["gptcli = gptcli.main:main"]},
)
