"""Build the model dashboard as one static web page, for the handbook.

    python3 scripts/dashboard_page/build.py        # writes build/dashboard.html

It is the app's Results page (/results) with its CSS and scripts inlined and
the data the app would serve from /api/results baked in, read from the repo's
docs/evaluation files only. Nothing from the Mac's ~/saxscribe-runs goes in,
so no run of the app or the Mac is needed to view it.

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

NOTE = ('<p class="quiet small" style="margin:0;padding:8px 16px">Static copy built from the repo on {date}. '
        'Reviewing keys (Needs review) and runs that only exist on the Mac stay in the app\'s Results page.</p>')


def data() -> dict:
    from saxscribe.score import history
    return history.dashboard_data(tempfile.mkdtemp())  # empty runs folder: repo records only


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


def build(out: Path | None = None) -> Path:
    import datetime
    d = data()
    html = inline(model_only((STATIC / "results.html").read_text()))
    shim = SHIM % json.dumps(d, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("<script>\n", shim + "\n<script>\n", 1)
    html = re.sub(r"(<body[^>]*>)", r"\1" + NOTE.format(date=datetime.date.today().isoformat()), html, count=1)
    out = out or ROOT / "build" / "dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return out


if __name__ == "__main__":
    print(build())
