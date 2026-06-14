"""CLI for the OKF bridge."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from tools._common.report import Severity
from tools.okf.export import export_okf


def _summary_text(result) -> str:
    lines = [
        f"okf: exported {result.files_exported} files, "
        f"{result.indexes_generated} index.md, "
        f"{result.links_rewritten} links rewritten -> {result.bundle_dir}",
    ]
    if result.unresolved:
        lines.append(f"  {len(result.unresolved)} unresolved link(s):")
        for f, slug in result.unresolved:
            lines.append(f"    {f}: [[{slug}]]")
    for finding in result.findings:
        lines.append(f"  {finding.severity.value.upper()} {finding.file}: {finding.message}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.okf",
        description="Export the wiki/ vault as an Open Knowledge Format (OKF) bundle.",
    )
    sub = parser.add_subparsers(dest="command")

    exp = sub.add_parser("export", help="Export wiki/ to an OKF bundle")
    exp.add_argument("--wiki", default="wiki", help="wiki directory to export (default: wiki)")
    exp.add_argument("--out", default="out/okf", help="output bundle directory (default: out/okf)")
    exp.add_argument(
        "--no-clean", action="store_true",
        help="do not wipe the output directory before exporting",
    )
    exp.add_argument("--json", action="store_true", help="emit JSON")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "export":
        try:
            result = export_okf(Path(args.wiki), Path(args.out), clean=not args.no_clean)
        except (NotADirectoryError, ValueError) as e:
            parser.error(str(e))
            return 1
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(_summary_text(result), end="")
        # Warnings don't fail the run; the export is best-effort and lossless.
        has_error = any(f.severity == Severity.ERROR for f in result.findings)
        return 1 if has_error else 0

    return 1
