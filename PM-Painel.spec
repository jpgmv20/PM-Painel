# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

project_dir = Path(SPECPATH)


# ============================================================
# IMPORTS OCULTOS
# ============================================================

hiddenimports = []

hiddenimports += collect_submodules("model")
hiddenimports += collect_submodules("service")
hiddenimports += collect_submodules("devtools")
hiddenimports += collect_submodules("plugins")
hiddenimports += collect_submodules("core")
hiddenimports += collect_submodules("data")
hiddenimports += collect_submodules("database")


# ============================================================
# ARQUIVOS E PASTAS QUE DEVEM SER COPIADOS
# ============================================================

datas = [
    ("assets", "assets"),
    ("view", "view"),
    ("core", "core"),
    ("data", "data"),
    ("database", "database"),
    ("docs", "docs"),
]


# ============================================================
# ANÁLISE DO PROJETO
# ============================================================

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)


# ============================================================
# PYZ
# ============================================================

pyz = PYZ(
    a.pure
)


# ============================================================
# EXECUTÁVEL
# ============================================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PM-Painel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)


# ============================================================
# DISTRIBUIÇÃO EM PASTA
# ============================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="PM-Painel",
)