"""Tests for the OKF CLI (tools.okf.cli)."""
from __future__ import annotations
import json
from pathlib import Path

import pytest

from tools.okf.cli import main
from tests.test_okf_export import make_wiki


def test_cli_export_returns_zero_and_prints_summary(tmp_path, capsys):
    wiki = make_wiki(tmp_path)
    rc = main(["export", "--wiki", str(wiki), "--out", str(tmp_path / "okf")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "okf: exported" in out
    assert (tmp_path / "okf" / "index.md").is_file()


def test_cli_export_json(tmp_path, capsys):
    wiki = make_wiki(tmp_path)
    rc = main(["export", "--wiki", str(wiki), "--out", str(tmp_path / "okf"), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["files_exported"] == 4
    assert payload["bundle_dir"].endswith("okf")


def test_cli_no_command_prints_help_and_returns_1(capsys):
    rc = main([])
    assert rc == 1
    assert "usage" in capsys.readouterr().out.lower()


def test_cli_missing_wiki_errors(tmp_path):
    # argparse error() exits with code 2
    with pytest.raises(SystemExit) as exc:
        main(["export", "--wiki", str(tmp_path / "nope"), "--out", str(tmp_path / "okf")])
    assert exc.value.code == 2
