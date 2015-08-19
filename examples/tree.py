from bleep import BLEDevice

if __name__ == "__main__":
    for device in BLEDevice.discoverDevices(filter=lambda x: x.address == "C9:E8:56:3B:4D:B1"):
        print(device)
        try:
            device.connect()

            for uuid, service in device.services.items():
                print("  " + repr(service))

                for char_uuid, characteristic in service.characteristics.items():
                    print("    " + repr(characteristic))

            break
        except:
            device.requester.disconnect()
        finally:
            device.requester.disconnect()
    else:
        # break didn't get called
        print('No Devices Found')
