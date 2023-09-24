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
import asyncio
from bleep import BLEDevice, BleManager


async def main(name):
    manager = await BleManager.new()
    ads = await manager.adapters()

    for device in await BLEDevice.discoverDevices(ads[0]):
        if device.name != name:
            continue

        try:
            print("Attempting to connect to %s" % device.name)
            await device.connect()

            for service in await device.services():
                print("  " + repr(service))

                for characteristic in service.characteristics():
                    print("    " + repr(characteristic))

                    for descriptor in characteristic.descriptors():
                        print("      " + repr(descriptor))

            break
        except Exception as e:
            print(f"Disconnecting due to exception ({e})")
            await device.disconnect()
            raise
        finally:
            print("Disconnecting")
            await device.disconnect()
    else:
        # break didn't get called
        print("Device not Found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Produce a tree of a BLE Device")

    parser.add_argument("name", help="Target device name")

    args = parser.parse_args()

    asyncio.run(main(args.name))
