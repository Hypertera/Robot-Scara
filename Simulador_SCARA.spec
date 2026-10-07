# -*- mode: python ; coding: utf-8 -*-

import sys

from PyInstaller.utils.hooks import collect_all


# ============================================================
# Recursos de la aplicación
# ============================================================

datas = [
    ("SimuladorSCARA/icon.ico", "."),
    ("SimuladorSCARA/icon.icns", "."),
    ("SimuladorSCARA/switch.png", "."),
    ("SimuladorSCARA/switch2.png", "."),
]


# ============================================================
# Recursos de pyqtgraph
# ============================================================

pg_datas, pg_binaries, pg_hiddenimports = collect_all("pyqtgraph")

datas += pg_datas


# ============================================================
# Icono según el sistema operativo
# ============================================================

if sys.platform == "darwin":
    icono_ejecutable = "SimuladorSCARA/icon.icns"
else:
    icono_ejecutable = "SimuladorSCARA/icon.ico"


# ============================================================
# Análisis
# ============================================================

a = Analysis(
    ["SimuladorSCARA/InterfazSimulacion.py"],
    pathex=[],
    binaries=pg_binaries,
    datas=datas,
    hiddenimports=pg_hiddenimports,
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
    name="Simulador_SCARA_by_Hypertera",
    icon=icono_ejecutable,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name="Simulador_SCARA_by_Hypertera",
)


# ============================================================
# Aplicación macOS
# ============================================================

if sys.platform == "darwin":

    app = BUNDLE(
        coll,
        name="Simulador_SCARA_by_Hypertera.app",
        icon="SimuladorSCARA/icon.icns",
        bundle_identifier="com.hypertera.simuladorscara",
    )