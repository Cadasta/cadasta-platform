#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup

BASE_DIR = os.path.dirname(__file__)

name = 'cadasta-platform'
package = 'cadasta'
description = 'Cadasta platform.'
url = 'https://github.com/Cadasta/cadasta-platform'
author = 'Cadasta development team'
author_email = 'dev@cadasta.org'
license = 'GNU Affero'
req_file = os.path.join(BASE_DIR, 'requirements/common.txt')
requirements = open(req_file).read().splitlines()

readme_file = os.path.join(BASE_DIR, 'README.rst')
with open(readme_file, 'r') as f:
    long_description = f.readline().strip()


def get_version(package):
    return '0.0.1'


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


version = get_version(package)


setup(
    name=name,
    version=version,
    url=url,
    license=license,
    description=description,
    long_description=long_description,
    author=author,
    author_email=author_email,
    packages=get_packages(package),
    package_data=get_package_data(package),
    install_requires=requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
