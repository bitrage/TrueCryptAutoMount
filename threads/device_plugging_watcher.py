''' Copyright (c) 2014-2018, Felix Heide

    This file is part of TrueCrypt AutoMount.

    TrueCrypt AutoMount is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    TrueCrypt AutoMount is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with TrueCrypt AutoMount.  If not, see <http://www.gnu.org/licenses/>.
'''

import wmi
import pythoncom


def thread(thread_signal):
    pythoncom.CoInitialize()  # @UndefinedVariable
    interface = wmi.WMI()
    watcher = interface.Win32_DeviceChangeEvent.watch_for()
    event_occured = False
    while True:
        try:
            event = watcher(1000).EventType  # Timeout 1000ms
            if event == 2 or event == 3:  # Device Arrival (2) or Device Unplugged (3)
                event_occured = True
        except wmi.x_wmi_timed_out:
            if event_occured:
                event_occured = False
                thread_signal.emit()
