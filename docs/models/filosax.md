# Model card: Filosax separator and transcriber (Riley & Dixon)

## Model details
- **What it does**: the separator pulls a saxophone out of a band record; the transcriber writes sax notes from that stem.
- **Developed by / version / date**: Xavier Riley and Simon Dixon, Queen Mary University of London, 2024.
  - Separator: `filosax_demucs_v3_14.22_SDR.th`, sha256 `4a801bc0…dbe360`.
  - Transcriber: `filosax_25k.pth`, 99,341,469 bytes, sha256 `448cf2c8…3a6a`.
- **Type**:
  - Separator: Demucs v3 hybrid (HDemucs) with two sources, "Sax" and "BackingMono". It loads under Demucs 4.1.0.
  - Transcriber: Kong et al.'s high-resolution CRNN (onset, offset, frame and velocity heads; 88 pitch classes; 16 kHz; 100 frames per second), fine-tuned on Filosax.
- **Source and licence**:
  - Weights are on Hugging Face (`xavriley/demucs_v3_saxophone_separation`, `xavriley/midi-transcription-models`), MIT.
  - The transcriber code is vendored from xavriley's fork of Kong's `piano_transcription_inference` (@7568dc7, MIT) into `saxscribe/vendor/kong.py`.
- **How Saxscribe calls it**: `saxscribe/filosax.py`.
  - `separate()` runs with shifts 1, overlap 0.25, on the CPU.
  - `transcribe()` uses the package's default thresholds: onset 0.3, offset 0.3, frame 0.1.
  - Both checkpoints load with torch's safe loader, and their sha256 is checked before every use.
- **Citation**: Riley & Dixon, "Reconstructing the Charlie Parker Omnibook using an audio-to-score automatic transcription pipeline", SMC 2024, arXiv 2405.16687.

## Intended use
- **In Saxscribe**: an opt-in alternative for layer 1 (`--separator filosax`) and for layer 3 notes (`--notes-tool filosax`). In the app it is the "Filosax (test)" note finder. Use case U2 (other players' records).
- **Out of scope**: it is not yet the default. It has not been checked on Austin's own playing.

## Factors
Both models were trained on Filosax: 24 hours of tenor sax, jazz standards played over backing tracks. They are strongest on jazz small-group records, and about even with ours on pop and fusion, where guitar, keys and vocals leak into the sax stem.

## Metrics
The scorecard set: note F1, no-offset note F1, onset recall and precision, sax found, sax purity. The transcriber writes no pitch line, so it has no pitch-accuracy score.

## Training data
Filosax, which is tenor sax only. The transcriber's ±5 semitone pitch shifts cover the alto range.

## Evaluation data and results (2026-11-05, Mac, current main, note F1)

| Set | Demucs + Basic Pitch (app today) | Filosax separator + Basic Pitch | Filosax separator + transcriber |
| --- | --- | --- | --- |
| Weimar, 6 solos, human keys (11,729 notes) | 57.3 | 60.2 | **76.3** (no sax-rest checks; 66.4 with them) |
| 4 tenor pop/fusion tunes | 32.5 | **37.3** | 36.1 |
| Pennies From Heaven | 50.1 | 54.7 | 57.7 (MVSep web + ours: 58.2) |
| Blues for Mary Jane | **56.2** | 52.2 | 52.0 (48.6 through the CLI; separator run-to-run variation, about 2 of 136 notes) |
| Parker, 10 band records | 58.2 | 62.6 | 67.2 † |

† The Omnibook keys' onsets were refined against a transcription model's frame activations (paper, section 3.1), so this key may favour their transcriber.

Speed on an M3 Pro: separator about 6 s per minute of audio on the CPU; transcriber about 9 s per minute on the CPU. Demucs htdemucs_6s with shifts 2 is slower.

## Ethical and licensing considerations
Code and weights are MIT. Filosax itself is a research dataset; we only use the published weights, not the data.

## Caveats and recommendations
- Blues for Mary Jane drops by about 4 points: the separator loses its quiet notes.
- With the transcriber, the sax-rest and bleed checks are skipped because they cut real notes. On the Weimar solos they cost about 10 points.
- The CLI path (this PR, commit 7708267) scores within about 1 point of the R&D run on every set except BFMJ: Weimar 76.9, Parker 67.5, PFH 56.8, tenor tunes 35.9. End-to-end it takes 40–74 s per minute of audio, because the pitch line and beats still run.
- **Piano solos leak through** (log E61): on Pennies From Heaven the Filosax path writes 64 notes of the 3:42–4:21 piano solo. The stem keeps the piano near sax level, so the bleed check can't hide them. The standard path does. Use the standard path, or check the sheet by ear, on records with long piano solos until a rival-stem check exists.
- **Quiet sax is lost** (E61): in bars 82–84 of Pennies the separator holds the sax 28.5 dB under the mix. In the four quiet stretches it finds 20 of 56 key notes, where Demucs finds 28. Austin's own flags confirm it (E69): 9 Missing note flags on Pennies cover 41 key notes, all quiet low sax that the separator turns down by 15–50 dB. Note-finder fixes can't recover them (E70): the notes are gone from the stem.
- Next step: an A/B on Austin's own takes.

## Change history
| Date | Change | PR |
| --- | --- | --- |
| 2026-11-05 | Added as opt-in separator and note finder | this PR |
