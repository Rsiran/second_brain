from pathlib import Path

from tools._common.report import Severity
from tools.render.validate import validate_bundle, validate_all_bundles


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


VALID_FM = (
    "---\ntitle: Test\ntype: output\nquery: \"What?\"\n"
    "created: 2026-04-01\nformat: report\ntags: [test]\n---\nBody.\n"
)


def test_valid_bundle(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    _write(bundle / "index.md", VALID_FM)
    _write(bundle / "index.html", "<!DOCTYPE html><html><body>Body.</body></html>")
    findings = validate_bundle(bundle)
    assert findings == []


def test_missing_index(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    bundle.mkdir(parents=True)
    findings = validate_bundle(bundle)
    assert any(f.severity == Severity.ERROR and "missing" in f.message for f in findings)


def test_bad_frontmatter(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    _write(bundle / "index.md", "no frontmatter here\n")
    findings = validate_bundle(bundle)
    assert any(f.severity == Severity.ERROR for f in findings)


def test_missing_required_fields(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    _write(bundle / "index.md", "---\ntitle: X\ntype: output\n---\nBody.\n")
    findings = validate_bundle(bundle)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    # Should catch missing: query, created, format, tags
    assert len(errors) >= 3


def test_invalid_format_enum(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    fm = VALID_FM.replace("format: report", "format: invalid")
    _write(bundle / "index.md", fm)
    findings = validate_bundle(bundle)
    assert any("format" in f.message for f in findings)


def test_invalid_date(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    fm = VALID_FM.replace("created: 2026-04-01", "created: not-a-date")
    _write(bundle / "index.md", fm)
    findings = validate_bundle(bundle)
    assert any("created" in f.message for f in findings)


def test_bad_dir_name_warning(tmp_path):
    bundle = tmp_path / "bad-name"
    _write(bundle / "index.md", VALID_FM)
    findings = validate_bundle(bundle)
    assert any(f.severity == Severity.WARNING and "pattern" in f.message for f in findings)


def test_slides_missing_marp_warning(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    _write(bundle / "index.md", VALID_FM)
    _write(bundle / "slides.md", "---\ntitle: No marp\n---\nSlide content\n")
    findings = validate_bundle(bundle)
    assert any(f.severity == Severity.WARNING and "marp" in f.message for f in findings)


def test_slides_with_marp_ok(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    _write(bundle / "index.md", VALID_FM)
    _write(bundle / "slides.md", "---\nmarp: true\ntitle: Good\n---\nSlide\n")
    findings = validate_bundle(bundle)
    assert not any("marp" in f.message for f in findings)


def test_orphan_py_script_warning(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    _write(bundle / "index.md", VALID_FM)
    _write(bundle / "assets" / "chart.py", "import matplotlib\n")
    findings = validate_bundle(bundle)
    assert any(f.severity == Severity.WARNING and "chart.png" in f.message for f in findings)


def test_py_with_png_ok(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    _write(bundle / "index.md", VALID_FM)
    _write(bundle / "assets" / "chart.py", "import matplotlib\n")
    (bundle / "assets" / "chart.png").touch()
    findings = validate_bundle(bundle)
    assert not any("chart.png" in f.message for f in findings)


def test_py_with_placeholder_ok(tmp_path):
    bundle = tmp_path / "2026-04-01-test-query"
    _write(bundle / "index.md", VALID_FM)
    _write(bundle / "assets" / "chart.py", "import matplotlib\n")
    (bundle / "assets" / "chart.png.placeholder").touch()
    findings = validate_bundle(bundle)
    assert not any("chart.png" in f.message for f in findings)


def test_validate_all(tmp_path):
    b1 = tmp_path / "2026-04-01-first"
    _write(b1 / "index.md", VALID_FM)
    b2 = tmp_path / "2026-04-02-second"
    b2.mkdir()  # missing index.md
    findings = validate_all_bundles(tmp_path)
    assert any(f.severity == Severity.ERROR for f in findings)
    assert len([f for f in findings if f.severity == Severity.ERROR]) >= 1


def test_mini_base_example():
    """The mini-base example output bundle must pass validation."""
    bundle = Path("examples/mini-base/out/2026-04-01-attention-mechanisms-compared")
    findings = validate_bundle(bundle)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert errors == [], f"Errors: {errors}"
