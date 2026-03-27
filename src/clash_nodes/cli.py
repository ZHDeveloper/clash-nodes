from __future__ import annotations

import argparse
import sys
from pathlib import Path

from clash_nodes.app import build_outputs, discover_sources, run_pipeline
from clash_nodes.github_search.client import GitHubClientError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="clash-nodes")
    parser.add_argument("command", choices=["discover", "build", "run"], nargs="?", default="run")
    parser.add_argument("--base-dir", default=".")
    parsed = parser.parse_args(argv)
    base_dir = Path(parsed.base_dir).resolve()

    try:
        if parsed.command == "discover":
            result = discover_sources(base_dir=base_dir)
        elif parsed.command == "build":
            result = build_outputs(base_dir=base_dir)
        else:
            result = run_pipeline(base_dir=base_dir)
    except GitHubClientError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
