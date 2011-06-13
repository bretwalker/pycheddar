import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name = 'pycheddar',
    version = '1.0',
    description = 'Pythonic Python wrapper for CheddarGetter.',
    license = 'BSD',
    url = 'https://github.com/bretwalker/pycheddar',
    
    py_modules =  ['__init__'],
    
    classifiers = (
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python',
    ),
)
