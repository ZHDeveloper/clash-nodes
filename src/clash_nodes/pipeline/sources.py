from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import urlparse

ALLOWED_SOURCE_SUFFIXES = {".txt", ".yml"}


def normalize_source_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return None
    normalized_path = parsed.path

    if parsed.netloc == "raw.githubusercontent.com":
        normalized_url = f"https://{parsed.netloc}{normalized_path}"
        return normalized_url if _has_allowed_source_suffix(normalized_path) else None

    if parsed.netloc != "github.com":
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 5 and parts[2] == "blob":
        owner, repo, _, ref = parts[:4]
        remainder = "/".join(parts[4:])
        normalized_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{remainder}"
        return normalized_url if _has_allowed_source_suffix(remainder) else None

    if len(parts) >= 4 and parts[2] == "raw":
        owner, repo, _, ref = parts[:4]
        remainder = "/".join(parts[4:])
        normalized_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{remainder}"
        return normalized_url if _has_allowed_source_suffix(remainder) else None

    return None


def _has_allowed_source_suffix(path: str) -> bool:
    return PurePosixPath(path).suffix.lower() in ALLOWED_SOURCE_SUFFIXES
