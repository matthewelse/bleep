# 2/3 compatibility
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from future.utils import bytes_to_native_str, native_str_to_bytes
from future.builtins import int, bytes

from gattlib import DiscoveryService, GATTRequester

import json
import os

from uuid import UUID
from math import ceil
from threading import Event

BASE_UUID = UUID("00000000-0000-1000-8000-00805F9B34FB")

CHAR_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'chars.json')))
SERVICE_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'services.json')))
DESC_UUIDS = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'descriptors.json')))

def is_short_uuid(uuid):
    return all(BASE_UUID.fields[x] == uuid.fields[x] for x in range(1, 6))

class Requester(GATTRequester):
    def __init__(self, *args):
        GATTRequester.__init__(self, *args)

        self.notification_callback = None
        self.notification_event = None

    def set_notification_event(self, event):
        self.notification_event = event

    def on_notification(self, handle, data):
        data = bytes([ord(x) for x in data[3:]])

        if self.notification_callback is not None:
            self.notification_callback(handle, data)

        self.notification_event.set()

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
        # TODO: check whether we can read it at all :p
        return self.device.read_handle(self.value_handle)

    def write(self, data):
        return self.device.write_handle(self.value_handle, data)

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

def parse_bytes(data, pattern):
    # TODO: check that the pattern adds up to less than the length of the data
    output = []
    total = 0
    for char in pattern:
        n_bytes = int(char, 16)
        output.append(int.from_bytes(data[total:total+n_bytes], 'little'))
        total += n_bytes
    return tuple(output + [data[total:]])

