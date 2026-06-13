from __future__ import annotations
import argparse
import sys
from pathlib import Path

from tools.lint.loader import load_base
from tools.lint.checks import (
    check_sources_mirror_raw,
    check_source_paths_exist,
    check_frontmatter_schemas,
    check_wikilinks_resolve,
    check_duplicate_slugs,
    check_orphan_sources,
    check_ungrounded_articles,
    check_dates_sane,
)
from tools.lint.report import Finding, Severity, render_text, render_json


ALL_CHECKS = [
    check_sources_mirror_raw,
    check_source_paths_exist,
    check_frontmatter_schemas,
    check_wikilinks_resolve,
    check_duplicate_slugs,
    check_orphan_sources,
    check_ungrounded_articles,
    check_dates_sane,
]


def run_lint(path: Path) -> list[Finding]:
    base = load_base(path)
    findings: list[Finding] = []
    for check in ALL_CHECKS:
        findings.extend(check(base))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.lint",
        description="Health-check a knowledge base against the CLAUDE.md contract.",
    )
    parser.add_argument("path", nargs="?", default=".", help="base directory (default: .)")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    findings = run_lint(Path(args.path))
    if args.json:
        print(render_json(findings))
    else:
        print(render_text(findings), end="")

    # Exit non-zero if any ERROR.
    return 1 if any(f.severity == Severity.ERROR for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
