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

from .characteristic import GATTCharacteristic
from ..util import BLEUUID, UUIDAccessor

import logging

class GATTService(object):
    """Represents a single BLE Characteristic

    Attributes:
        characteristic (UUIDAccessor): Allows dictionary-like access to _unique_
            characteristics.
        characteristics (UUIDAccessor): Allows dictionary-like access to all characteristics.
            GATTService.characteristics[UUID] always returns a list of GATTCharacteristics
    """

    def __init__(self, device, uuid, start, end):
        """Creates an instance of GATTService.

        Args:
            device (BLEDevice): BLEDevice object of which this is an attribute
            uuid (BLEUUID): The uuid representing this particular attribute
            start (int): The first handle of this service
            end (int): The last handle in this service
        """
        self.logger = logging.getLogger('bleep.GATTService')

        self.device = device
        self.uuid = uuid

        self.start = start
        self.end = end

        self._characteristics = self._discover_characteristics()

        self.characteristic = UUIDAccessor(self._characteristics)
        self.characteristics = UUIDAccessor(self._characteristics, True)

    def _discover_characteristics(self):
        characteristics = {}

        self.logger.debug("Discovering Characteristics")
        raw_chars = self.device.requester.discover_characteristics(self.start, self.end)
        self.logger.debug("Discovered: %s", raw_chars)

        for i, char in enumerate(raw_chars):
            handle = char['handle']
            value_handle = char['value_handle']
            uuid = char['uuid']
            properties = char['properties']

            if i == len(raw_chars) - 1:
                end_handle = self.end - 1
            else:
                end_handle = raw_chars[i + 1]['handle'] - 1

            characteristic = GATTCharacteristic(self.device, handle, value_handle, end_handle, BLEUUID(uuid), properties)

            if characteristic.uuid not in characteristics:
                characteristics[characteristic.uuid] = [characteristic]
            else:
                characteristics[characteristic.uuid].append(characteristic)

        return characteristics

    def __repr__(self):
        return str(self.uuid)