# Client for BTS
class BlockTransferService:
    # 0001 + base uuid and 0002 + base uuid, respectively.
    WRITE_CHARACTERISTIC_UUID = UUID("00000001-0000-1000-8000-00805F9B34FB")
    READ_CHARACTERISTIC_UUID  = UUID("00000002-0000-1000-8000-00805F9B34FB")

    PACKET_TYPES = {
        'WRITE': {
            'SETUP':        0x00,
            'REQUEST':      0x01,
            'PAYLOAD_MORE': 0x02,
            'PAYLOAD_LAST': 0x03,
            'DIRECT':       0x04
        },
        'READ': {
            'SETUP':        0x05,
            'REQUEST':      0x06,
            'PAYLOAD_MORE': 0x07,
            'PAYLOAD_LAST': 0x08,
            'DIRECT':       0x09
        },
        'NOTIFY':           0x0A
    }

    FRAGMENT_SIZE = 20

    CLIENT_CHARACTERISTIC_DESCRIPTOR = UUID("00002902-0000-1000-8000-00805F9B34FB")

    def __init__(self, service):
        self.service = service

        # Make sure we have the necessary characteristics
        if not any(characteristic.uuid == BlockTransferService.READ_CHARACTERISTIC_UUID for characteristic in self.service.characteristics):
            raise RuntimeError("BlockTransferService must have a read characteristic")
        if not any(characteristic.uuid == BlockTransferService.WRITE_CHARACTERISTIC_UUID for characteristic in self.service.characteristics):
            raise RuntimeError("BlockTransferService must have a write characteristic")

        # you to me
        self.write_characteristic = service.get_characteristic(BlockTransferService.WRITE_CHARACTERISTIC_UUID)

        # me to you
        self.read_characteristic = service.get_characteristic(BlockTransferService.READ_CHARACTERISTIC_UUID)

        # enable notifications
        self.ccc_descriptor = self.read_characteristic.get_descriptor(BlockTransferService.CLIENT_CHARACTERISTIC_DESCRIPTOR)
        print(self.ccc_descriptor.read())
        self.ccc_descriptor.write(1)

    def write(self, block, offset=0):
        # TODO: deal with direct transfer
        fragments = ceil(len(block) / self.FRAGMENT_SIZE)
        packet = self._write_setup_packet(len(block), offset, fragments)

        print('Writing SETUP Packet: %r' % packet)

        self.write_characteristic.write(packet)

        # wait for request packet.
        notification_data = self.service.device.wait_notification()

        if notification_data[0] >> 4 == BlockTransferService.PACKET_TYPES['WRITE']['REQUEST']:
            start_index, number_of_fragments = self._parse_request_packet(notification_data)

        print('Received REQUEST Packet')

        current_packet = start_index

        while current_packet <= 0xffff:
            # send some data :)
            packet = self._generate_fragment(block, BlockTransferService.FRAGMENT_SIZE, current_packet, fragments)
            print([x for x in packet])
            self.write_characteristic.write(packet)

            # wait for it to be sent
            time.sleep(0.2)

            current_packet += 1

            if number_of_fragments <= current_packet - start_index:
                # ask for some more data
                notification_data = self.service.device.wait_notification()

                if notification_data[0] >> 4 == BlockTransferService.PACKET_TYPES['WRITE']['REQUEST']:
                    start_index, number_of_fragments = self._parse_request_packet(notification_data)

                current_packet = start_index
                print(start_index, number_of_fragments)



    def read(self):
        # start by reading from the read characteristic
        packet = self.read_characteristic.read()

        if packet[0] >> 4 == BlockTransferService.PACKET_TYPES['READ']['SETUP']:
            # yay block transfer
            # send a request packet
            _, length, fragments, _ = parse_bytes(packet, '133')

            # TODO: re-request lost packets
            packets = [None for _ in range()]
            packet = _generate_request(0, fragments)

            self.write_characteristic.write(packet)

            fragment = self.read_characteristic.read()
            t, partial_fragment_number, payload = parse_bytes(fragment, '12')

            fragment_number = partial_fragment_number << 4 + (t & 0x0f)
            fragment_type = t >> 4

            packets[fragment_number] = payload

            while fragment_type != BlockTransferService.PACKET_TYPES['READ']['PAYLOAD_LAST']:
                fragment = self.read_characteristic.read()
                t, partial_fragment_number, payload = parse_bytes(fragment, '12')

                fragment_number = partial_fragment_number << 4 + (t & 0x0f)
                fragment_type = t >> 4

                packets[fragment_number] = payload

            print(packets)

            # send a 0xffff packet
            packet = _generate_request(0xffff, 1)
            self.write_characteristic.write(packet)

            data = packets

        elif packet[0] >> 4 == BlockTransferService.PACKET_TYPES['READ']['DIRECT']:
            # this one is really easy
            _, data = parse_bytes(packet, '1')

        return data

    def _generate_direct(self, data, offset):
        return int((BlockTransferService.PACKET_TYPES['WRITE']['DIRECT'] << 4) | (offset & 0x0f)).to_bytes(1, 'little') + \
               int(offset >> 4).to_bytes(2, 'little') + \
               data

    def _generate_fragment(self, data, fragment_size, fragment_number, total_fragments):
        offset = fragment_number * fragment_size
        # make sure we don't go too far
        size = fragment_size if fragment_size + offset <= len(data) else len(data) - offset
        fragment = data[offset:offset + size]

        if total_fragments == 1:
            # we're the last one :(
            packet_type = BlockTransferService.PACKET_TYPES['WRITE']['PAYLOAD_LAST']
        else:
            packet_type = BlockTransferService.PACKET_TYPES['WRITE']['PAYLOAD_MORE']

        return int((packet_type << 4) | (fragment_number & 0x0f)).to_bytes(1, 'little') + \
               int(fragment_number >> 4).to_bytes(2, 'little') + \
               fragment

    def _parse_request_packet(self, packet):
        # we have the type already
        _, start_index, number_of_fragments, _ = parse_bytes(packet, '133')

        return start_index, number_of_fragments

    def _parse_read_setup_packet(self, packet):
        _, length, number_of_fragments, _ = parse_bytes(packet, '133')

        return length, number_of_fragments

    def _write_setup_packet(self, length, offset, total_fragments):
        return int(BlockTransferService.PACKET_TYPES['WRITE']['SETUP'] << 4).to_bytes(1, 'little') + \
               int(length).to_bytes(3, 'little') + \
               int(offset).to_bytes(3, 'little') + \
               int(total_fragments).to_bytes(3, 'little')


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
        print("Writing data %r to handle: %i" % (data, handle))
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
