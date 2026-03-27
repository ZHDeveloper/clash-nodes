from __future__ import annotations

from datetime import UTC, datetime, timedelta


def build_search_queries() -> list[str]:
    since = (datetime.now(UTC) - timedelta(days=30)).date().isoformat()
    return [
        f"clash free nodes pushed:>={since}",
        f"clash 订阅 pushed:>={since}",
        f"节点 订阅 pushed:>={since}",
        f"mihomo free nodes pushed:>={since}",
        f"v2ray free nodes pushed:>={since}",
    ]

SOURCE_ALLOWLIST_PATH = "config/allowlist.txt"
SOURCE_BLOCKLIST_PATH = "config/blocklist.txt"
DISCOVERED_SOURCES_PATH = "data/sources.json"
STATS_PATH = "data/stats.json"
SUBS_CHECK_CONFIG_PATH = "data/subs-check.yaml"

EXPECTED_OUTPUT_FILES = ["all.yaml", "base64.txt"]
DATED_SOURCE_MAX_AGE_DAYS = 7
