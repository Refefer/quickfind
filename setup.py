# !/usr/bin/env python

from setuptools import setup

setup(name='quickfind',
      version="0.1.2.3",
      description='Fuzzy find for the terminal',
      url="https://github.com/Refefer/quickfind",
      packages=['quickfind', 'quickfind/source'],
      license="LICENSE",
      scripts=['bin/qf'],
      author='Andrew Stanton',
      author_email='Andrew Stanton',
      install_requires=[
          'python-ctags',
          'fsnix==0.2'
      ],
      classifiers=[
       "License :: OSI Approved :: Apache Software License",
       "Programming Language :: Python :: 2.6",
       "Operating System :: OS Independent"
      ])  
