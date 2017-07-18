#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup


def get_pkg_from_git_url(link):
    """
    Given a pip-compatible git-requirement, output a setup.py-compatible
    install requirement.
    'git+https://github.com/user/pkg.git@branch' ->
        'pkg'
    """
    try:
        link = link.split('#')[0].strip()
        end = link.split('/')[-1]
        pkg, version = end.split('@', 1)
        pkg = pkg.split('.git')[0]
        return pkg
    except:
        sys.stderr.write("Failed on link {!r}\n".format(link))
        raise


def get_dependency_from_git_url(link):
    """
    Given a pip-compatible git-requirement, output a setup.py-compatible
    dependency link.
    'git+https://github.com/user/pkg.git@branch' ->
        https://github.com/user/pkg/tarball/branch#egg=pkg'
    """
    try:
        link = link.split('#')[0].strip()
        link = link.replace('git+', '')
        link, branch = link.split('@', 1)
        link = link.replace('.git', '')
        pkg = link.split('/')[-1]
        link = '{}/tarball/{}'.format(link, branch)
        if '#egg=' not in link:
            link = "{}#egg={}".format(link, pkg)
        return link
    except:
        sys.stderr.write("Failed on link {!r}\n".format(link))
        raise


BASE_DIR = os.path.dirname(__file__)

name = 'cadasta-platform'
package = 'cadasta'
description = 'Cadasta platform.'
url = 'https://github.com/Cadasta/cadasta-platform'
author = 'Cadasta development team'
author_email = 'dev@cadasta.org'
license = 'GNU Affero'
req_file = os.path.join(BASE_DIR, 'requirements/common.txt')
raw_requirements = open(req_file).read().splitlines()
requirements = [
    (req if '://' not in req.split('#')[0] else get_pkg_from_git_url(req))
    for req in raw_requirements
]
dependency_links = [
    get_dependency_from_git_url(req)
    for req in raw_requirements if '://' in req.split('#')[0]
]

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
    dependency_links=dependency_links,
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
