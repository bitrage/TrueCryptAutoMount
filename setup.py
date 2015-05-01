import sys
import glob
import os
import shutil
import TrueCryptAutoMount
from cx_Freeze import setup, Executable
from PyQt4 import QtCore
 
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
                ('imageformats/qgif4.dll','imageformats/qgif4.dll'),
                ('icons/ico16.png','icons/ico16.png'),
                ('icons/ico24.png','icons/ico24.png'),
                ('icons/ico32.png','icons/ico32.png'),
                ('icons/ico48.png','icons/ico48.png'),
                ('icons/tc_logo.gif','icons/tc_logo.gif'),
                ('icons/readme.html','icons/readme.html'),
                ('icons/silk/drive.png','icons/silk/drive.png'),
                ('icons/silk/drive_add.png','icons/silk/drive_add.png'),
                ('icons/silk/drive_cd.png','icons/silk/drive_cd.png'),
                ('icons/silk/drive_link.png','icons/silk/drive_link.png'),
                ('icons/silk/drive_network.png','icons/silk/drive_network.png'),
                ('icons/silk/drive_flash.png','icons/silk/drive_flash.png'),
                ('icons/silk/drive_go.png','icons/silk/drive_go.png'),
                ('icons/silk/drive_error.png','icons/silk/drive_error.png'),
                ('icons/silk/application_double.png','icons/silk/application_double.png')]
includes = ['sip', 'PyQt4.QtCore']
build_exe_options = {"icon": "icons/logo.ico", 'include_files': includefiles, 'includes':includes}

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