# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all


# Recursos propios de la aplicación
datas = [
    ("icon.ico", "."),
    ("switch.png", "."),
    ("switch2.png", "."),
]

# Recopilar los componentes necesarios de pyqtgraph
pg_datas, pg_binaries, pg_hiddenimports = collect_all("pyqtgraph")

datas += pg_datas


a = Analysis(
    ["InterfazSimulacion.py"],
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

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Simulador_SCARA_by_Hypertera",
    debug=False,
    icon="icon.ico",
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
