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

from .enums import LogicalDiskType


class LogicalDisk(object):
    '''
    Representation of a system drive.
    '''

    def __init__(self, win32_logicaldisk):
        self.win32_logicaldisk = win32_logicaldisk
        self._letter = ""

    @property
    def id(self):
        return self.win32_logicaldisk.DeviceID

    @property
    def type(self):
        return LogicalDiskType(self.win32_logicaldisk.DriveType)

    @property
    def filesystem(self):
        return self.win32_logicaldisk.FileSystem

    @property
    def caption(self):
        return self.win32_logicaldisk.VolumeName

    @property
    def size(self):
        return self.win32_logicaldisk.Size

    @property
    def size_str(self):
        return "%s GiB" % int(int(self.size)/1024**3) if self.size else ""

    @property
    def free(self):
        return self.win32_logicaldisk.FreeSpace

    @property
    def free_str(self):
        return "%s GiB" % int(int(self.free)/1024**3) if self.free else ""

    @property
    def letter(self):
        return self.win32_logicaldisk.DeviceID
