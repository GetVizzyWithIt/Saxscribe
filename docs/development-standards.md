# Development standards

Austin's standards for every repo, and where Saxscribe stands on each.
Checked 2026-11-06. Update this table when a row changes.

| Standard | Status | Where / what's left |
| --- | --- | --- |
| README opens with copy-paste commands | Met | [README.md](../README.md) starts with the update, start, transcribe, scorecard and test commands |
| One-step setup script that ends with a health check | Met | `bash setup_mac.sh` installs everything and ends with `python -m saxscribe check`; fails loudly if a required piece is missing |
| Runtime version pinned | Met | `.python-version` (3.11); setup, CI and `saxscribe check` read it |
| Lockfile committed | Met | `requirements.lock` (exact versions, Apple Silicon); regenerate with `bash scripts/lock.sh`; scorecard model versions held in `scripts/scorecard-versions.txt`. The Filosax experiment venv (demucs 3.0.6) lives on the Mac only and is not locked here |
| CLAUDE.md with working rules and current state | Met | [CLAUDE.md](../CLAUDE.md): working rules, branch/PR/CI rules, current state |
| Tests on core logic | Met | `tests/`: every layer on the 10-second synthetic fixture, plus app, scoring and rule tests (199 tests) |
| CI runs tests on every PR | Met in the repo; needs a GitHub setting | `.github/workflows/tests.yml`. To make "nothing merges without the tests passing" binding, require the `pytest` check in a branch rule (Austin, on GitHub) |
| One PR per change, nothing straight to main | Practised; needs a GitHub setting | Every change since the first commits went through a PR. A branch rule on main (require a PR, require the `pytest` check) makes it enforced, not just practised |
| Branch names follow claude/&lt;type&gt;-&lt;what&gt; | Met from now on | Rule in CLAUDE.md. Old `claude/project-thread-xxxx` branches were named by the session system; all merged ones are deleted |
| Decision log in docs/decisions/ | Met | [docs/decisions/](decisions/README.md), ADR-0001 onward |
| Project glossary or data dictionary | Met | [docs/glossary.md](glossary.md); file formats (notes.json, take.json, flags.json) in [docs/architecture/system.md](architecture/system.md) |
| Secrets and machine files out of git | Met | Full history scanned 2026-11-06: no keys, tokens, audio or weights ever committed. `.gitignore` covers audio, `config.local.*`, `.env`, keys, weights, `.DS_Store`, editor folders. The MVSep key stays in a private file on the Mac |
| Private repo, or public by decision | Met | Private |
| Security alerts on, none serious left open | Needs a GitHub setting | Turn on Dependabot alerts, Dependabot security updates and secret scanning (Settings → Code security). Not visible from a Claude session |
| Schema changes through migrations | Does not apply (no database) | The closest thing is the take files on disk (notes.json, take.json, flags.json). Suggested follow-up when pipeline work resumes: a `format` version number in take.json and an upgrade step for old takes |
| Deploys from main automatically | Does not apply as written | There is no server: the app runs on Austin's Mac from a git checkout. "Deploy" is the update command in the README, which always pulls main. Auto-pulling while the app runs could swap code mid-transcription, so it stays a manual step by decision |
| Framework versions still get security fixes | Mostly met; one known hold | Python 3.11 gets security fixes until Oct 2027. FastAPI, uvicorn and numpy are current. Torch is held below 2.9 on purpose (newer torchaudio breaks Demucs' audio saving); upgrade in its own PR with a scorecard. Demucs is no longer actively developed (bug fixes only) |
