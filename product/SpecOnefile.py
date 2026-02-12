# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_submodules
from pathlib import Path
import sys

datas = []
binaries = []
hiddenimports = []
hiddenimports += collect_submodules("plyer")
tmp_ret = collect_all("apprise")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


def _collect_openssl_binaries():
    """Collect OpenSSL DLLs required by Python's _ssl module on Windows.

    Some Python distributions ship these in either <python>/DLLs or directly in
    <python>. If these files are omitted from onefile builds, importing
    ``ssl`` fails at runtime with:
    "ImportError: DLL load failed while importing _ssl"
    """

    openssl_patterns = ["libssl-*.dll", "libcrypto-*.dll"]
    search_roots = [Path(sys.base_prefix), Path(sys.base_prefix) / "DLLs"]
    found = []

    for root in search_roots:
        if not root.exists():
            continue
        for pattern in openssl_patterns:
            for dll in root.glob(pattern):
                found.append((str(dll), "."))

    # Preserve order but remove duplicates.
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
    ("./../frontend/dist", "frontend/dist"),
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
    version="Bot version.txt",
)
