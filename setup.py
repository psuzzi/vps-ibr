#!/usr/bin/env python3
from setuptools import setup, find_packages

# This file is kept for backward compatibility
# All configuration is in pyproject.toml
setup(
    name="vps-ibr",
    packages=find_packages(),
    package_data={"vps_ibr": ["scripts/*.sh"]},
    include_package_data=True,
)
