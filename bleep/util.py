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

# 2/3 compatibility
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from future.utils import bytes_to_native_str, native_str_to_bytes
from future.builtins import int, bytes

from uuid import UUID

import json
import os

BASE_UUID = UUID("00000000-0000-1000-8000-00805F9B34FB")

CHAR_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'chars.json')))
SERVICE_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'services.json')))
DESC_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'descriptors.json')))

def is_short_uuid(uuid):
    return all(BASE_UUID.fields[x] == uuid.fields[x] for x in range(1, 6))
