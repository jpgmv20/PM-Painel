"""Consulta e prepara instaladores publicados nas Releases do GitHub."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class UpdateService:
    """Verifica canais públicos e só prepara instaladores com SHA-256 publicado."""

    OWNER = "jpgmv20"
    REPOSITORY = "PM-Painel"
    CURRENT_VERSION = "0.0.1"
    API_ROOT = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}"

    def __init__(self, data_dir: str | Path, project_dir: str | Path | None = None) -> None:
        self.download_dir = Path(data_dir) / "updates"
        self.pending_file = self.download_dir / "pending-installer.json"
        self.project_dir = Path(project_dir).resolve() if project_dir else None

    def check(self, channel: str) -> dict[str, Any]:
        normalized = channel.casefold()
        if normalized in {"desenvolvimento", "development"}:
            commit = self._get_json(f"{self.API_ROOT}/commits/main")
            commit_sha = str(commit.get("sha", ""))
            version = commit_sha[:12]
            current_sha = self._local_dev_commit()
            available = bool(commit_sha) and (current_sha is None or current_sha != commit_sha)
            return {
                "channel": channel,
                "version": version,
                "available": available,
                "asset": None,
                "url": commit.get("html_url", f"https://github.com/{self.OWNER}/{self.REPOSITORY}/commits/main"),
                "message": (
                    f"Nova versão de desenvolvimento disponível: {version}."
                    if available else f"O canal de desenvolvimento está atualizado ({version})."
                ),
            }

        releases = self._get_json(f"{self.API_ROOT}/releases?per_page=50")
        if not isinstance(releases, list):
            raise RuntimeError("O GitHub retornou uma lista de versões inválida.")
        prerelease = normalized == "beta"
        release = next(
            (item for item in releases if bool(item.get("prerelease")) == prerelease),
            None,
        )
        if release is None:
            label = "beta" if prerelease else "estável"
            return {
                "channel": channel,
                "available": False,
                "asset": None,
                "url": f"https://github.com/{self.OWNER}/{self.REPOSITORY}/releases",
                "message": f"Nenhuma versão {label} foi publicada ainda.",
            }

        version = str(release.get("tag_name") or release.get("name") or "").strip()
        available = self._version_key(version) > self._version_key(self.CURRENT_VERSION)
        asset = self._installer_asset(release.get("assets") or []) if available else None
        if available:
            message = f"Atualização {version} disponível."
            if asset is None:
                message += " A versão não inclui um instalador verificável para download automático."
        else:
            message = f"O PM-Painel está atualizado ({version or self.CURRENT_VERSION})."
        return {
            "channel": channel,
            "version": version,
            "available": available,
            "asset": asset,
            "url": release.get("html_url", f"https://github.com/{self.OWNER}/{self.REPOSITORY}/releases"),
            "message": message,
        }

    def download(self, update: dict[str, Any]) -> Path:
        asset = update.get("asset")
        if not asset:
            raise RuntimeError("Esta versão não tem um instalador automático verificável.")
        digest = str(asset.get("digest") or "")
        if not digest.startswith("sha256:"):
            raise RuntimeError("O GitHub não publicou o SHA-256 deste instalador; o download automático foi bloqueado.")

        filename = Path(str(asset.get("name", ""))).name
        suffix = Path(filename).suffix.casefold()
        if suffix not in {".exe", ".msi"}:
            raise RuntimeError("O arquivo publicado não é um instalador Windows (.exe ou .msi).")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        destination = self.download_dir / filename
        temporary = destination.with_suffix(destination.suffix + ".download")
        request = Request(
            str(asset["browser_download_url"]),
            headers={"User-Agent": "PM-Painel-Updater", "Accept": "application/octet-stream"},
        )
        try:
            with urlopen(request, timeout=30) as response, temporary.open("wb") as output:
                total = 0
                digest_actual = hashlib.sha256()
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > 1024 * 1024 * 1024:
                        raise RuntimeError("O instalador excede o limite de 1 GB.")
                    output.write(chunk)
                    digest_actual.update(chunk)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

        expected = digest.partition(":")[2].casefold()
        if digest_actual.hexdigest().casefold() != expected:
            temporary.unlink(missing_ok=True)
            raise RuntimeError("A verificação SHA-256 do instalador falhou.")
        temporary.replace(destination)
        manifest = {
            "path": str(destination),
            "sha256": expected,
            "version": update.get("version", ""),
            "url": update.get("url", ""),
        }
        self.pending_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return destination

    def launch_pending_installer(self) -> bool:
        """Abre o instalador verificado uma vez antes de iniciar a interface."""
        if os.name != "nt":
            return False
        try:
            manifest = json.loads(self.pending_file.read_text(encoding="utf-8"))
            path = Path(manifest["path"]).resolve(strict=True)
            root = self.download_dir.resolve()
            path.relative_to(root)
            digest = str(manifest["sha256"])
            suffix = path.suffix.casefold()
            if suffix not in {".exe", ".msi"} or self._sha256_file(path) != digest:
                raise ValueError("O instalador pendente não passou na verificação de integridade.")
            self.pending_file.unlink(missing_ok=True)
            if suffix == ".msi":
                command = ["msiexec.exe", "/i", str(path)]
            else:
                command = [str(path)]
            flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            subprocess.Popen(command, cwd=str(path.parent), creationflags=flags, shell=False)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            self.pending_file.unlink(missing_ok=True)
            return False

    @staticmethod
    def _get_json(url: str) -> Any:
        request = Request(
            url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "PM-Painel"},
        )
        try:
            with urlopen(request, timeout=12) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 404:
                raise RuntimeError("O repositório ainda não publicou versões neste canal.") from error
            raise RuntimeError(f"O GitHub respondeu com erro HTTP {error.code}.") from error
        except URLError as error:
            raise RuntimeError("Não foi possível acessar o GitHub. Confira a conexão.") from error
        except TimeoutError as error:
            raise RuntimeError("A consulta ao GitHub excedeu o tempo limite.") from error

    @staticmethod
    def _installer_asset(assets: list[dict[str, Any]]) -> dict[str, Any] | None:
        candidates = [
            asset for asset in assets
            if Path(str(asset.get("name", ""))).suffix.casefold() in {".exe", ".msi"}
            and asset.get("browser_download_url")
            and str(asset.get("digest") or "").startswith("sha256:")
        ]
        return next(
            (asset for asset in candidates if "setup" in str(asset.get("name", "")).casefold()),
            candidates[0] if candidates else None,
        )

    @staticmethod
    def _version_key(version: str) -> tuple[int, ...]:
        numbers = re.findall(r"\d+", version)
        return tuple(int(number) for number in numbers[:4]) or (0,)

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _local_dev_commit(self) -> str | None:
        if self.project_dir is None or not (self.project_dir / ".git").exists():
            return None
        try:
            result = subprocess.run(
                ["git", f"-c", f"safe.directory={self.project_dir}", "-C", str(self.project_dir), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=3,
                check=True,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return result.stdout.strip()
