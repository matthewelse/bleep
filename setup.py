from setuptools import setup, find_packages

setup(
	name = "bleep",
	version = "0.0.1",
	author = "Matthew Else",
	author_email = "matthew.else@arm.com",
	description = "Python BLE API",
	license = "Apache-2.0",
	keywords = "ble",
	url = "about:blank",
	packages = find_packages(),
	package_data = {
		'bleep': ['data/*.json']
	}
)
