"""Marp CLI integration: convert slides.md to slides.html."""
from __future__ import annotations
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def find_marp() -> str | None:
    """Return the path to the marp CLI, or None if not installed."""
    return shutil.which("marp")


def render_marp(bundle_dir: Path) -> tuple[bool, str]:
    """Convert slides.md to slides.html using the Marp CLI.

    Returns (success, message).
    """
    slides_path = bundle_dir / "slides.md"
    if not slides_path.is_file():
        return False, f"slides.md not found in {bundle_dir}"

    marp_bin = find_marp()
    if marp_bin is None:
        return False, (
            "marp CLI not found on PATH. Install it with:\n"
            "  npm install -g @marp-team/marp-cli\n"
            "Then re-run this command."
        )

    html_path = bundle_dir / "slides.html"
    try:
        result = subprocess.run(
            [marp_bin, str(slides_path), "--html", "--allow-local-files", "-o", str(html_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False, "marp CLI timed out after 60 seconds"

    if result.returncode != 0:
        return False, f"marp CLI failed (exit {result.returncode}):\n{result.stderr}"

    # Write render manifest
    manifest = {
        "rendered_at": datetime.now().isoformat(),
        "marp_bin": marp_bin,
        "command": [marp_bin, str(slides_path), "--html", "--allow-local-files", "-o", str(html_path)],
        "output": str(html_path),
    }
    (bundle_dir / "_render.json").write_text(json.dumps(manifest, indent=2) + "\n")

    return True, f"rendered {html_path}"
