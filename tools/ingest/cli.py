"""CLI for the ingest diff tool."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from tools.ingest.diff import compute_ingest_diff, IngestDiff


def _render_text(diff: IngestDiff) -> str:
    if diff.total == 0:
        return "ingest: nothing to do (wiki/sources/ is in sync with raw/)\n"

    lines: list[str] = []

    if diff.new:
        lines.append(f"NEW ({len(diff.new)}):")
        for item in diff.new:
            lines.append(f"  + {item.raw_path}  ->  wiki/sources/{item.raw_type}/{item.slug}.md")

    if diff.modified:
        if lines:
            lines.append("")
        lines.append(f"MODIFIED ({len(diff.modified)}):")
        for item in diff.modified:
            lines.append(f"  ~ {item.raw_path}  (ingested: {item.ingested})")

    if diff.orphaned:
        if lines:
            lines.append("")
        lines.append(f"ORPHANED ({len(diff.orphaned)}):")
        for item in diff.orphaned:
            lines.append(f"  - {item.source_path}  (missing: {item.missing_raw})")

    lines.append(f"\ningest: {diff.summary}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.ingest",
        description="Show pending ingest work: new, modified, and orphaned items.",
    )
    sub = parser.add_subparsers(dest="command")
    status_parser = sub.add_parser("status", help="Show ingest status")
    status_parser.add_argument(
        "path", nargs="?", default=".", help="base directory (default: .)"
    )
    status_parser.add_argument("--json", action="store_true", help="emit JSON")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    diff = compute_ingest_diff(Path(args.path))

    if args.json:
        print(json.dumps(diff.to_dict(), indent=2))
    else:
        print(_render_text(diff), end="")

    return 0
