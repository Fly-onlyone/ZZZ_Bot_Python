# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
hiddenimports += collect_submodules("plyer")
tmp_ret = collect_all("apprise")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

datas += [
    ("./../frontend/dist", "frontend/dist"),
    ("./../images", "images"),
    ("./../sample", "sample"),
    ("./../reward image", "reward image"),
    ("./../src/message", "message"),
    ("./../src/playwright-browsers", "playwright-browsers"),
]

a = Analysis(
    ["..\\src\\Bot.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ZZZ Bot",
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
    icon="../images/Qingyi02.ico",
    version='Bot version.txt',
)

