import sys
import os
from cx_Freeze import setup, Executable

include_files = [
    ("assets", "assets"),
    ("data", "data"),
    ("ui/icons", "ui/icons"),
    ("dll/api-ms-win-core-path-l1-1-0.dll", "dll/api-ms-win-core-path-l1-1-0.dll"),
    ("dll/api-ms-win-core-winrt-l1-1-0.dll", "dll/api-ms-win-core-winrt-l1-1-0.dll"),
    ("dll/api-ms-win-core-winrt-string-l1-1-0.dll", "dll/api-ms-win-core-winrt-string-l1-1-0.dll"),
    ("dll/api-ms-win-crt-conio-l1-1-0.dll", "dll/api-ms-win-crt-conio-l1-1-0.dll"),
    ("dll/api-ms-win-crt-convert-l1-1-0.dll", "dll/api-ms-win-crt-convert-l1-1-0.dll"),
    ("dll/api-ms-win-crt-environment-l1-1-0.dll", "dll/api-ms-win-crt-environment-l1-1-0.dll"),
    ("dll/api-ms-win-crt-filesystem-l1-1-0.dll", "dll/api-ms-win-crt-filesystem-l1-1-0.dll"),
    ("dll/api-ms-win-crt-locale-l1-1-0.dll", "dll/api-ms-win-crt-locale-l1-1-0.dll"),
    ("dll/api-ms-win-crt-math-l1-1-0.dll", "dll/api-ms-win-crt-math-l1-1-0.dll"),
    ("dll/api-ms-win-crt-process-l1-1-0.dll", "dll/api-ms-win-crt-process-l1-1-0.dll"),
    ("dll/api-ms-win-crt-runtime-l1-1-0.dll", "dll/api-ms-win-crt-runtime-l1-1-0.dll"),
    ("dll/api-ms-win-crt-stdio-l1-1-0.dll", "dll/api-ms-win-crt-stdio-l1-1-0.dll"),
    ("dll/api-ms-win-crt-string-l1-1-0.dll", "dll/api-ms-win-crt-string-l1-1-0.dll"),
    ("dll/api-ms-win-crt-time-l1-1-0.dll", "dll/api-ms-win-crt-time-l1-1-0.dll"),
    ("dll/api-ms-win-crt-utility-l1-1-0.dll", "dll/api-ms-win-crt-utility-l1-1-0.dll"),
]

build_exe_options = {
    "packages": ["os", "sys", "requests", "json", "PyQt5", "urllib"],
    "include_files": include_files,
    "includes": [],
    "excludes": ["PyQt5.QtQml", "PySide2.QtQml"],
}

base = "Win32GUI" if sys.platform == "win32" else None

# Criação correta do executável
executavel = Executable(
    script="main.py",
    base=base,
    target_name="PipocaPlus.exe",
    icon="icon/pipocaplus.ico"
)

setup(
    name="PipocaPlus",
    version="1.0",
    description="PipocaPlus",
    options={"build_exe": build_exe_options},
    executables=[executavel]  # <-- usa o correto aqui
)
