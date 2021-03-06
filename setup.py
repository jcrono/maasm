#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Javier Peralta
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from setuptools import setup, find_packages


def read(filename):
    """
    Read a file relative to setup.py location.
    """
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, filename)) as fd:
        return fd.read()


def find_version(filename):
    """
    Find package version in file.
    """
    import re
    content = read(filename)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


def find_requirements(filename):
    """
    Find requirements in file.
    """
    import string
    content = read(filename)
    requirements = []
    for line in content.splitlines():
        line = line.strip()
        if line and line[:1] in string.ascii_letters:
            requirements.append(line)
    return requirements


setup(
    name='maasm',
    version='2.1.0',
    py_modules=['maasm'],
    entry_points ='''
    [console_scripts]
    maasm = maasm:main
    ''',

    # Dependencies
    install_requires=find_requirements('requirements.txt'),

    # Metadata
    author='Javier Peralta',
    author_email='javinachop@gmail.com',
    description=(
        'Assembler for MiniAlu'
    ),
    #long_description=read('README.rst'),
    url='https://maasm.readthedocs.org/',
    keywords='maasm',

    classifiers=[
        'Programming Language :: Python :: 3.4',
    ]
)
