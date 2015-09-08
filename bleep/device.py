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

from threading import Event

from .backend import DiscoveryService
from .requester import Requester

from .util import BLEUUID, UUIDAccessor
from .gatt.service import GATTService

import logging

class BLEDevice(object):
    """Represents a single BLE Device

    Attributes:
        name (str): The name of the BLE Device
        address (str): The MAC Address of the BLE Device
        serviceUUIDs (List[str]): List of advertised service UUIDs
            (there may be more)
        services (UUIDAccessor): Dictionary-like accessor for services
            (always returns a list)
        service (UUIDAccessor): Dictionary-like accessor for services
            (returns a single service or raises a key error)
    """

    def __init__(self, name, address, serviceUUIDs=[], flags=0, appearance=0):
        """Creates a BLE Device Object

        This class does not normally need to be initialised directly,
        since these objects are created in BLEDevice.discoverDevices,
        although it is theoretically possible to create this object
        manually, and then use BLEDevice.connect.

        Args:
            name (str): The name of this object, as advertised by GAP
            address (str): Device MAC Address
            serviceUUIDs (List[UUID]): List of advertised BLE UUIDs
            flags (int): GAP Flags
            appearance (int): GAP Appearance
        """
        self.name = name
        self.flags = flags
        self.address = address
        self.serviceUUIDs = serviceUUIDs
        self.appearance = appearance

        self._services = {}

        self.service = UUIDAccessor(self._services)
        self.services = UUIDAccessor(self._services, True)

        self.requester = Requester(address, False)

        self.requester.indicate(self._on_indication)
        self.requester.notify(self._on_notification)

        self._indication_callbacks = []
        self._notification_callbacks = []

        self.handles = {}

        self.logger = logging.getLogger('bleep.BLEDevice')

    def register_handle(self, handle, attribute):
        """Registers a handle to receive callbacks when notifications or indications occur

        This should only be called within the constructor of GATTAttribute,
        and only one GATTAttribute should be registered per handle.

        Args:
            handle (int): Handle to look out for
            attribute (GATTAttribute): Attribute to notify.
        """
        if handle in self.handles:
            raise KeyError("Handle %i already registered." % handle)

        self.handles[handle] = attribute

    def indicate(self, function):
        """Registers a catch all indication callback

        It's usually better to register a callback to a specific
        GATTAttribute, however if you need all of the callbacks,
        then this is the way to go.

        Args:
            function (Callable[[int, bytes], None]): Callback function
        """
        self._indication_callbacks.append(function)

    def _on_indication(self, handle, data):
        # propagate event to attributes
        for attr_handle, attribute in self.handles.iteritems():
            if handle == attr_handle:
                attribute._on_indication(data)

        # call the catch-alls
        for callback in self._indication_callbacks:
            callback(handle, data)

    def notify(self, function):
        """Registers a catch all notification callback

        It's usually better to register a callback to a specific
        GATTAttribute, however if you need all of the callbacks,
        then this is the way to go.

        Args:
            function (Callable[[int, bytes], None]): Callback function
        """
        # Register a catch-all notify callback. It's usually better to
        # register to a specific GATTAttribute
        self._notification_callbacks.append(function)

    def _on_notification(self, handle, data):
        self.logger.debug("Notification received on handle: %i", handle)
        self.logger.debug("Notification data: %s", data)
        # propagate event to attributes
        for attr_handle, attribute in self.handles.iteritems():
            if handle == attr_handle:
                attribute._on_notification(data)

        # call the catch-alls
        for callback in self._notification_callbacks:
            callback(handle, data)

    def connect(self):
        """Connect to the device"""
        # make sure we don't connect twice
        if self.connected:
            return

        self.requester.connect(True, "random")

        self.logger.debug("Connected.")
        self.logger.debug("Discovering Primary Services")

        # discover services
        primary = self.requester.discover_primary()

        self.logger.debug("Discovered services: %s", primary)

        for service in primary:
            start = service['start']
            end = service['end']

            uuid = BLEUUID(service['uuid'])

            serv = GATTService(self, uuid, start, end)

            # this also needs to be a list of tuples
            # services do not have to be unique.
            if uuid not in self._services:
                self._services[uuid] = [serv]
            else:
                self._services[uuid].append(serv)

        self.logger.debug("Connected Successfully.")

    def disconnect(self):
        """Disconnect from the device"""
        self.requester.disconnect()

    @property
    def connected(self):
        """bool: Whether or not this device is currently connected"""
        return self.requester.is_connected()

    def read_handle(self, handle):
        """Read from a specific handle. (Blocking)

        Args:
            handle (int): The handle to read from
        """
        return self.requester.read_by_handle(handle)[0]

    def _write_handle(self, handle, data, response=True):
        if response:
            return self.requester.write_by_handle(handle, bytes_to_native_str(data))
        else:
            return self.requester.write_without_response_by_handle(handle, bytes_to_native_str(data))

    def write_handle(self, handle, data, response=True):
        """Write to a specific handle. (Blocking)

        Args:
            handle (int): The handle to read from
            data (bytes): Data to be written
            response (bool): Whether or not the data should be written with response
        """
        self.logger.debug("Writing data%s to handle: 0x%x", '' if response else ' without response', handle)

        if isinstance(data, bytes):
            return self._write_handle(handle, data, response)
        else:
            raise NotImplementedError("Unsupported data type")

    def __repr__(self):
        output = "Device Name: %s (%s)"

        return output % (self.name, self.address)

    @staticmethod
    def _discoverDevices(device='hci0', timeout=5, filter=lambda x: True):
        # generate pairs of names and addresses

        discovery = DiscoveryService(device)
        devices = discovery.discover(timeout)

        for address, d in devices.items():
            dev = BLEDevice(d['name'], address, d['uuids'], d['flags'], d['appearance'])

            if filter(dev):
                yield dev

        del discovery

    @staticmethod
    def discoverDevices(device='hci0', timeout=5, filter=lambda x: True):
        """Scans for advertising devices

        Args:
            device (str): The BLE device to scan with (on OS X, this will be irrelevant)
            timeout (int): Time, in seconds, to scan for (it will block for this much time)
            filter (Callable[[BLEDevice], bool]): Function to decide whether to return a certain device

        Returns:
            List[BLEDevice]: A list of unconnected BLEDevice instances, containing data
                collected from advertising.
        """
        return list(BLEDevice._discoverDevices(device, timeout, filter))
