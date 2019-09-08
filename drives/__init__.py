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

from .disk import Disk
from .logicaldisk import LogicalDisk
from .partition import Partition
from .volume import Volume
from .enums import LogicalDiskType
from wmi import x_wmi

import time


class Drives(object):
    '''
    Representation of all system drives.
    '''
    try_again = True

    def __init__(self, interface):
        self.interface = interface
        self.win32_diskdrives = None
        self.win32_diskpartitions = None
        self.win32_volumes = None
        self.win32_logicaldisks = None
        self._drives = []
        self._logicaldisks = []

    def _init_wmi_objects(self):
        try:
            self.win32_diskdrives = self.interface.Win32_DiskDrive()
            self.win32_diskpartitions = self.interface.Win32_DiskPartition()
            self.win32_volumes = self.interface.Win32_Volume()
            self.win32_logicaldisks = self.interface.Win32_LogicalDisk()
        except x_wmi:
            if self.try_again:
                time.sleep(5)
                self.try_again = False
                self._init_wmi_objects()
            else:
                raise
        else:
            self.try_again = True

    def _init_all_drives(self):
        for win32_diskdrive in self.win32_diskdrives:
            # Only find identifiable drives
            if 'PHYSICALDRIVE' not in win32_diskdrive.DeviceID:
                continue
            if not win32_diskdrive.SerialNumber:
                continue
            self._drives.append(Disk(win32_diskdrive, self.win32_logicaldisks))

        for win32_diskpartition in self.win32_diskpartitions:
            self._drives.append(Partition(win32_diskpartition, self.win32_logicaldisks, self.win32_diskdrives))

        for win32_volume in self.win32_volumes:
            # Ignore already mounted volumes
            if win32_volume.DriveType != 3 or win32_volume.FileSystem:
                continue
            self._drives.append(Volume(win32_volume, self.win32_logicaldisks))

        for win32_logicaldisk in self.win32_logicaldisks:
            self._logicaldisks.append(LogicalDisk(win32_logicaldisk))

    def refresh(self):
        self.win32_diskdrives = None
        self.win32_diskpartitions = None
        self.win32_volumes = None
        self.win32_logicaldisks = None
        self._drives = []
        self._logicaldisks = []
        self._init_wmi_objects()
        self._init_all_drives()

    def get_drive_by_id(self, drive_id):
        for drive in self._drives:
            if drive.id == drive_id:
                return drive

    def get_drive_by_serial(self, drive_serial):
        for drive in self._drives:
            if drive.serial == drive_serial:
                return drive

    def get_logicaldisk_by_id(self, logicaldisk_id):
        for logicaldisk in self._logicaldisks:
            if logicaldisk.id == logicaldisk_id:
                return logicaldisk

    @property
    def drives(self):
        return self._drives

    @property
    def logicaldisks(self):
        return self._logicaldisks
