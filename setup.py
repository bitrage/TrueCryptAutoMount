import sys
import os
import TrueCryptAutoMount
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
includefiles = [('gui.ui','gui.ui'),
				('about.ui','about.ui'),
				('batch.ui','batch.ui')]
#includes = ['sip', 'PyQt5.QtCore']
build_dir = os.path.abspath('../build') 
build_exe_options = {"icon": "icons/logo.ico", 'include_files': includefiles, 'build_exe': build_dir}

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