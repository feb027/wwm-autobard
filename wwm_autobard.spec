# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for WWM Auto-Bard

from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / 'launcher.py')],
    pathex=[str(ROOT), str(ROOT / 'src')],
    binaries=[],
    datas=[
        (str(ROOT / 'src' / 'autobard'), 'autobard'),
        (str(ROOT / 'resources' / 'icon.ico'), 'resources'),
    ],
    hiddenimports=[
        'customtkinter',
        'mido',
        'mido.backends',
        'mido.backends.rtmidi',
        'keyboard',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
        'autobard',
        'autobard.config',
        'autobard.app',
        'autobard.gui',
        'autobard.gui.modern_window',
        'autobard.models',
        'autobard.core',
        'autobard.services',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WWM_AutoBard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'resources' / 'icon_rounded.ico') if (ROOT / 'resources' / 'icon_rounded.ico').exists() else (str(ROOT / 'resources' / 'icon.ico') if (ROOT / 'resources' / 'icon.ico').exists() else None),
)
