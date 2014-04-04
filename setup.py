# !/usr/bin/env python

from setuptools import setup

setup(name='quickfind',
      version="0.1.4.1",
      description='Fuzzy find for the terminal',
      url="https://github.com/Refefer/quickfind",
      packages=['quickfind', 'quickfind/source'],
      license="LICENSE",
      scripts=['qf'],
      author='Andrew Stanton',
      author_email='Andrew Stanton',
      extras_require={
          "ctags": 'python-ctags',
          "fsnix": 'fsnix==0.2'
      },
      classifiers=[
       "License :: OSI Approved :: Apache Software License",
       "Programming Language :: Python :: 2.7",
       "Programming Language :: Python :: 3.2",
       "Operating System :: OS Independent"
      ])  
