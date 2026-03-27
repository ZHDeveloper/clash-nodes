from __future__ import annotations

from pathlib import Path


def build_subs_check_config(source_urls: list[str], output_dir: Path) -> dict[str, object]:
    return {
        "print-progress": True,
        "concurrent": 20,
        "check-interval": 1440,
        "timeout": 5000,
        "alive-test-url": "http://gstatic.com/generate_204",
        "speed-test-url": "https://github.com/AaronFeng753/Waifu2x-Extension-GUI/releases/download/v2.21.12/Waifu2x-Extension-GUI-v2.21.12-Portable.7z",
        "min-speed": 0,
        "download-timeout": 5,
        "download-mb": 10,
        "rename-node": True,
        "media-check": False,
        "save-method": "local",
        "output-dir": str(output_dir),
        "enable-web-ui": False,
        "sub-store-port": ":8299",
        "sub-store-path": "",
        "sub-urls-retry": 2,
        "sub-urls-get-ua": "clash.meta (https://github.com/beck-8/subs-check)",
        "success-rate": 0,
        "sub-urls": source_urls,
    }
