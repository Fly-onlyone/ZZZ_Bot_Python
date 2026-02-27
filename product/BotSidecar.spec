# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_delvewheel_libs_directory
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules


datas = []
binaries = []
hiddenimports = []
hiddenimports += collect_submodules("plyer")
tmp_ret = collect_all("apprise")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# NumPy 2.x wheels on Windows ship hashed DLLs in numpy.libs (OpenBLAS/MSVCP).
datas += collect_data_files("numpy")
binaries += collect_dynamic_libs("numpy")
datas, binaries = collect_delvewheel_libs_directory(
    "numpy", datas=datas, binaries=binaries
)


def _collect_openssl_binaries():
    """Collect OpenSSL DLLs required by Python's _ssl module on Windows."""

    openssl_patterns = ["libssl-*.dll", "libcrypto-*.dll"]
    prefixes = {
        Path(prefix)
        for prefix in (sys.prefix, sys.base_prefix, sys.exec_prefix)
        if prefix
    }
    search_roots = []
    for prefix in prefixes:
        search_roots.extend([prefix, prefix / "DLLs"])
    found = []

    for root in search_roots:
        if not root.exists():
            continue
        for pattern in openssl_patterns:
            for dll in root.glob(pattern):
                found.append((str(dll), "."))

    seen = set()
    unique = []
    for item in found:
        if item[0] in seen:
            continue
        seen.add(item[0])
        unique.append(item)
    return unique


binaries += _collect_openssl_binaries()

datas += [
    ("./../images", "images"),
    ("./../sample", "sample"),
    ("./../reward image", "reward image"),
    ("./../backend/message", "backend/message"),
    ("./../backend/playwright-browsers", "playwright-browsers"),
]

a = Analysis(
    ["..\\backend\\Bot.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="zzz-backend",
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
)
