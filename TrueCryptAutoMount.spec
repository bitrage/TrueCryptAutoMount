# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['TrueCryptAutoMount.py', 'TrueCryptAutoMount.spec'],
             pathex=['..\\TrueCryptAutoMount'],
             binaries=[],
             datas=[('gui.ui', '.'),
                ('about.ui', '.'),
                ('batch.ui', '.'),
                ('README.md', '.'),
                ('COPYING', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='TrueCryptAutoMount',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon="icons/logo.ico")
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='TrueCryptAutoMount')
