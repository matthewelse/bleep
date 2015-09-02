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

from threading import Event

from .backend import DiscoveryService

from .requester import Requester
from .service import BLEService

class BLEDevice:
    def __init__(self, name, address, serviceUUIDs=[], flags=0, appearance=0):
        self.name = name
        self.flags = flags
        self.address = address
        self.services = []
        self.serviceUUIDs = serviceUUIDs
        self.appearance = appearance

        self.requester = Requester(address, False)

        self.notify_callback = None
        self.notification_event = Event()

        self.requester.set_notification_event(self.notification_event)
        self.requester.notification_callback = self._on_notification

        self.notification_handle = None
        self.notification_data = None

    def notify(self, function):
        self.notify_callback = function

    def _on_notification(self, handle, data):
        # TODO: propagate the notification to the necessary handle
        self.notification_data = data
        self.notification_handle = handle

        self.notification_event.set()

        if self.notify_callback is not None:
            self.notify_callback(handle, data)

    def connected(self):
        return self.requester.is_connected()

    def wait_notification(self, handle = 0):
        self.notification_event.wait()
        self.notification_event.clear()

        return self.notification_data

    def connect(self):
        # make sure we don't connect twice
        if self.connected():
            return

        self.requester.connect(True, "random")

        # discover services
        primary = self.requester.discover_primary()

        for service in primary:
            start = service['start']
            end = service['end']

            uuid = service['uuid']

            serv = BLEService(self, uuid, start, end)

            # this also needs to be a list of tuples
            # services do not have to be unique.
            self.services.append(serv)

    def __repr__(self):
        output = "Device Name: %s (%s)"

        return output % (self.name, self.address)

    def read_handle(self, handle):
        return self.requester.read_by_handle(handle)[0]


    def _write_handle(self, handle, data):
        # data has to be a bytes
        #print("Writing data %r to handle: %i" % (data, handle))
        return self.requester.write_by_handle(handle, bytes_to_native_str(data))

    def write_handle(self, handle, data):
        if isinstance(data, int):
            return self._write_handle(handle, bytes([data]))
        elif isinstance(data, list):
            return self._write_handle(handle, bytes(data))
        elif isinstance(data, bytes):
            return self._write_handle(handle, data)
        else:
            raise NotImplementedError("Unsupported data type")

    def _write_handle_without_response(self, handle, data):
        # data has to be a bytes
        print("Writing data %r to handle (without response): %i" % (data, handle))
        self.requester.write_without_response_by_handle(handle, bytes_to_native_str(data))

    def write_handle_without_response(self, handle, data):
        if isinstance(data, int):
            self._write_handle_without_response(handle, bytes([data]))
        elif isinstance(data, list):
            self._write_handle_without_response(handle, bytes(data))
        elif isinstance(data, bytes):
            self._write_handle_without_response(handle, data)
        else:
            raise NotImplementedError("Unsupported data type")

    @staticmethod
    def _discoverDevices(device='hci0', timeout=5, filter=lambda x: True):
        # generate pairs of names and addresses

        discovery = DiscoveryService(device)
        devices = discovery.discover(timeout)

        for address, d in devices.items():
            dev = BLEDevice(d['name'], address, d['uuids'], d['flags'], d['appearance'])

            if filter(dev):
                yield dev


    @staticmethod
    def discoverDevices(device='hci0', timeout=5, filter=lambda x: True):
        return list(BLEDevice._discoverDevices(device, timeout, filter))
