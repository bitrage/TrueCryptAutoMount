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

from .setting import Setting


class Drives(list):
    '''
    Drive Setting container
    '''

    def append(self, value):
        key = value["Letter"]
        for item in self:
            if item["Letter"] != key:
                continue
            self.remove(item)
            break
        super().append(Setting(value))
