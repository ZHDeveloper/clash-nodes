from __future__ import annotations

from urllib.parse import urlparse


def normalize_source_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return None

    if parsed.netloc == "raw.githubusercontent.com":
        return f"https://{parsed.netloc}{parsed.path}"

    if parsed.netloc != "github.com":
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 5 and parts[2] == "blob":
        owner, repo, _, ref = parts[:4]
        remainder = "/".join(parts[4:])
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{remainder}"

    if len(parts) >= 4 and parts[2] == "raw":
        owner, repo, _, ref = parts[:4]
        remainder = "/".join(parts[4:])
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{remainder}"

    return None
