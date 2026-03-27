from __future__ import annotations

import re
from typing import Iterable

from clash_nodes.pipeline.sources import normalize_source_url

README_URL_RE = re.compile(r"https?://[^\s)>\"]+")

SUBSCRIPTION_PATTERNS = (
    re.compile(r"(^|/)(clash[^/]*|proxy[^/]*|nodes?[^/]*)\.(yml|txt)$", re.IGNORECASE),
    re.compile(r"\.(yml|txt)$", re.IGNORECASE),
)


def extract_github_readme_urls(readme_text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for match in README_URL_RE.findall(readme_text):
        normalized = normalize_source_url(match)
        if normalized and normalized not in seen:
            seen.add(normalized)
            urls.append(normalized)
    return urls


def extract_tree_subscription_candidates(
    owner: str,
    repo: str,
    ref: str,
    tree_paths: Iterable[str],
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for path in tree_paths:
        if not _looks_like_subscription_path(path):
            continue
        candidates.append(
            {
                "path": path,
                "url": f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}",
                "source": "repo_tree",
            }
        )
    return candidates


def _looks_like_subscription_path(path: str) -> bool:
    normalized = path.strip("/")
    if not normalized or normalized.lower().endswith(".md"):
        return False
    return any(pattern.search(normalized) for pattern in SUBSCRIPTION_PATTERNS)
