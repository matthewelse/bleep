# bleep

[![CI](https://github.com/matthewelse/bleep/actions/workflows/CI.yml/badge.svg)](https://github.com/matthewelse/bleep/actions/workflows/CI.yml)

A BLE abstraction layer for Python. This library is a wrapper around the
`btleplug` rust library, and supports Windows, Linux and macOS.

## Current Support

* Discovering devices
* Reading advertising data
* Connecting to devices
* Discovering services, characteristics and descriptors
* Read from and writing to characteristics

## Installation

```bash
pip install bleep
```

If you want to develop bleep, instead of the last line, clone the repo and run:

```
git clone https://github.com/matthewelse/bleep
pip install maturin
maturin develop 
```

## Examples

### tree.py

You can run tree.py to see all of the services, characteristics and descriptors
attached to a device with a specific name. In order to find the device's name
address, you could use `hcitool lescan`, or use `BLEDevice.discoverDevices()`.

```
usage: tree.py [-h] name 
```

## Usage

<!-- TODO: add some more complete examples here. -->

See examples/ for examples of how to use this library.
