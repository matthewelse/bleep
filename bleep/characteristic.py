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

from .util import is_short_uuid, DESC_UUIDS, CHAR_UUIDS

class BLEDescriptor:
    def __init__(self, device, handle, uuid):
        self.device = device
        self.handle = handle
        self.uuid = UUID(uuid)

    def shortest_uuid(self):
        if is_short_uuid(self.uuid):
            return str(self.uuid)[4:8]
        else:
            return str(self.uuid)

    def read(self):
        return self.device.read_handle(self.handle)

    def write(self, data):
        return self.device.write_handle(self.handle, data)

    def write_without_response(self, data):
        self.device.write_handle_without_response(self.handle, data)

    def __repr__(self):
        return '%s' % self.shortest_uuid() if self.shortest_uuid() not in DESC_UUIDS else DESC_UUIDS[self.shortest_uuid()]['name']

class BLECharacteristic:
    def __init__(self, device, handle, value_handle, end_handle, uuid, properties):
        self.handle = handle
        self.value_handle = value_handle
        self.end_handle = end_handle
        self.uuid = UUID(uuid)
        self.properties = properties
        self.device = device

        # This has to be a list of tuples, since (I think) you
        # could theoretically have more than one of the same uuid
        self.descriptors = list(self._get_descriptors())

    def read(self):
        return self.device.read_handle(self.value_handle)

    def write(self, data):
        return self.device.write_handle(self.value_handle, data)

    def write_without_response(self, data):
        self.device.write_handle_without_response(self.value_handle, data)

    def shortest_uuid(self):
        if is_short_uuid(self.uuid):
            return str(self.uuid)[4:8]
        else:
            return str(self.uuid)

    def get_descriptors(self, uuid):
        return [c for c in self.descriptors if c.uuid == uuid]

    def get_descriptor(self, uuid):
        # TODO: make this neater, by using a dictionary of lists
        matching = self.get_descriptors(uuid)

        if len(matching) == 0:
            raise RuntimeError("descriptor not found.")
        elif len(matching) > 1:
            # technically, there could be too few also :)
            raise RuntimeError("too many descriptors with this uuid")

        return matching[0]

    def _get_descriptors(self):
        if self.value_handle + 1 > self.end_handle:
            return
            yield

        try:
            for descriptor in self.device.requester.discover_descriptors(self.value_handle + 1, self.end_handle):
                desc = BLEDescriptor(self.device, descriptor['handle'], descriptor['uuid'])
                yield desc
        except RuntimeError:
            return
            yield

    def __repr__(self):
        return self.shortest_uuid() if self.shortest_uuid() not in CHAR_UUIDS else CHAR_UUIDS[self.shortest_uuid()]['name']
