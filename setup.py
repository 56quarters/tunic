# !/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import print_function

from setuptools import setup, find_packages

import tshfab


DESCRIPTION = 'TSH Labs Fabric Utilities'
AUTHOR = 'TSH Labs'
EMAIL = 'projects@tshlabs.org'
URL = 'http://www.tshlabs.org/'
LICENSE = 'MIT'
CLASSIFIERS = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7"
]


def get_contents(filename):
    """Get the contents of the given file."""
    with open(filename, 'rb') as handle:
        return handle.read().decode('utf-8')


REQUIRES = [
    'fabric'
]

README = get_contents('README.rst')

setup(
    name='tshfab',
    version=tshfab.__version__,
    author=AUTHOR,
    description=DESCRIPTION,
    long_description=README,
    author_email=EMAIL,
    classifiers=CLASSIFIERS,
    license=LICENSE,
    url=URL,
    zip_safe=True,
    install_requires=REQUIRES,
    packages=find_packages())
