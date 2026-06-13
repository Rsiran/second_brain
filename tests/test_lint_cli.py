import subprocess
import sys
from pathlib import Path

FIXTURE = Path("tests/fixtures/tiny_base")


def _run(args, **kw):
    return subprocess.run(
        [sys.executable, "-m", "tools.lint", *args],
        capture_output=True, text=True, **kw
    )


def test_cli_tiny_base_passes():
    r = _run([str(FIXTURE)])
    assert r.returncode == 0, f"stderr: {r.stderr}\nstdout: {r.stdout}"
    assert "OK" in r.stdout or "0 errors" in r.stdout


def test_cli_json_mode():
    r = _run([str(FIXTURE), "--json"])
    assert r.returncode == 0
    import json
    parsed = json.loads(r.stdout)
    assert isinstance(parsed, list)


def test_cli_errors_exit_nonzero(tmp_path):
    (tmp_path / "wiki" / "articles").mkdir(parents=True)
    (tmp_path / "wiki" / "articles" / "broken.md").write_text("no frontmatter at all\n")
    r = _run([str(tmp_path)])
    assert r.returncode != 0
