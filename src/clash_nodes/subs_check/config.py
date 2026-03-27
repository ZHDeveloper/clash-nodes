from __future__ import annotations

from pathlib import Path

DEFAULT_MIHOMO_OVERWRITE_URL = (
    "https://raw.githubusercontent.com/beck-8/override-hub/refs/heads/main/yaml/ACL4SSR_Online_Full.yaml"
)


def build_subs_check_config(source_urls: list[str], output_dir: Path, work_dir: Path) -> dict[str, object]:
    try:
        configured_output_dir = output_dir.relative_to(work_dir)
    except ValueError:
        configured_output_dir = output_dir

    return {
        "print-progress": True,
        "concurrent": 50,
        "check-interval": 60,
        "timeout": 1000,
        "alive-test-url": "http://gstatic.com/generate_204",
        "speed-test-url": "https://github.com/AaronFeng753/Waifu2x-Extension-GUI/releases/download/v2.21.12/Waifu2x-Extension-GUI-v2.21.12-Portable.7z",
        "min-speed": 1024,
        "download-timeout": 2,
        "download-mb": 20,
        "rename-node": True,
        "media-check": False,
        "save-method": "local",
        "output-dir": str(configured_output_dir),
        "enable-web-ui": False,
        "sub-store-port": ":8299",
        "sub-store-path": "",
        "mihomo-overwrite-url": DEFAULT_MIHOMO_OVERWRITE_URL,
        "sub-urls-retry": 2,
        "sub-urls-get-ua": "clash.meta (https://github.com/beck-8/subs-check)",
        "success-rate": 0,
        "sub-urls": source_urls,
    }
