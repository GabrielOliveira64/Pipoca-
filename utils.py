import os
import sys

def resource_path(relative_path):
    """Obtém o caminho absoluto para recursos, funciona para desenvolvimento e PyInstaller"""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)