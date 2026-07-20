# Issue 05: golden-set-session-1

Status: blocked-on-human
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
