# -*- coding: utf-8 -*-
#

from __future__ import print_function
import codecs

from setuptools import setup, find_packages

import tunic


DESCRIPTION = 'Deployment related Fabric utilities'
AUTHOR = 'TSH Labs'
EMAIL = 'projects@tshlabs.org'
URL = 'https://github.com/tshlabs/tunic'
LICENSE = 'MIT'
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Topic :: System :: Installation/Setup"
]


def get_contents(filename):
    with codecs.open(filename, 'rb', encoding='utf-8') as handle:
        return handle.read()


REQUIRES = [
    'fabric'
]

README = get_contents('README.rst')

setup(
    name='tunic',
    version=tunic.__version__,
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
