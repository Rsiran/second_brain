import json
import subprocess
import sys


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "tools.ingest"] + args,
        capture_output=True,
        text=True,
    )


def test_status_empty_base(tmp_path):
    result = _run(["status", str(tmp_path)])
    assert result.returncode == 0
    assert "nothing to do" in result.stdout


def test_status_mini_base():
    result = _run(["status", "examples/mini-base"])
    assert result.returncode == 0
    assert "0 new" in result.stdout
    assert "0 orphaned" in result.stdout


def test_status_json():
    result = _run(["status", "examples/mini-base", "--json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert isinstance(data["new"], list)
    assert isinstance(data["modified"], list)
    assert isinstance(data["orphaned"], list)
    assert "summary" in data


def test_no_subcommand_shows_help():
    result = _run([])
    assert result.returncode == 1
