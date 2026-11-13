"""Build the model dashboard as one static web page, for the handbook.

    python3 scripts/dashboard_page/build.py        # writes build/dashboard.html
    python3 scripts/dashboard_page/build.py --runs ~/saxscribe-runs --open   # on the Mac

It is the app's Results page (/results) with its CSS and scripts inlined and
the data the app would serve from /api/results baked in. By default only the
repo's docs/evaluation files go in: that is the copy published next to the
handbook, so no run of the app or the Mac is needed to view it. With --runs,
the Mac's own results.jsonl and experiments.jsonl in that folder are merged in
too (runs not logged yet), and --open shows the page in the browser. That copy
stays on the Mac.

A line at the top says which experiment the data runs to and when it was
built, so a stale copy is easy to spot.

Only the model-performance tabs come over (Progress, Songs, Lab, Log). The
reviewer parts (Needs review, flags) play recordings from the Mac and stay in
the app.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "saxscribe" / "app" / "static"
sys.path.insert(0, str(ROOT))

SHIM = """<script>
// Static copy: answer the page's API calls from the baked-in data.
window.__SAXSCRIBE_STATIC__ = true;
(function () {
  const DATA = %s;
  const realFetch = window.fetch;
  window.fetch = function (url, opts) {
    const u = String(url);
    // answer once the page is laid out: the charts measure their boxes when drawn
    const laidOut = new Promise(ok => (document.readyState === 'complete' ? ok() : addEventListener('load', () => ok())))
      .then(() => new Promise(ok => requestAnimationFrame(() => ok())));
    if (u.startsWith('/api/results')) return laidOut.then(() => new Response(JSON.stringify(DATA), {headers: {'Content-Type': 'application/json'}}));
    if (u.startsWith('/api/review')) return Promise.resolve(new Response('null', {status: 404}));
    return realFetch.apply(this, arguments);
  };
})();
</script>"""

HANDBOOK_URL = "https://claude.ai/artifact/LHvpK1sBSP8ADqziMc2c8X"

NOTE = ('<p class="quiet small" style="margin:0;padding:8px 16px"><b>Data as of {latest}.</b> Built {date} from {source}. '
        'Reviewing keys (Needs review) stays in the app\'s Results page.</p>')


def data(runs: str | Path | None = None) -> dict:
    from saxscribe.score import history
    # an empty runs folder means repo records only
    return history.dashboard_data(Path(runs).expanduser() if runs else tempfile.mkdtemp())


def freshness(d: dict) -> str:
    """'E81, run 2026-11-12': the newest experiment entry in the data and the date of the newest row."""
    rows = list(d.get("runs") or []) + list(d.get("experiments") or [])
    nums = [int(m.group(1)) for r in rows if (m := re.fullmatch(r"E(\d+)", str(r.get("entry") or "")))]
    when = max((str(r.get("when") or "")[:10] for r in rows), default="")
    parts = [f"E{max(nums)}" if nums else "", f"last run {when}" if when else ""]
    return ", ".join(p for p in parts if p) or "no runs yet"


def inline(html: str) -> str:
    def css(m: re.Match) -> str:
        return "<style>\n" + (STATIC / m.group(1)).read_text() + "\n</style>"

    def js(m: re.Match) -> str:
        return "<script>\n" + (STATIC / m.group(1)).read_text().replace("</script", "<\\/script") + "\n</script>"

    html = re.sub(r'<link rel="stylesheet" href="/static/([\w.-]+)">', css, html)
    return re.sub(r'<script src="/static/([\w.-]+)"></script>', js, html)


def model_only(html: str) -> str:
    """Drop the reviewer parts (Needs review tab, its panel and script); the Library button goes to the handbook."""
    html = re.sub(r'<a role="tab" href="#review".*?</a>', "", html, flags=re.S)
    html = re.sub(r'\n\s*<div class="tab" id="tab-review".*?\n  </div>', "", html, flags=re.S)
    html = html.replace('<script src="/static/results-review.js"></script>', "")
    return html.replace('<a class="button" href="/">Library</a>', f'<a class="button" href="{HANDBOOK_URL}" target="_blank" rel="noopener">Handbook</a>')


def build(out: Path | None = None, runs: str | Path | None = None) -> Path:
    import datetime
    d = data(runs)
    html = inline(model_only((STATIC / "results.html").read_text()))
    shim = SHIM % json.dumps(d, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("<script>\n", shim + "\n<script>\n", 1)
    html = re.sub(r"(<body[^>]*>)", r"\1" + NOTE.format(latest=freshness(d), date=datetime.date.today().isoformat(),
                                                   source="the repo and this Mac's runs" if runs else "the repo"), html, count=1)
    out = out or ROOT / "build" / "dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return out


if __name__ == "__main__":
    import argparse
    import webbrowser
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", help="also merge this folder's results.jsonl and experiments.jsonl (the Mac's ~/saxscribe-runs)")
    ap.add_argument("--out", type=Path, help="where to write the page (default build/dashboard.html)")
    ap.add_argument("--open", action="store_true", help="open the page in the browser when done")
    a = ap.parse_args()
    path = build(a.out, a.runs)
    print(path)
    if a.open:
        webbrowser.open(path.resolve().as_uri())
