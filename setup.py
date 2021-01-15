#!/usr/bin/env python

from setuptools import setup

with open('README.md') as fh:
    long_description = fh.read()

setup(
    name='simpleclient',
    packages=['simpleclient'],
    version='0.0.2',
    license='MIT',
    author='nggit',
    author_email='contact@anggit.com',
    description='Python Simple HTTP Client',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nggit/simpleclient',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: System :: Networking',
    ],
)
