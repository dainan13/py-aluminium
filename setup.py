#!/usr/bin/env python

from distutils.core import setup

setup(name='py-aluminium',
      description = 'a lite easy practical Python library',
      version='0.8.0',
      url='http://py-aluminium.googlecode.com',
      author='Dai,Nan',
      author_email='dainan13@gmail.com',
      license = 'BSD',
      packages=['Al',],
      package_dir={'Al':'src','Al/__furture__':'src/__furture__'}
     )
