"""Serve the play-along on the 10-second fixture, for the browser check (play_page.js).

    python -m tests.browser.serve_fixture [port]

Prints "READY <take id>" once the fixture is transcribed and the server is up.
Everything lives in a temp folder; nothing touches the real library or Desktop.
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8799
    tmp = Path(tempfile.mkdtemp(prefix="saxscribe-browser-"))
    os.environ.setdefault("SAXSCRIBE_DESKTOP", str(tmp / "Desktop"))
    import uvicorn

    from saxscribe.app.library import Library
    from saxscribe.app.server import create_app
    from tests import fixture

    wav = tmp / "phrase.wav"
    fixture.make(wav)
    library = Library(tmp / "library", inline=True)
    take_id = library.add("phrase.wav", wav.read_bytes(), horn="alto", mix=False,
                          title="Fixture phrase", artist="Test Player")
    assert library.job(take_id)["state"] == "done", library.job(take_id)
    # Mark the last bar's notes "maybe not sax", so the page has a "Sax?" question to show.
    import json
    take = library.take(take_id)
    notes = json.loads(take.notes.read_text())
    written = json.loads(take.notation.read_text())["notes"]
    last = max(n["bar"] for n in written)
    for n in written:
        if n["bar"] == last:
            notes["notes"][n["index"]].setdefault("tags", []).append("maybe_not_sax")
    take.notes.write_text(json.dumps(notes))
    server = uvicorn.Server(uvicorn.Config(create_app(library, port=port), host="127.0.0.1", port=port,
                                           log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    print(f"READY {take_id}", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.should_exit = True


if __name__ == "__main__":
    main()
