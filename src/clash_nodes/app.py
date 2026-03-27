from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from clash_nodes.constants import (
    DISCOVERED_SOURCES_PATH,
    EXPECTED_OUTPUT_FILES,
    SOURCE_ALLOWLIST_PATH,
    SOURCE_BLOCKLIST_PATH,
    STATS_PATH,
)
from clash_nodes.github_search.client import GitHubClient, GitHubClientError
from clash_nodes.github_search.extractors import (
    extract_github_readme_urls,
    extract_tree_subscription_candidates,
)
from clash_nodes.pipeline.sources import normalize_source_url
from clash_nodes.pipeline.storage import read_json, read_line_set, write_json
from clash_nodes.subs_check.runner import SubsCheckRunner


@dataclass
class SourceRecord:
    url: str
    repository: str
    path: str
    discovered_via: str
    default_branch: str
    updated_at: str


def discover_sources(base_dir: Path, github_client: GitHubClient | object | None = None) -> dict[str, int | str]:
    github_client = github_client or GitHubClient.from_env()
    allowlist = read_line_set(base_dir / SOURCE_ALLOWLIST_PATH)
    blocklist = read_line_set(base_dir / SOURCE_BLOCKLIST_PATH)

    repositories = github_client.search_repositories()
    found_sources: list[SourceRecord] = []
    seen_urls: set[str] = set()

    for repo in repositories:
        try:
            tree_paths = github_client.get_repository_tree(
                repo["owner"], repo["name"], repo["default_branch"]
            )
        except GitHubClientError:
            continue
        for candidate in extract_tree_subscription_candidates(
            owner=repo["owner"],
            repo=repo["name"],
            ref=repo["default_branch"],
            tree_paths=tree_paths,
        ):
            _append_source(
                found_sources,
                seen_urls,
                allowlist,
                blocklist,
                repo,
                url=candidate["url"],
                path=candidate["path"],
                discovered_via="repo_tree",
            )

        try:
            readme = github_client.get_readme(repo["owner"], repo["name"])
        except GitHubClientError:
            readme = ""
        for url in extract_github_readme_urls(readme):
            path = _path_from_raw_url(url)
            _append_source(
                found_sources,
                seen_urls,
                allowlist,
                blocklist,
                repo,
                url=url,
                path=path,
                discovered_via="readme",
            )

    write_json(
        base_dir / DISCOVERED_SOURCES_PATH,
        {
            "sources": [asdict(item) for item in found_sources],
        },
    )
    return {
        "status": "ok",
        "repo_count": len(repositories),
        "candidate_source_count": len(found_sources),
    }


def build_outputs(base_dir: Path, subs_check_runner: SubsCheckRunner | object | None = None) -> dict[str, object]:
    subs_check_runner = subs_check_runner or SubsCheckRunner()
    source_payload = read_json(base_dir / DISCOVERED_SOURCES_PATH, default={"sources": []})
    source_urls = [item["url"] for item in source_payload.get("sources", [])]
    output_dir = base_dir / "output"

    if not source_urls:
        stats = {"status": "no_sources", "candidate_source_count": 0, "generated_files": []}
        write_json(base_dir / STATS_PATH, stats)
        return stats

    result = subs_check_runner.run(source_urls=source_urls, output_dir=output_dir, work_dir=base_dir)
    generated_files = sorted(name for name in EXPECTED_OUTPUT_FILES if (output_dir / name).exists())
    stats = {
        "status": "ok",
        "candidate_source_count": len(source_urls),
        "generated_files": generated_files,
    }
    write_json(base_dir / STATS_PATH, stats)
    return {"status": "ok", "generated_files": generated_files, "runner": result}


def run_pipeline(
    base_dir: Path,
    github_client: GitHubClient | object | None = None,
    subs_check_runner: SubsCheckRunner | object | None = None,
) -> dict[str, object]:
    discover_result = discover_sources(base_dir=base_dir, github_client=github_client)
    if int(discover_result["candidate_source_count"]) == 0:
        stats = {"status": "no_sources", "candidate_source_count": 0, "generated_files": []}
        write_json(base_dir / STATS_PATH, stats)
        return stats
    return build_outputs(base_dir=base_dir, subs_check_runner=subs_check_runner)


def _append_source(
    found_sources: list[SourceRecord],
    seen_urls: set[str],
    allowlist: set[str],
    blocklist: set[str],
    repo: dict[str, str],
    *,
    url: str,
    path: str,
    discovered_via: str,
) -> None:
    normalized = normalize_source_url(url)
    if not normalized or normalized in seen_urls:
        return
    if blocklist and (normalized in blocklist or repo["full_name"] in blocklist):
        return
    if allowlist and normalized not in allowlist and repo["full_name"] not in allowlist:
        return

    seen_urls.add(normalized)
    found_sources.append(
        SourceRecord(
            url=normalized,
            repository=repo["full_name"],
            path=path,
            discovered_via=discovered_via,
            default_branch=repo["default_branch"],
            updated_at=repo["updated_at"],
        )
    )


def _path_from_raw_url(url: str) -> str:
    parts = url.split("/", 6)
    return parts[6] if len(parts) > 6 else ""
