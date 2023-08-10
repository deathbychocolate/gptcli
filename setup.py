#!/usr/bin/env python

from setuptools import find_packages, setup

_version = "0.4.1"

setup(
    name="gptcli",
    version=_version,
    description="A CLI tool for talking to the Openai API.",
    author="Damian Vonapartis",
    url="https://www.python.org/sigs/distutils-sig/",
    packages=find_packages(),
    entry_points={"console_scripts": ["gptcli = gptcli.main:main"]},
)
