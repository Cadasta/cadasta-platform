#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
import sys
from setuptools import setup


name = 'cadasta-platform'
package = 'cadasta'
description = 'Cadasta platform.'
url = 'https://github.com/Cadasta/cadasta-platform'
author = 'Cadasta development team'
author_email = 'dev@cadasta.org'
license = 'GNU Affero'

readme_file = os.path.join(os.path.dirname(__file__), 'README.rst')
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
    install_requires=[
        'Django==1.9.4',
        'djangorestframework==3.3.3',
        'psycopg2==2.6.1',
        'djoser==0.4.3',
        'django-allauth==0.25.2',
        'django-cors-headers==1.1.0',
        'django-filter==0.12.0',
        'django-crispy-forms==1.6.0',
        'django-formtools==1.0',
        'django-countries==3.4.1',
        'django-leaflet==0.18.0',
        'django-sass-processor==0.3.4',
        'djangorestframework-gis==0.10.1',
        'jsonschema==2.5.1',
        'rfc3987==1.3.5',
        'drfdocs==0.0.9',
        'django-tutelary==0.1.11',
        'django-audit-log==0.7.0',
        'simplejson==3.8.1',
        'django-widget-tweaks==1.4.1'
    ],
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
