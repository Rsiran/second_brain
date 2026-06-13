"""CLI for the render tool."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from tools._common.report import Finding, Severity
from tools.render.validate import validate_bundle, validate_all_bundles
from tools.render.marp import render_marp


def _sibling_wiki(out_dir: Path) -> Path | None:
    """The wiki/ that sits beside an out/ directory, if it exists.

    Bundles live at <base>/out/<bundle>/, so the wiki for cross-checking
    sources_consulted is <base>/wiki/. Returns None when absent so the check
    stays a no-op rather than erroring.
    """
    candidate = out_dir.parent / "wiki"
    return candidate if candidate.is_dir() else None


def _render_findings_text(findings: list[Finding]) -> str:
    if not findings:
        return "render: OK (0 findings)\n"
    lines: list[str] = []
    errors = sum(1 for f in findings if f.severity == Severity.ERROR)
    warnings = sum(1 for f in findings if f.severity == Severity.WARNING)
    for f in findings:
        loc = f.file or "<bundle>"
        lines.append(f"{f.severity.value.upper():7} {loc}: {f.message}")
    lines.append(f"\nrender: {errors} errors, {warnings} warnings")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.render",
        description="Validate output bundles and render Marp slides.",
    )
    sub = parser.add_subparsers(dest="command")

    # validate subcommand
    val_parser = sub.add_parser("validate", help="Validate output bundle(s)")
    val_parser.add_argument(
        "path", nargs="?", default=None,
        help="bundle directory, or omit with --all to validate all bundles",
    )
    val_parser.add_argument(
        "--all", action="store_true", dest="validate_all",
        help="validate all bundles under the given directory (default: out/)",
    )
    val_parser.add_argument(
        "--wiki", default=None,
        help="wiki directory for cross-checking sources_consulted wikilinks "
             "(default: the bundle's sibling wiki/, if present)",
    )
    val_parser.add_argument("--json", action="store_true", help="emit JSON")

    # marp subcommand
    marp_parser = sub.add_parser("marp", help="Render slides.md to slides.html")
    marp_parser.add_argument("path", help="bundle directory")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "validate":
        explicit_wiki = Path(args.wiki) if args.wiki else None

        if args.validate_all:
            out_dir = Path(args.path) if args.path else Path("out")
            wiki_dir = explicit_wiki or _sibling_wiki(out_dir)
            findings = validate_all_bundles(out_dir, wiki_dir)
        elif args.path:
            bundle = Path(args.path)
            wiki_dir = explicit_wiki or _sibling_wiki(bundle.parent)
            findings = validate_bundle(bundle, wiki_dir)
        else:
            parser.error("provide a bundle path or use --all")
            return 1

        if args.json:
            print(json.dumps([f.to_dict() for f in findings], indent=2))
        else:
            print(_render_findings_text(findings), end="")

        return 1 if any(f.severity == Severity.ERROR for f in findings) else 0

    if args.command == "marp":
        success, message = render_marp(Path(args.path))
        print(message)
        return 0 if success else 1

    return 1
