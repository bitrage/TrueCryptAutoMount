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

import time
import win32api
import pythoncom


def thread(thread_signal):
    pythoncom.CoInitialize()  # @UndefinedVariable
    w32_logicaldrives = win32api.GetLogicalDriveStrings()
    while True:
        time.sleep(1)
        new_call = win32api.GetLogicalDriveStrings()
        if w32_logicaldrives != new_call:
            w32_logicaldrives = new_call
            thread_signal.emit()
