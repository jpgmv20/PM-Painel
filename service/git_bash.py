"""Git Bash com perfil descartável para o PM-Painel."""

from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional


class GitBashManager:
    """Abre o Git Bash sem reutilizar histórico, configuração ou credenciais."""

    _PROFILE_PREFIX = "pm-painel-git-"

    def __init__(
        self,
        base_temp_dir: Optional[str | Path] = None,
        cleanup_abandoned_profiles: bool = True,
    ) -> None:
        temporary_root = Path(base_temp_dir) if base_temp_dir else Path(tempfile.gettempdir())
        self._profiles_root = temporary_root / "pm-painel-git-profiles"
        self._profiles_root.mkdir(parents=True, exist_ok=True)
        if cleanup_abandoned_profiles:
            self._remove_abandoned_profiles()
        self._profile_dir = Path(
            tempfile.mkdtemp(prefix=f"{self._PROFILE_PREFIX}{os.getpid()}-", dir=self._profiles_root)
        )
        self._processes: list[subprocess.Popen[bytes]] = []
        self._destroyed = False
        atexit.register(self.shutdown)

    def open_git_bash(self, working_directory: Optional[str | Path] = None) -> None:
        """Abre o Git Bash em uma pasta local, usando somente dados temporários."""
        if self._destroyed:
            raise RuntimeError("O perfil temporário do Git já foi removido.")

        start_directory = Path(working_directory or Path.home()).resolve()
        if not start_directory.is_dir():
            raise ValueError("A pasta inicial do Git Bash não existe.")

        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(self._profile_dir),
                "USERPROFILE": str(self._profile_dir),
                "HISTFILE": str(self._profile_dir / ".bash_history"),
                "GIT_CONFIG_GLOBAL": str(self._profile_dir / ".gitconfig"),
                "GIT_CONFIG_NOSYSTEM": "1",
                # Impede que o Git Credential Manager guarde logins do terminal.
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "credential.helper",
                "GIT_CONFIG_VALUE_0": "",
            }
        )
        command = [str(self._find_git_bash()), f"--cd={start_directory}"]
        process = subprocess.Popen(
            command,
            cwd=str(start_directory),
            env=environment,
        )
        time.sleep(0.2)
        if process.poll() not in (None, 0):
            raise RuntimeError("Não foi possível abrir o Git Bash.")
        self._processes.append(process)

    def shutdown(self) -> None:
        """Fecha os terminais do painel e apaga o perfil temporário."""
        if self._destroyed:
            return
        self._destroyed = True
        processes, self._processes = self._processes, []
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
        shutil.rmtree(self._profile_dir, ignore_errors=True)
        try:
            self._profiles_root.rmdir()
        except OSError:
            pass

    def _remove_abandoned_profiles(self) -> None:
        for candidate in self._profiles_root.iterdir():
            if candidate.is_dir() and candidate.name.startswith(self._PROFILE_PREFIX):
                owner_text = candidate.name[len(self._PROFILE_PREFIX):].split("-", 1)[0]
                try:
                    owner_pid = int(owner_text)
                except ValueError:
                    owner_pid = 0
                if not owner_pid or not self._process_is_running(owner_pid):
                    shutil.rmtree(candidate, ignore_errors=True)

    @staticmethod
    def _process_is_running(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except PermissionError:
            return True
        except OSError:
            return False

    @staticmethod
    def _find_git_bash() -> Path:
        candidates = (
            Path(os.environ.get("PROGRAMFILES", "")) / "Git" / "git-bash.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Git" / "git-bash.exe",
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise RuntimeError("Instale o Git for Windows para usar o Git Bash.")
