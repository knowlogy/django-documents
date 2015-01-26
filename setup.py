#!/usr/bin/env python

from setuptools import setup, find_packages

version = "1.14.0"

if version == '{version}':
    version = 'head'

setup( 
    name='django-documents',
    version= version,
    description='Django documents',
    author='Knowlogy',
    author_email='robert.hofstra@knowlogy.nl',
    url='http://www.knowlogy.nl/python/django-documents',
    packages = find_packages(),
    install_requires=[
        'setuptools',
        'python-dateutil'
      ],
)

