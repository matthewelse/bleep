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
# 2/3 compatibility
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from future.utils import bytes_to_native_str, native_str_to_bytes
from future.builtins import int, bytes

from .backend import GATTRequester

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
