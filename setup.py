import sys
import glob
import os
import shutil
import TrueCryptAutoMount
from cx_Freeze import setup, Executable
from PyQt5 import QtCore
 
app = QtCore.QCoreApplication(sys.argv)
qt_library_path = QtCore.QCoreApplication.libraryPaths()

imageformats_path = None
for path in qt_library_path:
    if os.path.exists(os.path.join(path, 'imageformats')):
        imageformats_path = os.path.join(path, 'imageformats')
        local_imageformats_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imageformats')
        if not os.path.exists(local_imageformats_path):
            os.mkdir(local_imageformats_path)
        for file in glob.glob(os.path.join(imageformats_path, '*')):
            shutil.copy(file, os.path.join(local_imageformats_path, os.path.basename(file)))

# Dependencies are automatically detected, but it might need fine tuning.
includefiles = [('gui.ui','gui.ui'),
				('about.ui','about.ui'),
				('batch.ui','batch.ui'),
                ('imageformats/qgif.dll','imageformats/qgif.dll')]
includes = ['sip', 'PyQt5.QtCore']
build_dir = os.path.abspath('../build') 
build_exe_options = {"icon": "icons/logo.ico", 'include_files': includefiles, 'includes':includes, 'build_exe': build_dir}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "TrueCrypt AutoMount",
        version = TrueCryptAutoMount.__version__,
        description = "TrueCrypt AutoMount",
        options = {"build_exe": build_exe_options},
        executables = [Executable("TrueCryptAutoMount.py", base=base)])
        #executables = [Executable("TrueCryptAutoMount.py")])