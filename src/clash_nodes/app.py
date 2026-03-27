from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
import re

from clash_nodes.constants import (
    DATED_SOURCE_MAX_AGE_DAYS,
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


def _log(message: str) -> None:
    print(f"[clash-nodes] {message}", flush=True)


@dataclass
class SourceRecord:
    url: str
    repository: str
    path: str
    discovered_via: str
    default_branch: str
    updated_at: str


DATE_TOKEN_PATTERNS = (
    re.compile(r"(?P<full_ymd>20\d{2}\d{2}\d{2})"),
    re.compile(r"(?P<y>20\d{2})[-_/](?P<m>\d{2})[-_/](?P<d>\d{2})"),
)


def discover_sources(
    base_dir: Path,
    github_client: GitHubClient | object | None = None,
    today: date | None = None,
) -> dict[str, int | str]:
    github_client = github_client or GitHubClient.from_env()
    allowlist = read_line_set(base_dir / SOURCE_ALLOWLIST_PATH)
    blocklist = read_line_set(base_dir / SOURCE_BLOCKLIST_PATH)
    today = today or datetime.now(UTC).date()

    _log(f"discovering sources in {base_dir}")
    repositories = github_client.search_repositories()
    _log(f"found {len(repositories)} candidate repositories")
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
                today=today,
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
                today=today,
            )

    write_json(
        base_dir / DISCOVERED_SOURCES_PATH,
        {
            "sources": [asdict(item) for item in found_sources],
        },
    )
    _log(f"saved {len(found_sources)} subscription sources to {DISCOVERED_SOURCES_PATH}")
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
        _log("no subscription sources found; skipping output generation")
        return stats

    _log(f"building outputs from {len(source_urls)} sources into {output_dir}")
    result = subs_check_runner.run(source_urls=source_urls, output_dir=output_dir, work_dir=base_dir)
    generated_files = sorted(name for name in EXPECTED_OUTPUT_FILES if (output_dir / name).exists())
    stats = {
        "status": "ok",
        "candidate_source_count": len(source_urls),
        "generated_files": generated_files,
    }
    write_json(base_dir / STATS_PATH, stats)
    _log(f"generated files: {', '.join(generated_files)}")
    return {"status": "ok", "generated_files": generated_files, "runner": result}


def run_pipeline(
    base_dir: Path,
    github_client: GitHubClient | object | None = None,
    subs_check_runner: SubsCheckRunner | object | None = None,
) -> dict[str, object]:
    _log("pipeline started")
    discover_result = discover_sources(base_dir=base_dir, github_client=github_client)
    if int(discover_result["candidate_source_count"]) == 0:
        stats = {"status": "no_sources", "candidate_source_count": 0, "generated_files": []}
        write_json(base_dir / STATS_PATH, stats)
        _log("pipeline finished without sources")
        return stats
    result = build_outputs(base_dir=base_dir, subs_check_runner=subs_check_runner)
    _log(f"pipeline finished with status={result['status']}")
    return result


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
    today: date,
) -> None:
    normalized = normalize_source_url(url)
    if not normalized or normalized in seen_urls:
        return
    if _is_stale_dated_path(path, today=today):
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


def _is_stale_dated_path(path: str, *, today: date) -> bool:
    dated_value = _extract_date_from_path(path)
    if dated_value is None:
        return False
    age_days = (today - dated_value).days
    return age_days >= DATED_SOURCE_MAX_AGE_DAYS


def _extract_date_from_path(path: str) -> date | None:
    for pattern in DATE_TOKEN_PATTERNS:
        match = pattern.search(path)
        if not match:
            continue
        groups = match.groupdict()
        if groups.get("full_ymd"):
            ymd = groups["full_ymd"]
            year = int(ymd[:4])
            month = int(ymd[4:6])
            day = int(ymd[6:8])
        else:
            year = int(groups["y"])
            month = int(groups["m"])
            day = int(groups["d"])
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None
