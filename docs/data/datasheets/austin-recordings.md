# Datasheet: Austin's recordings and personal answer keys (planned)

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
None recorded yet (2026-11-02). Scans to be sent in the UI thread.
