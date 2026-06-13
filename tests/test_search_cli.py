import subprocess
import sys
from pathlib import Path

FIXTURE = Path("tests/fixtures/tiny_base")


def _run(args):
    return subprocess.run(
        [sys.executable, "-m", "tools.search", *args],
        capture_output=True, text=True,
    )


def test_cli_index_then_query(tmp_path):
    index_path = tmp_path / "search-index.json"
    r = _run(["index", "--base", str(FIXTURE), "--index", str(index_path)])
    assert r.returncode == 0, r.stderr
    assert index_path.exists()

    r = _run(["query", "foo", "--index", str(index_path)])
    assert r.returncode == 0, r.stderr
    assert "foo" in r.stdout
