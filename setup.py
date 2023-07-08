#!/usr/bin/env python

import configparser

from setuptools import find_packages, setup


def _get_project_version_number()->str:
    config = configparser.ConfigParser()
    project_version_number = config.read("pyproject.toml", "version")
    project_version_number = project_version_number.strip('"')
    return project_version_number

setup(
    name="gptcli",
    version=_get_project_version_number(),
    description="A CLI tool for talking to the Openai API.",
    author="Damian Vonapartis",
    url="https://www.python.org/sigs/distutils-sig/",
    packages=find_packages(),
    entry_points={"console_scripts": ["gptcli = gptcli.main:main"]},
)
