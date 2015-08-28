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

setup(
    name = "bleep",
    version = "0.0.1",
    author = "Matthew Else",
    author_email = "matthew.else@arm.com",
    description = "Python BLE API",
    license = "Apache-2.0",
    keywords = "ble",
    url = "about:blank",
    packages = find_packages(),
    package_data = {
        'bleep': ['data/*.json']
    },
    install_requires = [
        'gattlib'
    ],
    dependency_links = [
        'https://github.com/matthewelse/pygattlib/archive/master.zip#egg=pygattlib'
    ]
)
