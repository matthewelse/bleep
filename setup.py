"""
 bleep: BLE Abstraction Library for Python

 Copyright (c) 2015 Matthew Else

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from setuptools import setup, find_packages

import sys
import os

# Utility function to cat in a file (used for the README)
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def check_system(systems, message):
    import sys
    if sys.platform in systems:
        return
    print(message)
    sys.exit(1)

OTHER_OS_MESSAGE = """
        *****************************************************
        *      bleep only works on Mac OS X and Linux       *
        *                                                   *
        * if you're using Windows, then raise an issue here *
        * https://github.com/matthewelse/bleep suggesting   *
        * that I add Windows support (if there isn't one    *
        *                      already)                     *
        *****************************************************
    """

# check that this is being installed on Mac OS X.
check_system(['darwin', 'linux2', 'linux'], OTHER_OS_MESSAGE)

if sys.platform == 'darwin':
    platform_dependencies = ['pygattosx']
    platform_links = ['https://github.com/matthewelse/pygattosx/archive/master.zip#egg=pygattosx']
elif 'linux' in sys.platform:
    platform_dependencies = ['gattlib']
    platform_links = ['https://github.com/matthewelse/pygattlib/archive/master.zip#egg=gattlib']

setup(
    name = "bleep",
    use_scm_version={
        'local_scheme': 'dirty-tag',
        'write_to': 'bleep/_version.py'
    },
    setup_requires=['setuptools_scm!=1.5.3,!=1.5.4'],
    author = "Matthew Else",
    author_email = "matthew.else@arm.com",
    description = read('README.md'),
    license = "Apache-2.0",
    keywords = "ble",
    url = "https://github.com/matthewelse/bleep",
    packages = find_packages(),
    package_data = {
        'bleep': ['data/*.json']
    },
    install_requires = [
        'future'
    ] + platform_dependencies,
    dependency_links = platform_links
)
