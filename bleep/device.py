from gattlib import DiscoveryService, GATTRequester

import json
import os

CHAR_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'chars.json')))
SERVICE_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'services.json')))
DESC_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'descriptors.json')))

class BLEDescriptor:
    def __init__(self, handle, uuid):
        self.handle = handle
        self.uuid = uuid[4:8]

    def __repr__(self):
        return 'descriptor %s' % self.uuid if self.uuid not in DESC_UUIDS else DESC_UUIDS[self.uuid]['name']

class BLECharacteristic:
    def __init__(self, service, handle, value_handle, end_handle, uuid, properties):
        self.short_uuid = uuid[4:8] # TODO: support longer uuids
        self.handle = handle
        self.value_handle = value_handle
        self.end_handle = end_handle
        self.uuid = uuid
        self.properties = properties
        self.service = service

    def read(self):
        # TODO: check whether we can read it at all :p
        return self.service.device.requester.read_by_handle(self.handle)

    def get_descriptors(self):
        for descriptor in self.service.device.requester.discover_descriptors(self.handle, self.end_handle):
            descriptor_object = BLEDescriptor(descriptor['handle'], descriptor['uuid'])

            print(descriptor_object)

    def __repr__(self):
        return CHAR_UUIDS[self.short_uuid]['name']

class BLEService:
    def __init__(self, device, uuid, start, end):
        self.device = device
        self.uuid = uuid

        self.start = start
        self.end = end

        self.characteristics = {x.short_uuid: x for x in self.get_characteristics()}

    def get_characteristics(self):
        print(self)
        print(self.start,self.end)

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

            print(handle, end_handle)

            yield BLECharacteristic(self, handle, value_handle, end_handle, uuid, properties)

    def __repr__(self):
        return SERVICE_UUIDS[self.uuid]['name']

class BLEDevice:
    def __init__(self, name, address, serviceUUIDs=[], flags=0, appearance=0):
        self.name = name
        self.flags = flags
        self.address = address
        self.services = {}
        self.serviceUUIDs = serviceUUIDs
        self.appearance = appearance

        self.requester = GATTRequester(address, False)

    def connected(self):
        return self.requester.is_connected()

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

            uuid = service['uuid'] if len(service['uuid']) == 4 else service['uuid'][4:8]

            serv = BLEService(self, uuid, start, end)

            self.services[uuid] = serv

    def __repr__(self):
        output = "Device Name: %s (%s)"

        return output % (self.name, self.address)

    @staticmethod
    def discoverDevices(device='hci0', timeout=5, filter=lambda x: True):
        # generate pairs of names and addresses

        discovery = DiscoveryService(device)
        devices = discovery.discover(timeout)

        for address, d in devices.items():
            dev = BLEDevice(d['name'], address, d['uuids'], d['flags'], d['appearance'])

            if filter(dev):
                yield dev
