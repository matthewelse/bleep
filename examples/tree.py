import argparse
from bleep import BLEDevice

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Produce a tree of a BLE Device')

    parser.add_argument('mac', help='Target MAC Address')

    args = parser.parse_args()

    address = args.mac

    for device in BLEDevice.discoverDevices():
        if device.address != address:
            continue

        print(device)

        try:
            device.connect()

            for uuid, service in device.services:
                print("  " + repr(service))

                for char_uuid, characteristic in service.characteristics:
                    print("    " + repr(characteristic))

                    for desc_uuid, descriptor in characteristic.descriptors:
                        print("      " + repr(descriptor))

            break
        except:
            device.requester.disconnect()
            raise
        finally:
            device.requester.disconnect()
    else:
        # break didn't get called
        print('Device not Found')
