# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for mycelium-core sidecar (onedir).

Ships the HTTP Core without torch/sentence-transformers to keep the download
size workable. Embedding falls back to the offline hashing backend (see
bootstrap.py). A later release can vendor MiniLM into the bundle.
"""

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

ENTRY = Path(SPECPATH).resolve() / "sidecar_entry.py"
SRC = Path(SPECPATH).resolve().parents[1] / "src"

datas: list = []
binaries: list = []
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "mycelium",
    "mycelium.adapters.http.app",
    "mycelium.cli",
    "mycelium.adapters.embeddings.hashing",
    "mycelium.adapters.embeddings.bootstrap",
]

for pkg in ("fastapi", "starlette", "pydantic", "anyio", "httpx", "mcp", "watchdog"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception:
        pass

a = Analysis(
    [str(ENTRY)],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch",
        "torchvision",
        "torchaudio",
        "sentence_transformers",
        "transformers",
        "tensorflow",
        "sklearn",
        "scipy",
        "matplotlib",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="mycelium-core",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="mycelium-core",
)
