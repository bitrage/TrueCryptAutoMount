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


def format_serial_number(serial_number):
    try:
        sn_str = bytes.fromhex(serial_number).decode('ascii')
        if any([ord(c) < 32 for c in sn_str]):
            return serial_number
    except UnicodeDecodeError:
        return serial_number
    except ValueError:
        return serial_number
    c = ""
    for n in range(0, len(sn_str), 2):
        c += sn_str[n+1]
        c += sn_str[n]
    return c.strip()
