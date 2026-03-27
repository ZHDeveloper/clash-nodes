from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from clash_nodes.constants import build_search_queries


class GitHubClientError(RuntimeError):
    """Raised when the GitHub API returns an unexpected response."""


@dataclass
class GitHubClient:
    token: str
    api_base_url: str = "https://api.github.com"
    raw_base_url: str = "https://raw.githubusercontent.com"
    timeout_seconds: int = 15
    transport_retries: int = 3

    @classmethod
    def from_env(cls) -> "GitHubClient":
        token = os.environ.get("GH_TOKEN")
        if not token:
            raise GitHubClientError("GH_TOKEN is required")
        return cls(token=token)

    def search_repositories(self) -> list[dict[str, Any]]:
        repositories: dict[str, dict[str, Any]] = {}
        for query in build_search_queries():
            payload = self._get_json(
                f"/search/repositories?q={quote(query)}&sort=updated&order=desc&per_page=10"
            )
            for item in payload.get("items", []):
                full_name = item["full_name"]
                repositories[full_name] = {
                    "full_name": full_name,
                    "owner": item["owner"]["login"],
                    "name": item["name"],
                    "default_branch": item["default_branch"],
                    "description": item.get("description") or "",
                    "updated_at": item["updated_at"],
                }
        return list(repositories.values())

    def get_repository_tree(self, owner: str, repo: str, ref: str) -> list[str]:
        payload = self._get_json(f"/repos/{owner}/{repo}/git/trees/{quote(ref)}?recursive=1")
        return [item["path"] for item in payload.get("tree", []) if item.get("type") == "blob"]

    def get_readme(self, owner: str, repo: str) -> str:
        try:
            payload = self._get_json(f"/repos/{owner}/{repo}/readme")
        except GitHubClientError as exc:
            if "404" in str(exc):
                return ""
            raise

        content = payload.get("content", "")
        if not content:
            return ""
        return base64.b64decode(content).decode("utf-8", errors="ignore")

    def _get_json(self, path: str) -> dict[str, Any]:
        request = Request(
            f"{self.api_base_url}{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "clash-nodes",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        last_transport_error: URLError | None = None
        for attempt in range(1, self.transport_retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="ignore")
                raise GitHubClientError(f"GitHub API error {exc.code}: {body}") from exc
            except URLError as exc:
                last_transport_error = exc
                if attempt == self.transport_retries:
                    break
                time.sleep(0.5 * attempt)

        assert last_transport_error is not None
        raise GitHubClientError(
            f"GitHub API transport error: {last_transport_error.reason}"
        ) from last_transport_error
