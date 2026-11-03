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
*to verify* (the dataset search recorded ODbL; the download page didn't state one). Folder `WeimarJazzDatabase/`.

## Maintenance
Checksums in the manifest.

## Saxscribe results
- Rhythm scorecard baseline: pending (PR #53, [log E24](../../evaluation/log.md)).
- Key-finding test set: 429 solos with annotated keys, home note right 49% → 60% with the blues-aware finder ([log E15](../../evaluation/log.md)). Labels are the tune's key, so 100% isn't reachable.
