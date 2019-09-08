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

import os
import sys
import platform
import functools
from PyQt5 import QtWidgets

import gui


# Windows7 Taskbar Grouping (Don't group with Python)
if platform.system() == 'Windows' and platform.release() >= '7':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('TrueCrypt_AutoMount')

sys.excepthook = gui.excepthook


def on_close(win):
    win.save_settings()
    win.sysTray.setVisible(False)
    print("Goodbye")


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        # The application is frozen
        os.chdir(os.path.dirname(os.path.abspath(sys.executable)))
    else:
        # The application is not frozen
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = QtWidgets.QApplication(sys.argv)
    win = gui.TrueCrypt_AutoMounter()
    # win.show()
    app.aboutToQuit.connect(functools.partial(on_close, win=win))
    sys.exit(app.exec_())
