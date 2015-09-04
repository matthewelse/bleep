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

import argparse
from bleep import BLEDevice

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Produce a tree of a BLE Device')

    parser.add_argument('mac', help='Target MAC Address')

    args = parser.parse_args()

    address = args.mac

    for device in BLEDevice.discoverDevices():
        print(device.address)

        if str(device.address) != address:
            continue

        print(device)

        try:
            print("Attempting to connect to %s" % device.address)
            device.connect()

            for service in device.services:
                print("  " + repr(service))

                for characteristic in service.characteristics:
                    print("    " + repr(characteristic))

                    for descriptor in characteristic.descriptors:
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
