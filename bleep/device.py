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

import asyncio
import logging
from typing import Optional
from bleep.gatt.characteristic import GATTCharacteristic

from bleep.gatt.service import GATTService

from .bleep import BleAdapter, BleCharacteristic, BlePeripheral, BlePeripheralProperties


class BLEDevice(object):
    """Represents a single BLE Device"""

    def __init__(
        self, peripheral: BlePeripheral, properties: Optional[BlePeripheralProperties]
    ):
        """Creates a BLE Device Object

        This class does not normally need to be initialised directly,
        since these objects are created in BLEDevice.discoverDevices,
        although it is theoretically possible to create this object
        manually, and then use BLEDevice.connect.
        """

        self.peripheral = peripheral
        self.properties = properties
        self.logger = logging.getLogger("bleep.BLEDevice")

    @property
    def address(self):
        """Note that this is hidden by CoreBluetooth, so is unavailable on MacOS."""

        return self.peripheral.address()

    async def services(self):
        services = await self.peripheral.services()

        return [ GATTService(service) for service in services ]

    @property
    def name(self):
        if self.properties is None:
            return None
        return self.properties.local_name()

    async def on_notification(self, f):
        await self.peripheral.register_notification_callback(f)

    async def connect(self):
        """Connect to the device"""

        if await self.peripheral.is_connected():
            return

        await self.peripheral.connect()

    async def disconnect(self):
        """Disconnect from the device"""

        if await self.peripheral.is_connected():
            await self.peripheral.disconnect()

    async def read(self, characteristic : GATTCharacteristic):
        return await self.peripheral.read(characteristic.characteristic)

    async def write(
        self, characteristic: GATTCharacteristic, data: bytes, response: bool = True
    ):
        self.logger.debug(
            "Writing data%s to characteristic: %r",
            "" if response else " without response",
            characteristic,
        )

        await self.peripheral.write(characteristic.characteristic, data, response)
    
    async def subscribe(self, characteristic : GATTCharacteristic):
        await self.peripheral.subscribe(characteristic.characteristic)

    def __repr__(self):
        return f"Device Name: {self.name} ({self.address})"

    @staticmethod
    async def _discoverDevices(adapter: BleAdapter, timeout=5, filter=lambda x: True):
        await adapter.start_scan()
        await asyncio.sleep(timeout)

        for device in await adapter.peripherals():
            properties = await device.properties()

            dev = BLEDevice(device, properties)

            if filter(dev):
                yield dev

    @staticmethod
    async def discoverDevices(adapter: BleAdapter, timeout=5, filter=lambda x: True):
        """Scans for advertising devices"""

        return [x async for x in BLEDevice._discoverDevices(adapter, timeout, filter)]
