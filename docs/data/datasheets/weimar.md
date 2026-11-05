# Datasheet: Weimar Jazz Database (Jazzomat)

## Motivation
Made by the Jazzomat Research Project (Hochschule für Musik Franz Liszt
Weimar) for computational study of jazz improvisation.

## Composition
- 456 expert transcriptions of jazz solos: 157 tenor, 80 alto, 23 soprano, 11 baritone sax, plus other instruments.
- Per solo: notes with onsets and durations aligned to the commercial record, beats, bars, chords, phrases. SQLite (`wjazzd.db`) and MIDI.
- **No audio.** Tier E: answer keys once paired with a copy of the record.

## Collection process
Transcribed by trained annotators with software assistance, against the original records.

## Preprocessing and labelling
No Saxscribe loader yet. Pairing needs records Austin owns, aligned to the
database's timing (check the offset per record).

## Uses
- **Role**: key-finding test set (no audio needed; PR #34); rhythm scorecard for the notation layer (`python -m saxscribe rhythm`, PR #53; split by performer; Parker melids 52, 53, 55, 58–61, 63, 64, 66–68 excluded because they are also in the Omnibook); full-mix answer keys (especially tenor) once paired with Austin's records; chord context for enharmonic spelling; style statistics.
- **Do not use for**: anything requiring audio until records are sourced.

## Distribution
https://jazzomat.hfm-weimar.de/download/, open download, 44 MB. Licence:
ODbL 1.0 (confirmed by the jazz sax research survey, 2026-11-05). The separate jazzomat `raw_data` repository states no licence. Folder `WeimarJazzDatabase/`.

## Maintenance
Checksums in the manifest.

## Saxscribe results
- Rhythm scorecard baseline (444 solos): exact position 58.7%, right beat 89.3%, notes kept 100%; ballads 15.7%, slow tunes 18.5% ([log E24](../../evaluation/log.md)). Weimar writes swung off-beats at their played position, so exact position undercounts correct swing notation. On the swing-aware measure (`position_read`, PR #55): 63.1% overall, 57.6% saxes; ballads 16.9%, slow tunes 19.5% ([log E28](../../evaluation/log.md)). After PR #64 (finer grids): 65.9% overall, ballads 36.2% ([log E32](../../evaluation/log.md)). About 37% of ballad notes are in 5-, 7- or 9+-way divisions that no regular grid matches.
- Key-finding test set: 429 solos with annotated keys, home note right 49% → 60% with the blues-aware finder ([log E15](../../evaluation/log.md)). Labels are the tune's key, so 100% isn't reachable.

2026-11-05 ([survey](https://claude.ai/artifact/51xs3wjGscA9JLx9ZB4Wxu)): jazzomat `raw_data` has f0 tracks for 110 tenor and 50 alto solos, at a 5.805 ms hop, with times relative to the WJD solo cut; tuning ranges 428–453 Hz. Buy lists for the solos' audio are in the project files (`datasets/weimar-audio/`): `wjd_tenor_solos.csv` and "Weimar tenor songs to buy.csv", which lists 142 songs with warnings where the take is easy to mix up. Buying them would give jazz training audio with Weimar's note labels. JazzTube released no YouTube IDs and its site is down, so it is not a route to the audio.

2026-11-05, first audio: Austin bought five records. They are Sonny Rollins "The Everywhere Calypso", Chris Potter "Item 1" (D.I.T.), Michael Brecker "Confirmation", and John Coltrane "Impressions" (Village Vanguard 1961 and Berlin 1963). Each take was checked against the Weimar notes: 80–94% of notes are the loudest pitch at that moment, where chance would be 17%. The 1961 Impressions copy runs 14:53, not the listed 15:02, but the solo is complete. Six solos (11,729 notes, about 13% of the buy list) are now Saxscribe-format keys, on the Mac only (`~/saxscribe-runs/keys/weimar/`). Two Weimar notes below the tenor's low A-flat are kept and flagged, not dropped. Status of each record: `datasets/weimar-audio/weimar_audio_status.csv` in the project files. The audio stays private on the Mac. Scoring is under way in the build thread. First scores: note F1 57.3% over the six solos, 78.5% on Confirmation ([log E56](../../evaluation/log.md)).
Split (2026-11-05): Impressions 1961, Impressions 1963 and Item 1 (D.I.T.) are locked as test records, held out by record. About 1 in 5 records bought from now on goes to test. Alignment passed the go/no-go check (residual 2–15 ms). See [ADR-0035](../../decisions/0035-sax-trained-note-model-plan.md).
