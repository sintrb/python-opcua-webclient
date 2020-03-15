# -*- coding: utf-8 -*-
import os, io
from setuptools import setup

from opcuawebclient.info import __version__

here = os.path.abspath(os.path.dirname(__file__))
README = io.open(os.path.join(here, 'README.md'), encoding='UTF-8').read()
CHANGES = io.open(os.path.join(here, 'CHANGES.md'), encoding='UTF-8').read()
setup(name='opcua-webclient',
      version=__version__,
      description='A OPCUA web client, implemented by Python.',
      long_description=README + '\n\n\n' + CHANGES,
      long_description_content_type="text/markdown",
      url='https://github.com/sintrb/python-opcua-webclient',
      classifiers=[
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
      ],
      keywords='OPC OPCUA WEB CLIENT',
      author='sintrb',
      author_email='sintrb@gmail.com',
      license='Apache',
      packages=['opcuawebclient'],
      scripts=['opcuawebclient/opcua-webclient.bat', 'opcuawebclient/opcua-webclient'],
      include_package_data=True,
      install_requires=['tornado', 'freeopcua'],
      zip_safe=False)
