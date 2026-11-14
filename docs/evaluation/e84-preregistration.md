# E84: held-out swap retrain, then all-in model (pre-registration)

Written 2026-11-14 17:30Z, before any E84 training or scoring. Austin's go: "go held-out swap: train on Coltrane, Potter, Getz (except benchmark, test-tune and held-out sessions); hold out Byas, Stitt, Marsh, Berg, Mobley, Sims + 2 alto players" (Build, 17:14Z). Two-stage plan agreed in Build 17:16Z. Advisor second-pass review in the book-matching thread (17:11Z).

## Question
Does a note finder trained with Coltrane, Getz and Potter in training (and a new set of held-out players for choosing the checkpoint) beat E77 on the 33-song benchmark? And does a final model trained on every player beat it?

## Arms
Both arms start from filosax_25k.pth (Riley & Dixon, sha256 448cf2c8ea6d4b77f7435f5b9a496211ea60300c5c17fa9c754da764f75f3a6a), not from E77. E77 trained on the E76 train set, which held the new held-out players, so starting from E77 would make them "seen". Recipe as E77, on Filosax-separated stems: hybrid loss, patience 1500, validate every 500, cap 6000.

| Arm | Training data | Checkpoint |
|---|---|---|
| E84a | 108 spans, 260.5 min, 59,258 notes (see Split) | Best per-solo mean note F1 on the new held-out set (24 solos); note-weighted value and 1,000-resample bootstrap range logged |
| E84b | E84a's train set plus the 24 held-out spans (132 spans, 302.8 min, 68,493 notes) | Fixed number of steps = E84a's best step; final step kept; held-out F1 logged for information only |

## Split (built 2026-11-14 on the Mac, ~/saxscribe-runs/exp/e84/manifest.csv)
- Train (E84a): E76 train set, minus the 22 new held-out spans, minus session drops; plus the 22 former held-out spans (Coltrane, Getz and Potter) that pass the session rule; plus 4 Weimar solos not in E76 (Brecker Confirmation, Rollins Everywhere Calypso 1 and 2, Potter Item 1). E83b's new pairs are not used, apart from the 2 held-out altos.
- Held out: Bob Berg 2, Don Byas 6, Hank Mobley 4, Sonny Stitt 3, Warne Marsh 3, Zoot Sims 4, Gary Bartz (alto, Strode Rode) 1, Charles Davis (alto, Miriam's Delight) 1. That is 24 spans, 42.3 min and 9,235 notes.
- Session rule: any span from the same recording session or album sessions as a benchmark song or one of Austin's six tunes stays out of every arm. Dropped:
  - Coltrane Blue Train (same session as Lazy Bird)
  - Brecker Never Alone and Peep (Now You See It, same as Chime This)
  - Webster Bye Bye Blackbird (Ben Webster Meets Oscar Peterson, same as The Touch of Your Lips)
  - Getz I'm Glad There Is You (1957-10-10 with Oscar Peterson, same as Austin's Pennies From Heaven)
  - Coltrane Impressions 1961 and 1963
  - Dexter Gordon Cheese Cake (Go!, same band two days before Soy Califa; dropped to be safe)
- Answer-key audit drops (2026-11-14, added 20:45Z before any training): Maiden Voyage m171 (14% of key notes agree with the pitch line) and I'll Remember April m382 (47%), likely wrong take or line-up. Both were in E76 train.
- Held-out alto masks (audit misreads): Charles Davis bars 51, 75, 86, 87, 92, 99, 104 and 116 (half step off; 57 of 742 notes); Gary Bartz bars 14, 93, 94 and 175 (octave or fifth off; 18 of 1,006 notes). These bars are left out of held-out scoring in both arms. "Pitches differ" bars are kept.
- All E83 leakage rules still hold: the 33 benchmark songs; Austin's six tunes, his flags and his own playing; the 3 Parker test records.

## Known past leak
Blue Train, Never Alone, Peep and Bye Bye Blackbird were in the E76 train set, so E77, E83a and E83b trained on recordings from the same sessions as 3 benchmark songs: Lazy Bird, Chime This and The Touch of Your Lips. E77's score on those 3 may be slightly flattering. The comparison therefore leans toward E77.

## Scoring (once, at the end)
Benchmark keys are proofread first (audit thread), then frozen: freeze_keys.sh writes the sha256 of all 38 files the scorer reads to e84/KEYS_FROZEN. score84.py checks every hash and stops if any key changed. E77, E84a and E84b are all scored on the same frozen keys, so E77's numbers may differ from E81 and E83. Training starts before the freeze, since training never reads benchmark keys.
E81 setup D (Filosax separator) on all 33 songs, run with E77, E84a and E84b finders. Same thresholds, same classify, bars on. Secondary report: the same comparison on the 30 songs without the 3 leaked sessions.

## Adoption rule (same as E83)
An arm is a candidate when, against E77 on all 33 songs:
- its mean note F1 is at least 1.0 point higher;
- it wins at least 18 of 33 songs;
- its mean note F1 without offsets is not lower.

If both qualify, the higher mean note F1 wins. A tie within 0.3 goes to E84b, the all-in model. Switching the app's default still needs Austin's go. Held-out scores from E84 on are not comparable to E77 and E83 (a clean break).

## Not in E84
Note-end fix, pop and R&B data, and soprano.

## Case against
- Two changes at once versus E77: the start point (filosax_25k instead of E77 weights) and the data. A win or loss can't be pinned on the swap alone. E83a showed Filosax versus Mega training stems is neutral.
- The new held-out set is small (24 solos, about 42 min), so checkpoint picks are noisy. The bootstrap range is logged.
- The held-out altos have grace notes removed while the Weimar spans keep them, so held-out scoring conventions are mixed.
- E83 found that more of the same jazz data didn't help. This adds about 25 more minutes of mainstream tenor.
- Bias-check count: E83 was one experiment that didn't beat the best. If E84 also fails, that makes two.
