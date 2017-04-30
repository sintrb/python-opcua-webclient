# -*- coding: utf-8 -*-
import os, io
from setuptools import setup

from opcuawebclient.info import __version__
here = os.path.abspath(os.path.dirname(__file__))
README = io.open(os.path.join(here, 'README.rst'), encoding='UTF-8').read()
CHANGES = io.open(os.path.join(here, 'CHANGES.rst'), encoding='UTF-8').read()
setup(name='opcua-webclient',
      version=__version__,
      description='A OPCUA web client, implemented by Python.',
      long_description=README + '\n\n\n' + CHANGES,
      url='https://github.com/sintrb/python-opcua-webclient',
      classifiers=[
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
      ],
      keywords='OPC OPCUA WEB CLIENT',
      author='sintrb',
      author_email='sintrb@gmail.com',
      license='Apache',
      packages=['opcuawebclient'],
      scripts=['opcuawebclient/opcua-webclient.bat'] if os.name == 'nt' else ['opcuawebclient/opcua-webclient'],
      include_package_data=True,
      install_requires=['tornado', 'freeopcua'],
      zip_safe=False)
