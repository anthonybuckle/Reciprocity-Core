#!/usr/bin/env python3

from distutils.core import setup

with open('README.txt') as file:
    readme = file.read()

with open('LICENSE') as file:
    license = file.read()

setup(
    name='Reciprocity',
    version='1.0',
    description='Reciprocity Core',
    long_description=readme,
    author='Anthony Buckle',
    url='N/A',
    license=license,
    packages=['recip'],
)