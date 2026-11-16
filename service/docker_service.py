"""Serviço de detecção e gerenciamento do ciclo de vida do Docker."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Callable


class DockerService:
    """Gerencia a detecção, diagnóstico e inicialização do serviço Docker."""

    @staticmethod
    def _creation_flags() -> int:
        return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

    def get_docker_executable(self) -> str | None:
        """Localiza o binário CLI do Docker no PATH ou nos diretórios padrões do Windows."""
        found = shutil.which("docker")
        if found:
            return found
        if os.name == "nt":
            candidates = [
                Path(r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"),
                Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe",
                Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe",
            ]
            for candidate in candidates:
                if candidate.is_file():
                    return str(candidate)
        return None

    def get_docker_desktop_executable(self) -> str | None:
        """Localiza o executável do Docker Desktop no Windows."""
        if os.name == "nt":
            candidates = [
                Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe"),
                Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Docker" / "Docker" / "Docker Desktop.exe",
                Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Docker" / "Docker" / "Docker Desktop.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Docker" / "Docker" / "Docker Desktop.exe",
            ]
            for candidate in candidates:
                if candidate.is_file():
                    return str(candidate)
        return None

    def is_installed(self) -> bool:
        """Retorna True se o Docker CLI ou Docker Desktop estiver presente no sistema."""
        return bool(self.get_docker_executable() or self.get_docker_desktop_executable())

    def is_running(self, timeout: float = 3.0) -> tuple[bool, str]:
        """Verifica se o daemon do Docker está ativo e respondendo a comandos.
        
        Retorna (True, mensagem_sucesso) ou (False, mensagem_erro).
        """
        docker_bin = self.get_docker_executable()
        if not docker_bin:
            return False, "Docker não foi encontrado no sistema. Instale o Docker Desktop."
        try:
            result = subprocess.run(
                [docker_bin, "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=self._creation_flags(),
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"Docker ativo (v{version})" if version else "Docker ativo e respondendo."
            detalhe = (result.stderr or result.stdout).strip()
            return False, detalhe or "O serviço do Docker não está em execução."
        except FileNotFoundError:
            return False, "Docker CLI não encontrado no caminho especificado."
        except subprocess.TimeoutExpired:
            return False, "O Docker demorou demais para responder à consulta de status."
        except Exception as error:
            return False, f"Falha ao consultar o Docker: {error}"

    def start_docker_service(
        self,
        progress_callback: Callable[[int, str], None] | None = None,
        timeout: int = 60,
    ) -> tuple[bool, str]:
        """Tenta abrir o Docker Desktop e iniciar o serviço, aguardando até estar pronto."""
        ok, msg = self.is_running(timeout=2.0)
        if ok:
            return True, "O Docker já está ativo e respondendo."

        desktop_exe = self.get_docker_desktop_executable()
        started_process = False

        if desktop_exe:
            try:
                flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
                subprocess.Popen([desktop_exe], creationflags=flags, close_fds=True)
                started_process = True
            except Exception:
                pass

        # No Windows, também tenta iniciar o serviço com.docker.service se possível
        if os.name == "nt":
            try:
                subprocess.run(
                    ["sc.exe", "start", "com.docker.service"],
                    capture_output=True,
                    timeout=5,
                    creationflags=self._creation_flags(),
                )
            except Exception:
                pass

        if not started_process and not self.is_installed():
            return False, "O Docker Desktop não foi encontrado neste computador. Instale o Docker Desktop para continuar."

        start_time = time.time()
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            if progress_callback:
                progress_callback(elapsed, f"Aguardando o serviço Docker inicializar... ({elapsed}s)")
            time.sleep(2.0)
            running, _ = self.is_running(timeout=2.0)
            if running:
                if progress_callback:
                    progress_callback(int(time.time() - start_time), "Docker iniciado com sucesso!")
                return True, "Docker iniciado com sucesso!"

        return False, (
            f"O Docker não respondeu após {timeout} segundos. "
            "Por favor, abra o Docker Desktop manualmente pelo Menu Iniciar e aguarde a inicialização da engine."
        )
