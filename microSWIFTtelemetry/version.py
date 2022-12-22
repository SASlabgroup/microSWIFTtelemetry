from __future__ import absolute_import, division, print_function
from os.path import join as pjoin

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 0
_version_minor = 2
_version_micro = 3  # use '' for first of series, number for 1 and above
# _version_extra = 'dev'
_version_extra = ''  #TODO: Uncomment this for full releases

# Construct full version string from these.
_ver = [_version_major, _version_minor]
if _version_micro:
    _ver.append(_version_micro)
if _version_extra:
    _ver.append(_version_extra)

__version__ = '.'.join(map(str, _ver))

CLASSIFIERS = [
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Topic :: Scientific/Engineering"
]

# Description should be a one-liner:
description = "microSWIFTtelemetry: Python-based functionality for pulling telemetry from the microSWIFT wave buoy."
# Long description will go up on the pypi page
long_description = """

microSWIFTtelemetry
===================
Python-based functionality for pulling telemetry from the microSWIFT wave buoy.

.. _README: https://github.com/SASlabgroup/microSWIFTtelemetry/blob/main/README.md

License
=======
``microSWIFTtelemetry`` is licensed under the terms of the MIT license. See the file
"LICENSE" for information on the history of this software, terms & conditions
for usage, and a DISCLAIMER OF ALL WARRANTIES.

All trademarks referenced herein are property of their respective holders.

Copyright (c) 2022--, Jacob Davis, University of Washington
"""

NAME = "microSWIFTtelemetry"
MAINTAINER = "Jacob Davis"
MAINTAINER_EMAIL = "davisjr@uw.edu"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
LONG_DESCRIPTION_CONTENT_TYPE = "text/markdown"
URL = "https://github.com/SASlabgroup/microSWIFTtelemetry"
DOWNLOAD_URL = ""
LICENSE = "MIT"
AUTHOR = "Jacob Davis"
AUTHOR_EMAIL = "davisjr@uw.edu"
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
VERSION = __version__
PACKAGE_DATA = {'microSWIFTtelemetry': [pjoin('data', '*')]} # or {'': ['data/x', 'data/x']}
REQUIRES = [
    "matplotlib",
    "numpy",
    "pandas",
    "xarray",
]
PYTHON_REQUIRES = ">= 3.7"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

