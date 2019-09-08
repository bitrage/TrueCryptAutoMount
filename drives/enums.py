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

from enum import Enum


class LogicalDiskType(Enum):
    UNKNOWN = 0
    NO_ROOT_DIRECTORY = 1
    REMOVABLE_DRIVE = 2
    LOCAL_DRIVE = 3
    NETWORK_DRIVE = 4
    COMPACT_DISC = 5
    RAM_DRIVE = 6
