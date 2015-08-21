from gattlib import DiscoveryService, GATTRequester

import json
import os

from uuid import UUID

BASE_UUID = UUID("00000000-0000-1000-8000-00805F9B34FB")

CHAR_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'chars.json')))
SERVICE_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'services.json')))
DESC_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'descriptors.json')))

def is_short_uuid(uuid):
    return all(BASE_UUID.fields[x] == uuid.fields[x] for x in range(1, 6))

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
        self.descriptors = [(x.shortest_uuid(), x) for x in self.get_descriptors()]

    def read(self):
        # TODO: check whether we can read it at all :p
        return self.device.requester.read_by_handle(self.value_handle)

    def shortest_uuid(self):
        if is_short_uuid(self.uuid):
            return str(self.uuid)[4:8]
        else:
            return str(self.uuid)

    def get_descriptors(self):
        if self.value_handle + 1 > self.end_handle:
            return
            yield

        for descriptor in self.device.requester.discover_descriptors(self.value_handle + 1, self.end_handle):
            desc = BLEDescriptor(self.device, descriptor['handle'], descriptor['uuid'])
            yield desc

    def __repr__(self):
        return self.shortest_uuid() if self.shortest_uuid() not in CHAR_UUIDS else CHAR_UUIDS[self.shortest_uuid()]['name']

class BLEService:
    def __init__(self, device, uuid, start, end):
        self.device = device
        self.uuid = UUID(uuid)

        self.start = start
        self.end = end

        # This has to be a list of tuples rather than a dictionary
        # because there can be more than one characteristic with
        # each uuid
        self.characteristics = [(x.shortest_uuid(), x) for x in self.get_characteristics()]

    def shortest_uuid(self):
        if is_short_uuid(self.uuid):
            return str(self.uuid)[4:8]
        else:
            return str(self.uuid)

    def get_characteristics(self):
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

    def __repr__(self):
        return self.shortest_uuid() if self.shortest_uuid() not in SERVICE_UUIDS else SERVICE_UUIDS[self.shortest_uuid()]['name']

class BLEDevice:
    def __init__(self, name, address, serviceUUIDs=[], flags=0, appearance=0):
        self.name = name
        self.flags = flags
        self.address = address
        self.services = []
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

            uuid = service['uuid']

            serv = BLEService(self, uuid, start, end)

            # this also needs to be a list of tuples
            # services do not have to be unique.
            self.services.append((uuid, serv))

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


    @staticmethod
    def discoverDevices(device='hci0', timeout=5, filter=lambda x: True):
        return list(BLEDevice._discoverDevices(device, timeout, filter))
