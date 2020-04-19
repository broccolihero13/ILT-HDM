from setuptools import setup, find_packages, Command
import io
import os
import sys
from shutil import rmtree

here = os.path.abspath(os.path.dirname(__file__))
description = "This is a CLI tool used to create Historical Data for Live Training enrollments for Bridge LMS. You'll need to have a CSV file with the appropriate format to process these historical enrollment records. Be sure to have the following Python modules (This version also works with Python 3.6 and 3.7)"

try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = description

setup(
    name="ILTHDM",
    version="0.0.1",
    author="broccolihero13",
    description=description,
    author_email="bhalladay@instructure.com",
    python_require=">=3.6.0",
    py_modules=["main"],
    install_requires=["Click","pandas","requests","colorama"],
    entry_points={
        "console_scripts":['ILTHDM=main:main'],
    },
    extra_require={},
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ]
    #url="URL-Goes-Here"
)