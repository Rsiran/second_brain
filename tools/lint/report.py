"""Finding dataclass and report rendering."""
from __future__ import annotations
import json

from tools._common.report import Finding, Severity  # noqa: F401 — re-export


def render_text(findings: list[Finding]) -> str:
    if not findings:
        return "lint: OK (0 findings)\n"
    lines: list[str] = []
    by_sev = {Severity.ERROR: 0, Severity.WARNING: 0}
    for f in findings:
        by_sev[f.severity] += 1
        loc = f.file or "<base>"
        if f.line is not None:
            loc = f"{loc}:{f.line}"
        lines.append(f"{f.severity.value.upper():7} {loc}: {f.message}")
    summary = f"{by_sev[Severity.ERROR]} errors, {by_sev[Severity.WARNING]} warnings"
    lines.append(f"\nlint: {summary}")
    return "\n".join(lines) + "\n"


def render_json(findings: list[Finding]) -> str:
    return json.dumps([f.to_dict() for f in findings], indent=2)
