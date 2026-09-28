"""Integração reversível do PM-Painel com a inicialização do Windows."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


class WindowsStartupService:
    """Registra o executável atual somente para o usuário conectado."""

    VALUE_NAME = "PM-Painel"
    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def set_enabled(self, enabled: bool) -> None:
        if os.name != "nt":
            raise OSError("A inicialização automática só está disponível no Windows.")

        import winreg

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, self.RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                command = self._launch_command()
                winreg.SetValueEx(key, self.VALUE_NAME, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, self.VALUE_NAME)
                except FileNotFoundError:
                    pass

    @staticmethod
    def _launch_command() -> str:
        if getattr(sys, "frozen", False):
            parts = [sys.executable]
        else:
            interpreter = Path(sys.executable)
            windowless = interpreter.with_name("pythonw.exe")
            executable = str(windowless if windowless.is_file() else interpreter)
            entrypoint = Path(__file__).resolve().parents[1] / "main.py"
            parts = [executable, str(entrypoint)]
        return subprocess.list2cmdline(parts)
