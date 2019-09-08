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

import win32file


class Volume(object):
    '''
    Representation of a system volume.
    '''

    def __init__(self, win32_volume, win32_logicaldisks):
        self.win32_logicaldisks = win32_logicaldisks
        self.win32_volume = win32_volume
        self._letter = ""

    @property
    def id(self):
        try:
            return win32file.QueryDosDevice(self.serial.replace("\\", "").replace("?", "")).strip("\x00")
        except Exception:
            return "Unknown"

    @property
    def partition_index(self):
        return None

    @property
    def disk_index(self):
        return None

    @property
    def caption(self):
        return "Unidentified Harddisk Volume"

    @property
    def serial(self):
        return self.win32_volume.DeviceID

    @property
    def letter(self):
        return self._letter.lower()

    @letter.setter
    def letter(self, value):
        self._letter = value.lower()[0:1]

    @property
    def free(self):
        disk = self._get_win32_logicaldisk()
        if disk:
            return disk.FreeSpace

    @property
    def size(self):
        disk = self._get_win32_logicaldisk()
        if disk:
            return disk.Size
        return 0

    @property
    def size_str(self):
        return "%s GiB" % int(int(self.size)/1024**3)

    def _get_win32_logicaldisk(self):
        for win32_logicaldisk in self.win32_logicaldisks:
            if win32_logicaldisk.DeviceID.lower() == self.letter:
                return win32_logicaldisk
