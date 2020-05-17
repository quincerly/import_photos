#! /usr/bin/env python3

from distutils.core import setup

setup(name='ImportPhotos',
    version='2.0',
    description='Simple photo importer',
    author='Dan Rolfe',
      author_email='git@rolfe.email',
      py_modules=['SimpleGUI', 'ProgressBars'],
    scripts=[
        'import_photos',
    ],
)
