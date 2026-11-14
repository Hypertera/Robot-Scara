
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules


# ============================================================
# Directorio principal del proyecto
# ============================================================

project_dir = Path(SPECPATH) / "ControlSCARA"


# ============================================================
# Recursos de la aplicación
# ============================================================

datas = []

# Incorporar todos los PNG, conservando sus carpetas
excluded_dirs = {"build", "dist", ".venv", "venv", "__pycache__"}

for file in project_dir.rglob("*"):

    if not file.is_file():
        continue

    if any(part in excluded_dirs for part in file.relative_to(project_dir).parts):
        continue

    if file.suffix.lower() == ".png":
        destination = file.parent.relative_to(project_dir)
        datas.append((str(file), str(destination)))


# Iconos de la aplicación
datas += [
    (str(project_dir / "icon.ico"), "."),
    (str(project_dir / "icon.icns"), "."),
]


# Fuentes tipográficas
fonts_dir = project_dir / "Fuentes"

if fonts_dir.exists():

    for file in fonts_dir.rglob("*"):

        if file.is_file():

            destination = file.parent.relative_to(project_dir)
            datas.append((str(file), str(destination)))


# ============================================================
# Recursos de pyqtgraph
# ============================================================

pg_datas, pg_binaries, pg_hiddenimports = collect_all("pyqtgraph")

datas += pg_datas

# ============================================================
# Recursos de PySerial
# ============================================================

serial_hiddenimports = collect_submodules("serial")

hiddenimports = pg_hiddenimports + serial_hiddenimports

# ============================================================
# Icono según el sistema operativo
# ============================================================

if sys.platform == "darwin":
    icono_ejecutable = str(project_dir / "icon.icns")
else:
    icono_ejecutable = str(project_dir / "icon.ico")


# ============================================================
# Análisis
# ============================================================

a = Analysis(
    [str(project_dir / "InterfazRobot.py")],

    pathex=[str(project_dir)],

    binaries=pg_binaries,
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

pyz = PYZ(a.pure)


# ============================================================
# Ejecutable
# ============================================================

exe = EXE(
    pyz,
    a.scripts,
    [],

    exclude_binaries=True,

    name="ControlSCARA",

    icon=icono_ejecutable,

    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)


# ============================================================
# Distribución onedir
# ============================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,

    strip=False,
    upx=True,

    name="ControlSCARA",
)


# ============================================================
# Aplicación macOS
# ============================================================

if sys.platform == "darwin":

    app = BUNDLE(
        coll,

        name="ControlSCARA.app",

        icon=str(project_dir / "icon.icns"),

        bundle_identifier="com.hypertera.controlscara",
    )
