import json
import subprocess
import sys


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "tools.render"] + args,
        capture_output=True,
        text=True,
    )


def test_no_subcommand_shows_help():
    result = _run([])
    assert result.returncode == 1


def test_validate_mini_base_example():
    result = _run(["validate", "examples/mini-base/out/2026-04-01-attention-mechanisms-compared"])
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_validate_json():
    result = _run(["validate", "examples/mini-base/out/2026-04-01-attention-mechanisms-compared", "--json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)


def test_validate_all_mini_base():
    result = _run(["validate", "--all", "examples/mini-base/out"])
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_validate_nonexistent_bundle():
    result = _run(["validate", "nonexistent/path"])
    assert result.returncode == 1
