from gattlib import GATTRequester

req = GATTRequester("C9:E8:56:3B:4D:B1", False)
req.connect(True, "random")
req.is_connected()

print(req.discover_primary())
req.disconnect()
