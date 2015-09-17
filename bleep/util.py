# bleep: BLE Abstraction Library for Python
#
# Copyright (c) 2015 Matthew Else
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# 2/3 compatibility
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from future.utils import bytes_to_native_str, native_str_to_bytes
from future.builtins import int, bytes

from uuid import UUID

from copy import copy

import json
import os

BASE_UUID = UUID("00000000-0000-1000-8000-00805F9B34FB")

def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in later dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

class BLEUUID(object):
    """Representation of BLE UUIDs, with useful tools"""
    BASE_UUID_BYTES = bytearray(BASE_UUID.bytes)

    CHAR_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'chars.json')))
    SERVICE_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'services.json')))
    DESC_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'descriptors.json')))

    UUID_LOOKUP = merge_dicts(CHAR_UUIDS, SERVICE_UUIDS, DESC_UUIDS)

    def __init__(self, uuid):
        self._uuid = copy(BLEUUID.BASE_UUID_BYTES)

        if isinstance(uuid, UUID):
            # Assume that the UUID is correct
            self._uuid = bytearray(uuid.bytes)
        elif type(uuid) == type(bytes()):
            self._uuid[2:4] = bytearray(bytes_to_native_str(uuid))
        elif type(uuid) == type(str()):
            if len(uuid) == 4:
                # 16-bit UUID
                part = int(uuid, 16).to_bytes(2, 'little')
                self._uuid[2:4] = bytearray(part)
            elif len(uuid) == 8:
                # 32-bit UUID
                part = int(uuid, 16).to_bytes(4, 'little')
                self._uuid[0:4] = bytearray(part)
            elif len(uuid) == 36:
                # 128-bit UUID
                self._uuid = bytearray(UUID(uuid).bytes)
            else:
                raise ValueError("Invalid UUID")
        elif isinstance(uuid, int):
            if uuid < 65536:
                # 16-bit UUID
                part = int(uuid).to_bytes(2, 'little')
                self._uuid[2:4] = bytearray(part)
            elif uuid < 2**32:
                # 32-bit UUID
                part = int(uuid).to_bytes(4, 'little')
                self._uuid[0:4] = bytearray(part)
            else:
                raise ValueError("Invalid UUID")
        else:
            raise ValueError("Invalid UUID (type error)")

    def full_uuid_str(self):
        """Return a string representation of the full UUID (128-bit)"""
        print(self._uuid)
        return str(UUID(bytes=str(self._uuid)))

    def canonical_str(self):
        """Return the shortest specific string representation of the UUID"""
        if self._uuid[4:] == BLEUUID.BASE_UUID_BYTES[4:]:
            # At least a 32-bit UUID
            if self._uuid[:2] == BLEUUID.BASE_UUID_BYTES[:2]:
                # 16-bit UUID
                return self.full_uuid_str()[4:8]
            else:
                return self.full_uuid_str()[:8]
        else:
            return self.full_uuid_str()

    def __str__(self):
        c_str = self.canonical_str()
        return c_str if c_str not in BLEUUID.UUID_LOOKUP else BLEUUID.UUID_LOOKUP[c_str]['name']

    def __repr__(self):
        return "BLEUUID('%s')" % self.full_uuid_str()

    def __hash__(self):
        return hash(bytes(self._uuid))

    def __eq__(x, y):
        if not isinstance(y, BLEUUID):
            y = BLEUUID(y)

        return bytes(x._uuid) == bytes(y._uuid)

    def __ne__(x, y):
        return not BLEUUID.__eq__(x, y)


class UUIDAccessor(object):
    def __init__(self, data, all = False):
        self.data = data
        self.all = all

    def __iter__(self):
        for obj in self.data.itervalues():
            for item in obj:
                yield item

    def __getitem__(self, uuid):
        if not isinstance(uuid, BLEUUID):
            uuid = BLEUUID(uuid)

        if self.all:
            return self.data[uuid]

        if len(self.data[uuid]) == 1:
            return self.data[uuid][0]
        else:
            raise KeyError("More than one instance of %s" % uuid)
