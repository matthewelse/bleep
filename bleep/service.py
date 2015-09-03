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

from .characteristic import BLECharacteristic
from .util import is_short_uuid, SERVICE_UUIDS, UUIDAccessor

class BLEService:
    """Represents a single BLE Characteristic

    Attributes:
        characteristic (UUIDAccessor): Allows dictionary-like access to _unique_
            characteristics.
        characteristics (UUIDAccessor): Allows dictionary-like access to all characteristics.
            BLEService.characteristics[UUID] always returns a list of BLECharacteristics
    """

    def __init__(self, device, uuid, start, end):
        """Creates an instance of BLEService.

        Args:
            device (BLEDevice): BLEDevice object of which this is an attribute
            uuid (UUID): The uuid representing this particular attribute
            start (int): The first handle of this service
            end (int): The last handle in this service
        """
        self.device = device
        self.uuid = uuid

        self.start = start
        self.end = end

        self._characteristics = self._get_characteristics()

        self.characteristic = UUIDAccessor(self._characteristics)
        self.characteristics = UUIDAccessor(self._characteristics, True)

    def shortest_uuid(self):
        """Returns a string containing the shortest unique representation of the UUID.

        Returns:
            str: A textual representation of the UUID either in 16-bit form or 128-bit form
        """
        if is_short_uuid(self.uuid):
            return str(self.uuid)[4:8]
        else:
            return str(self.uuid)

    def _discover_characteristics(self):
        characteristics = {}

        for i, char in enumerate(self.device.requester.discover_characteristics(self.start, self.end)):
            handle = char['handle']
            value_handle = char['value_handle']
            uuid = char['uuid']
            properties = char['properties']

            if i == len(characteristics) - 1:
                end_handle = self.end - 1
            else:
                end_handle = characteristics[i + 1]['handle'] - 1

            characteristic = BLECharacteristic(self.device, handle, value_handle, end_handle, UUID(uuid), properties)

            if characteristic.uuid not in characteristics:
                characteristics[characteristic.uuid] = [characteristic]
            else:
                characteristics[characteristic.uuid].append(characteristic)

        return characteristics

    def __repr__(self):
        return self.shortest_uuid() if self.shortest_uuid() not in SERVICE_UUIDS else SERVICE_UUIDS[self.shortest_uuid()]['name']
