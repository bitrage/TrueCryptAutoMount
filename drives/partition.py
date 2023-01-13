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

from helpers import format_serial_number


class Partition(object):
    '''
    Representation of a system partition.
    '''

    def __init__(self, win32_diskpartition, win32_logicaldisks, win32_diskdrives):
        self.win32_diskdrives = win32_diskdrives
        self.win32_logicaldisks = win32_logicaldisks
        self.win32_diskpartition = win32_diskpartition
        self.win32_diskdrive = self._get_win32_diskdrive()
        self._letter = ""

    @property
    def id(self):
        return "\\Device\\Harddisk{}\\Partition{}".format(self.disk_index, self.partition_index)

    @property
    def partition_index(self):
        offset = 1
        if self.is_gpt:
            offset += 1
        return self.win32_diskpartition.Index + offset

    @property
    def disk_index(self):
        return self.win32_diskpartition.DiskIndex

    @property
    def caption(self):
        return self.win32_diskdrive.Caption

    @property
    def serial(self):
        if self.win32_diskdrive and self.win32_diskdrive.SerialNumber:
            return "{}#{}".format(format_serial_number(self.win32_diskdrive.SerialNumber.strip()), self.partition_index)
        else:
            return "NoSerial"

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
        return self.win32_diskpartition.Size

    @property
    def size_str(self):
        return "%s GiB" % int(int(self.size) / 1024 ** 3)

    @property
    def is_gpt(self):
        return self.win32_diskpartition.Type.startswith("GPT")

    def _get_win32_logicaldisk(self):
        for win32_logicaldisk in self.win32_logicaldisks:
            if win32_logicaldisk.DeviceID.lower() == self.letter:
                return win32_logicaldisk

    def _get_win32_diskdrive(self):
        for win32_diskdrive in self.win32_diskdrives:
            if win32_diskdrive.Index == self.disk_index:
                return win32_diskdrive
