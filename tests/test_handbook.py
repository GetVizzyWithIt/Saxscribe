"""HANDBOOK.md's generated blocks must match the repo's records.

If this fails, run `python3 scripts/handbook.py` and commit HANDBOOK.md.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _handbook():
    spec = importlib.util.spec_from_file_location("handbook", ROOT / "scripts" / "handbook.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_handbook_generated_blocks_are_current():
    hb = _handbook()
    text = (ROOT / "HANDBOOK.md").read_text()
    assert hb.render(text) == text, "HANDBOOK.md is out of date: run python3 scripts/handbook.py"


def test_render_only_touches_marked_blocks():
    hb = _handbook()
    text = (ROOT / "HANDBOOK.md").read_text()
    stripped = text.split("<!-- auto:status -->")[0]
    assert hb.render(text).startswith(stripped)
