# Issue 05: golden-set-session-1

Status: done
Blocked by: 02, 01(S0)
Session: 03
Closes: audio/s1/ (200 files)

## Summary
Record golden session 1: 200 utterances, 48 kHz S16_LE mono, quiet room, offline 3:1 soxr VHQ resample to 16 kHz.

## Deliverables
- Planned for Session 03.
- Closes requirement: audio/s1/ (200 files).

## Comments
- 2026-09-07 (Session 01A): Tracker initialized.
- 2026-09-14 (Session 03): `data/record_session.py` + `data/resample.py` written and tested (19 tests). Capture device auto-detected by NAME (`USB Audio Device`, hw:2,0) because ALSA card numbers move between boots -- S0 saw hw:1,0. 48 kHz masters stay in `audio/s1/` and are never written to; the derived 16 kHz corpus is `audio/s1_16k/`. **Waiting on ~90 min of human recording.**
- 2026-09-18 (Session 03): **DONE.** 200/200 masters at 48 kHz in audio/s1/, 200 resampled to audio/s1_16k/. Room floor -70.51 dBFS (S0 baseline was -64.47); session gain -13.56 dB; active speech median -34.4 dBFS. A refrigerator was the noise contaminant, not the AC charger as S0's R-2 ladder assumed -- floor went -45.5 (AC + fridge) -> -52.1 (battery + fridge) -> -68.2 (fridge off). Two capture bugs fixed first: the +0.0078 DC offset sat 26 dB above the floor and would have refused every take, and the speech level was measured over the whole take so a long one failed for its length.
