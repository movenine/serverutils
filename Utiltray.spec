# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ("ServerUtils.ico", '.'),
    ("hapconvert.ui", '.'),
    ("Files/*", 'Files'),
    ("log/*", 'log'),
    ("Manual/*", 'Manual'),
    ("resources/*", 'resources')
    ]

a = Analysis(
    ['Utiltray.py'],
    pathex=['D:\\MyJobs\\Software\\02_Project\\pythonProject\\ServerUtils'],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
    )

exe = EXE(
    pyz,
    a.binaries,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Utiltray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon='./ServerUtils.ico',
    contents_directory='.'
)
coll = COLLECT(
    exe,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Utiltray_v100'
)
