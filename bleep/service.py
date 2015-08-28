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

from .characteristic import BLECharacteristic
from .util import is_short_uuid, SERVICE_UUIDS

class BLEService:
    def __init__(self, device, uuid, start, end):
        self.device = device
        self.uuid = UUID(uuid)

        self.start = start
        self.end = end

        # This has to be a list rather than a dictionary
        # because there can be more than one characteristic with
        # each uuid
        self.characteristics = list(self._get_characteristics())

    def shortest_uuid(self):
        if is_short_uuid(self.uuid):
            return str(self.uuid)[4:8]
        else:
            return str(self.uuid)

    def _get_characteristics(self):
        characteristics = self.device.requester.discover_characteristics(self.start, self.end)

        for i, char in enumerate(characteristics):
            handle = char['handle']
            value_handle = char['value_handle']
            uuid = char['uuid']
            properties = char['properties']

            if i == len(characteristics) - 1:
                end_handle = self.end - 1
            else:
                end_handle = characteristics[i + 1]['handle'] - 1

            yield BLECharacteristic(self.device, handle, value_handle, end_handle, uuid, properties)

    def get_characteristics(self, uuid):
        return [c for c in self.characteristics if c.uuid == uuid]

    def get_characteristic(self, uuid):
        # TODO: make this neater, by using a dictionary of lists
        matching = self.get_characteristics(uuid)

        if len(matching) == 0:
            raise RuntimeError("characteristic not found.")
        elif len(matching) > 1:
            # technically, there could be too few also :)
            raise RuntimeError("too many characteristics with this uuid")

        return matching[0]

    def __repr__(self):
        return self.shortest_uuid() if self.shortest_uuid() not in SERVICE_UUIDS else SERVICE_UUIDS[self.shortest_uuid()]['name']