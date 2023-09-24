# bleep: BLE Abstraction Library for Python
#
# Copyright (c) 2015-2023 Matthew Else
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

from bleep.bleep import BleCharacteristic, BleDescriptor
from bleep.util import BLEUUID

class GATTDescriptor:
    """Represents a single BLE Descriptor"""

    def __init__(self, descriptor : BleDescriptor):
        self.descriptor = descriptor
    
    @property
    def uuid(self) -> BLEUUID:
        return BLEUUID(self.descriptor.uuid())
    
    def __repr__(self):
        return str(self.uuid)


class GATTCharacteristic:
    """Represents a single BLE Characteristic"""

    def __init__(self, characteristic: BleCharacteristic):
        self.characteristic = characteristic
    
    @property
    def uuid(self) -> BLEUUID:
        return BLEUUID(self.characteristic.uuid())
    
    def descriptors(self):
        return [GATTDescriptor(descriptor) for descriptor in self.characteristic.descriptors()]

    def __repr__(self):
        return str(self.uuid)
