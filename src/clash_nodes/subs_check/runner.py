from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from clash_nodes.constants import EXPECTED_OUTPUT_FILES, SUBS_CHECK_CONFIG_PATH
from clash_nodes.subs_check.config import build_subs_check_config


class SubsCheckError(RuntimeError):
    """Raised when subs-check execution fails."""


@dataclass
class SubsCheckRunner:
    image: str = "ghcr.io/beck-8/subs-check:latest"

    def run(self, source_urls: list[str], output_dir: Path, work_dir: Path) -> dict[str, object]:
        if shutil.which("docker") is None:
            raise SubsCheckError("docker is required")

        config_path = work_dir / SUBS_CHECK_CONFIG_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            yaml.safe_dump(
                build_subs_check_config(source_urls=source_urls, output_dir=output_dir),
                sort_keys=False,
                allow_unicode=True,
            )
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        command = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{work_dir}:/workspace",
            "-w",
            "/workspace",
            self.image,
            "/app/subs-check",
            "-f",
            f"/workspace/{SUBS_CHECK_CONFIG_PATH}",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise SubsCheckError(result.stderr or result.stdout or "subs-check failed")

        missing = [name for name in EXPECTED_OUTPUT_FILES if not (output_dir / name).exists()]
        if missing:
            raise SubsCheckError(f"subs-check finished without expected files: {', '.join(missing)}")

        return {
            "returncode": result.returncode,
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
