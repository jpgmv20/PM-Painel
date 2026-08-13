"""Navegador Chromium temporário, controlado pelo ciclo de vida do painel."""

from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional


class BrowserManager:
    """Abre o Chrome em uma janela comum, mas com perfil exclusivo e descartável."""

    _PROFILE_PREFIX = "pm-painel-browser-"

    def __init__(self, base_temp_dir: Optional[str | Path] = None) -> None:
        temporary_root = Path(base_temp_dir) if base_temp_dir else Path(tempfile.gettempdir())
        self._profiles_root = temporary_root / "pm-painel-browser-profiles"
        self._profile_dir: Optional[Path] = None
        self._browser_processes: list[subprocess.Popen[bytes]] = []
        self._destroyed = False
        self._resource_releaser: Optional[Callable[[], None]] = None

        self._remove_abandoned_profiles()
        self._create_profile()
        atexit.register(self.destroy_profile)

    @property
    def profile_path(self) -> Path:
        """Diretório que contém somente os dados da sessão atual do navegador."""
        if self._profile_dir is None:
            raise RuntimeError("O perfil temporário do navegador já foi removido.")
        return self._profile_dir

    @property
    def is_open(self) -> bool:
        """Informa se a janela do Chrome criada pelo painel ainda está aberta."""
        self._browser_processes = [
            process for process in self._browser_processes if process.poll() is None
        ]
        return bool(self._browser_processes)

    def open_url(
        self,
        url: str,
        title: str = "Navegador do PM-Painel",
        app_mode: bool = False,
    ) -> None:
        """Abre uma janela completa do Chrome sem tocar no perfil pessoal do usuário."""
        if self._destroyed:
            raise RuntimeError("O navegador já foi encerrado junto com o painel.")
        if not url.startswith(("https://", "http://")):
            raise ValueError("A URL do navegador deve iniciar com http:// ou https://.")
        # Vários atalhos podem permanecer abertos ao mesmo tempo.

        # O Chrome recebe um diretório temporário próprio, portanto abas, cookies e
        # favoritos do navegador pessoal não são lidos nem modificados.
        command = [
            str(self._find_chromium_executable()),
            f"--user-data-dir={self.profile_path}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        if app_mode:
            command.append(f"--app={url}")
        else:
            command.extend(("--new-window", url))

        browser_process = subprocess.Popen(command, cwd=str(self.profile_path))
        time.sleep(0.2)
        # Nas aberturas seguintes o Chrome pode encaminhar a URL para a janela
        # já existente e encerrar somente este processo auxiliar com código 0.
        if browser_process.poll() not in (None, 0):
            exit_code = browser_process.returncode
            self._browser_process = None
            raise RuntimeError(f"Não foi possível iniciar o navegador (código {exit_code}).")

        self._browser_processes.append(browser_process)

    def close_browser(self) -> None:
        """Fecha somente a janela pertencente ao painel antes de apagar o perfil."""
        browser_processes, self._browser_processes = self._browser_processes, []
        for browser_process in browser_processes:
            if browser_process.poll() is not None:
                continue
            browser_process.terminate()
            try:
                browser_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                browser_process.kill()
                browser_process.wait(timeout=2)
        return

    def register_resource_releaser(self, releaser: Callable[[], None]) -> None:
        """Registra uma limpeza complementar para recursos futuros do navegador."""
        self._resource_releaser = releaser

    def shutdown(self) -> None:
        """Encerra o Chrome e remove todos os dados temporários desta execução."""
        try:
            if self._resource_releaser is not None:
                self._resource_releaser()
        finally:
            self.destroy_profile()

    def destroy_profile(self) -> None:
        """Remove cookies, cache e preferências quando o programa principal termina."""
        if self._destroyed:
            return
        self._destroyed = True
        self.close_browser()
        profile_dir, self._profile_dir = self._profile_dir, None
        if profile_dir is not None:
            shutil.rmtree(profile_dir, ignore_errors=True)
        try:
            self._profiles_root.rmdir()
        except OSError:
            pass

    def get_profile_path(self) -> Path:
        """Mantém compatibilidade com componentes visuais que exibem o caminho."""
        return self.profile_path

    @staticmethod
    def _find_chromium_executable() -> Path:
        """Localiza um navegador Chromium instalado, priorizando o Google Chrome."""
        candidates = (
            Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise RuntimeError("Instale Google Chrome ou Microsoft Edge para usar o navegador do painel.")

    def _create_profile(self) -> None:
        self._profiles_root.mkdir(parents=True, exist_ok=True)
        self._profile_dir = Path(tempfile.mkdtemp(prefix=f"{self._PROFILE_PREFIX}{os.getpid()}-", dir=self._profiles_root))

    def _remove_abandoned_profiles(self) -> None:
        """Apaga perfis de execuções que foram encerradas inesperadamente."""
        if not self._profiles_root.exists():
            return
        for candidate in self._profiles_root.iterdir():
            if candidate.is_dir() and candidate.name.startswith(self._PROFILE_PREFIX):
                shutil.rmtree(candidate, ignore_errors=True)
