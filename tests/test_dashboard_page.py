"""The static model dashboard (scripts/dashboard_page/build.py) builds from the repo alone."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _build_module():
    spec = importlib.util.spec_from_file_location("dashboard_build", ROOT / "scripts" / "dashboard_page" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_builds_with_freshness_line_and_no_review_tab(tmp_path):
    mod = _build_module()
    out = mod.build(tmp_path / "dashboard.html")
    html = out.read_text()
    assert "Data as of E" in html and "from the repo." in html
    assert 'id="tab-review"' not in html and 'href="#review"' not in html
    assert '<script src="/static/' not in html  # everything inlined


def test_freshness_reads_newest_entry_and_date():
    mod = _build_module()
    d = {"runs": [{"entry": "E9", "when": "2026-11-01T00:00:00Z"}],
         "experiments": [{"entry": "E81", "when": "2026-11-12T03:00:00Z"}, {"entry": None, "when": ""}]}
    assert mod.freshness(d) == "E81, last run 2026-11-12"
    assert mod.freshness({}) == "no runs yet"


def test_mac_runs_folder_is_merged(tmp_path):
    mod = _build_module()
    (tmp_path / "experiments.jsonl").write_text('{"id": "x1", "entry": "E999", "when": "2030-01-01T00:00:00Z", '
                                                '"set": "pfh", "setup": {}, "metrics": {}}\n')
    html = mod.build(tmp_path / "d.html", runs=tmp_path).read_text()
    assert "Data as of E999, last run 2030-01-01" in html and "this Mac" in html
