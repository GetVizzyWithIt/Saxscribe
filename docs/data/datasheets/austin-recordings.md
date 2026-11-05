# Datasheet: Austin's recordings and personal answer keys

## Motivation
The only data in Austin's own sound and style, and the only way to meet the
v1 gate "solo targets on 20 of your own recordings". Also the long-term
training loop: every correction in the editor becomes labelled data.

## Composition (planned)
1. **Etude takes**: Austin plays written material (alto first), recorded on
   phone or interface. The written score becomes the answer key via
   `python -m saxscribe answer-key take.wav etude.musicxml` (DTW alignment,
   onsets snapped to heard attacks within 80 ms). Tier B until spot-checked, then A.
2. **Paper transcriptions paired with records**: Austin owns many printed
   transcriptions for alto and tenor. Each is scanned (one PDF per tune, with
   the recording and horn noted), read by optical music recognition (Audiveris
   or oemer) into MusicXML, fixed by hand, then aligned to the record. First
   tune: Stan Getz, "Pennies from Heaven".
3. **Editor corrections**: model output plus Austin's edits, stored as a diff
   (`edits/notes.ops.jsonl`), the model's `notes.json` untouched.

## Collection process
Austin's own horn(s), his room, his equipment. Record per take: horn, mouthpiece/setup if relevant, device, backing track or not.

## Uses
- 20 takes frozen as a test set, never trained on.
- Fine-tuning data; aim for 50 takes before the first fine-tune.
- Written pitch differs by horn: always record which horn a transcription is written for.

## Distribution
Private. Audio stays on the Mac. Commercial records are Austin's own copies
and are never uploaded or shared. Not in the repo.

## Status
- 2026-11-02: none recorded yet. Scans to be sent in the UI thread.
- 2026-11-03: first personal answer key under way: Austin's printed transcription of Stan Getz, "Blues for Mary Jane" (4 pages, concert C), being digitised. The record is Austin's own copy, on the Mac only. The transcription confirms Getz plays 0–192 s (intro plus 12 choruses), which PR #35's sax-span probe matched.
- 2026-11-03: first hand comparison of the app's PDF against this transcription, two choruses ([log E18](../../evaluation/log.md)). Turning the full transcription into a scored answer key needs an OMR tool on the Mac (awaiting Austin's approval).
- 2026-11-03: **first personal answer key scored**: intro and choruses 1–2 hand-entered (136 notes, first 35 s) and aligned. Note F1 54% (70% without note ends), onset recall 83%, no octave errors ([log E19](../../evaluation/log.md)).
- 2026-11-04: **second personal answer key**: Stan Getz with the Oscar Peterson Trio, "Pennies From Heaven" (tenor). Austin's verified first half typed in by hand: 169 bars, 867 notes, 87% confirmed by heard pitch. Key and differences CSV in the project files (`transcriptions/pennies-from-heaven/`); Mac copy at `~/saxscribe-runs/keys/pfh/` (JSON and MIDI). A fresh run scores 49.2% against 50.3% for the library take: Demucs varies by about 1 point between runs on this record (E42). Note F1 50.3% (66.5% without note ends), onset F1 75.1%, pitch 69.3%, 2 octave errors ([log E40](../../evaluation/log.md)). Tier A (checked by Austin). Test only, never trained on.
- 2026-11-04: piano bleed review on Pennies From Heaven ([log E46](../../evaluation/log.md)). 87 notes in the keyed half are piano or bass, 9% of the notes on the sheet. 3:42–4:21 is a piano solo with Getz out (Austin confirmed by ear, 2026-11-05). Oscar Peterson's piano is inside Demucs's "vocals + other" stem with the sax, so separation can't remove it. A list of suspect notes is in the project files (`transcriptions/pennies-from-heaven/piano-bleed/`).
- 2026-11-05: the jazz sax survey estimates 4–9 more answer keys are needed for testing, and 10–20 pop/soul keys for training. Jazz training keys aren't needed if the Weimar records are bought ([ADR-0035](../../decisions/0035-sax-trained-note-model-plan.md)). Austin's keys stay test-only.
- 2026-11-05: **four more tenor keys** from Austin's PDFs, typed by hand (written pitch minus 14 semitones = concert): Resolution (Coltrane, 939 notes, 320 bars, includes a 92-bar piano solo where the sax rests), Walker's Theme (Albright, 863 notes), Isn't She Lovely (Hornheads, Kenni Holmen's solo only, 319 notes) and Bloody Well Right (Supertramp, John Helliwell, 174 notes: two short fills and the solo). Keys in the project files (`transcriptions/<song>/key/`, plus MusicXML), audio on the Mac only (`~/saxscribe-runs/keys/<song>/`). Timing is a draft fitted to the sax stem's pitch line (66–81% of key notes agree with the heard pitch); about 10 hard-to-read notes still to settle by ear. First scores: note F1 41.7% / 24.6% / 21.0%, and 0 on Walker's Theme from a sax-span bug ([log E53](../../evaluation/log.md)). Test only.
