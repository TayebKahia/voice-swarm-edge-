#!/usr/bin/env python3
"""Golden-set capture --- the 320 files that cannot be re-made.

`prd.md` D4 and `IMPLEMENTATION_ROADMAP.md` §0.2 conflict 3: record at **48 kHz,
S16_LE, mono**, one file per utterance, and resample offline. Recording at 16 kHz
is irreversible --- the resample path cannot be recovered afterwards and these 320
files cannot be re-recorded --- so this tool refuses to open a stream at any other
rate.

Three properties matter more than convenience here:

**The filename is a join key.** `0042.wav` is the same utterance in `s1/`, `s2/`
and `s3/`, and `0042` is its line in `test_golden.jsonl`. The tool derives the
filename from the transcript file and never from the order in which items were
recorded, so a skip or a retake cannot shift the corpus by one.

**A bad take is rejected at capture time, not at analysis time.** Clipping and
silence are both unrecoverable and both invisible in a spectrogram glance. Every
take is measured against a room-silence reference recorded at session start and
either accepted or offered as a retake; nothing is written that has not passed.

**Nothing is processed.** No AGC, no noise suppression, no normalisation, no
resampling. `data/audio/s1/` holds what the ADC produced. The 3:1 soxr VHQ
resample and the level normalisation are `data/resample.py`, offline, reversible,
and applied to a *copy*.

Usage:
    python data/record_session.py --session s1
    python data/record_session.py --session s2 --ids data/golden_subset_60.txt
    python data/record_session.py --list-devices

Keys during a session: [Enter] start, [Enter] stop, then
[Enter] accept · [r] retake · [s] skip · [q] save and quit.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import queue
import sys
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import soundfile as sf

if __package__ in (None, ""):  # `python data/record_session.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.mix_noise import active_speech_rms, rms

DATA_DIR = Path(__file__).resolve().parent
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPTS = DATA_DIR / "test_golden_transcripts.txt"

#: Non-negotiable (`prd.md` D4). The tool exits rather than record at another rate.
CAPTURE_RATE = 48_000
CAPTURE_SUBTYPE = "PCM_16"  # S16_LE

#: Discarded at the head of every stream. The USB ADC settles and the Enter
#: keystroke's own mechanical transient lands inside this window; S0 found both.
WARMUP_SECONDS = 0.30

#: A take shorter than this is a mis-trigger; longer than this is a runaway
#: stream, and the cap exists so an unattended session cannot fill the disk.
MIN_SECONDS = 0.50
MAX_SECONDS = 20.0

#: Full scale for S16. `soundfile` hands back float in [-1, 1); a sample at or
#: past this is a clipped sample, and clipping cannot be undone.
CLIP_LEVEL = 0.999
MAX_CLIPPED_SAMPLES = 0

#: Active-speech level against the room floor measured at the start of the
#: session. Two thresholds, because one would be wrong in one direction or the
#: other: S0's headline "28.4 dB" is *peak* over the floor, and the active-speech
#: RMS on this chain sits roughly 11 dB under the peak --- so a perfectly good
#: BOYA take measures ~17 dB here. Rejecting at 20 dB would reject the corpus.
#: Below `MIN_SNR_DB` the capture is broken (muted, off-axis, wrong device) and
#: the take is refused; between the two it is written with a warning.
MIN_SNR_DB = 12.0
GOOD_SNR_DB = 20.0

#: Headroom either side of the speech. Too little and the VAD has nothing to
#: anchor end-of-speech against; a warning, not a rejection, because a tight but
#: clean take is still usable and re-recording costs the author 30 seconds.
MIN_MARGIN_SECONDS = 0.10

#: Recorded for the dataset card. Anything above this and the room is not the
#: room S0 characterised, so the nominal SNR levels in Exp-3 would not hold.
MAX_ROOM_FLOOR_DBFS = -50.0
SILENCE_REFERENCE_SECONDS = 5.0

BLOCK_FRAMES = 2_400  # 50 ms at 48 kHz


def dbfs(level: float) -> float:
    return 20.0 * np.log10(max(level, 1e-12))


# --- device selection ------------------------------------------------------


def _sounddevice():
    try:
        import sounddevice as sd
    except Exception as exc:  # pragma: no cover - environment probe
        raise SystemExit(
            f"sounddevice is required to record: {exc}\n"
            "conda activate pfe_swarm"
        ) from exc
    return sd


def list_devices() -> None:
    sd = _sounddevice()
    print("input devices:")
    for index, device in enumerate(sd.query_devices()):
        if device["max_input_channels"] > 0:
            print(
                f"  [{index:2d}] {device['name']!r}  "
                f"ch={device['max_input_channels']}  default_rate={device['default_samplerate']:.0f}"
            )


def find_capture_device(preferred: str | None = None) -> tuple[int, str]:
    """Pick the USB capture device by name, never by index.

    ALSA card numbers move between boots --- S0 recorded `hw:1,0` and the same
    microphone came back as `hw:2,0` --- so an index written into a script points
    at the laptop's built-in microphone sooner or later. The built-in ALC295
    peaks 31 dB hotter than the BOYA and applies its own processing, which would
    silently split the corpus across two capture chains.
    """
    sd = _sounddevice()
    devices = sd.query_devices()
    inputs = [(i, d) for i, d in enumerate(devices) if d["max_input_channels"] > 0]

    if preferred is not None:
        if preferred.isdigit():
            index = int(preferred)
            return index, devices[index]["name"]
        for index, device in inputs:
            if preferred.lower() in device["name"].lower():
                return index, device["name"]
        raise SystemExit(f"no input device matching {preferred!r}; try --list-devices")

    for needle in ("usb audio device", "usb", "generalplus", "boya"):
        for index, device in inputs:
            name = device["name"].lower()
            if needle in name and "hw:" in name:
                return index, device["name"]
        for index, device in inputs:
            if needle in device["name"].lower():
                return index, device["name"]

    raise SystemExit(
        "no USB capture device found. The built-in microphone is NOT an acceptable\n"
        "substitute -- it processes the signal. Plug the BOYA in, or name a device\n"
        "explicitly with --device after checking --list-devices."
    )


# --- capture ---------------------------------------------------------------


def record_until_enter(device: int, max_seconds: float = MAX_SECONDS) -> np.ndarray:
    """Stream mono float32 at 48 kHz until the author presses Enter or the cap hits."""
    sd = _sounddevice()
    blocks: "queue.Queue[np.ndarray]" = queue.Queue()
    stop = threading.Event()

    def callback(indata, frames, time_info, status):  # noqa: ANN001
        if status:
            print(f"\n  [stream] {status}", file=sys.stderr)
        blocks.put(indata[:, 0].copy())

    waiter = threading.Thread(target=lambda: (input(), stop.set()), daemon=True)
    waiter.start()

    collected: list[np.ndarray] = []
    with sd.InputStream(
        device=device,
        samplerate=CAPTURE_RATE,
        channels=1,
        dtype="float32",
        blocksize=BLOCK_FRAMES,
        callback=callback,
    ):
        total = 0
        while not stop.is_set() and total < int(max_seconds * CAPTURE_RATE):
            try:
                block = blocks.get(timeout=0.1)
            except queue.Empty:
                continue
            collected.append(block)
            total += block.size
            if len(collected) % 4 == 0:
                print(f"\r  recording {total / CAPTURE_RATE:5.1f}s ", end="", flush=True)
    print()

    while True:  # drain whatever the callback queued after the loop exited
        try:
            collected.append(blocks.get_nowait())
        except queue.Empty:
            break

    if not collected:
        return np.zeros(0, dtype=np.float32)
    audio = np.concatenate(collected).astype(np.float32)
    warmup = int(WARMUP_SECONDS * CAPTURE_RATE)
    return audio[warmup:] if audio.size > warmup else np.zeros(0, dtype=np.float32)


def record_fixed(device: int, seconds: float) -> np.ndarray:
    """Blocking capture of a known length --- used for the silence reference."""
    sd = _sounddevice()
    frames = int((seconds + WARMUP_SECONDS) * CAPTURE_RATE)
    audio = sd.rec(frames, samplerate=CAPTURE_RATE, channels=1, dtype="float32", device=device)
    sd.wait()
    return audio[int(WARMUP_SECONDS * CAPTURE_RATE) :, 0].astype(np.float32)


# --- verification ----------------------------------------------------------


@dataclass
class TakeReport:
    id: str
    seconds: float
    peak_dbfs: float
    active_dbfs: float
    floor_dbfs: float
    snr_db: float
    clipped_samples: int
    lead_seconds: float
    tail_seconds: float
    failures: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.failures


def _speech_bounds(audio: np.ndarray, floor_linear: float) -> tuple[float, float]:
    """Seconds of room tone before the first and after the last active frame."""
    frame = int(CAPTURE_RATE * 0.020)
    if audio.size < frame:
        return 0.0, 0.0
    usable = (audio.size // frame) * frame
    frames = audio[:usable].reshape(-1, frame)
    energy = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1))
    threshold = max(floor_linear * 4.0, float(energy.max()) * 0.05)
    active = np.flatnonzero(energy >= threshold)
    if active.size == 0:
        return 0.0, 0.0
    lead = active[0] * frame / CAPTURE_RATE
    tail = (len(frames) - 1 - active[-1]) * frame / CAPTURE_RATE
    return float(lead), float(tail)


def verify(item_id: str, audio: np.ndarray, floor_linear: float) -> TakeReport:
    seconds = audio.size / CAPTURE_RATE
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    active = active_speech_rms(audio, CAPTURE_RATE) if audio.size else 0.0
    clipped = int(np.count_nonzero(np.abs(audio) >= CLIP_LEVEL))
    snr = dbfs(active) - dbfs(floor_linear)
    lead, tail = _speech_bounds(audio, floor_linear)

    failures: list[str] = []
    warnings: list[str] = []

    if seconds < MIN_SECONDS:
        failures.append(f"too short ({seconds:.2f}s < {MIN_SECONDS}s) -- mis-trigger")
    if seconds > MAX_SECONDS - 0.01:
        warnings.append(f"hit the {MAX_SECONDS:.0f}s cap; check the take ran on")
    if clipped > MAX_CLIPPED_SAMPLES:
        failures.append(f"CLIPPED: {clipped} samples at full scale -- unrecoverable")
    if active <= 0.0:
        failures.append("digital silence -- nothing was captured")
    elif snr < MIN_SNR_DB:
        failures.append(
            f"level too low: speech {dbfs(active):.1f} dBFS is only {snr:.1f} dB "
            f"over the room floor (need {MIN_SNR_DB:.0f} dB). Mic muted or off-axis?"
        )
    elif snr < GOOD_SNR_DB:
        warnings.append(f"speech only {snr:.1f} dB over the floor; closer to the mic would help")
    if lead < MIN_MARGIN_SECONDS:
        warnings.append(f"only {lead * 1000:.0f} ms before speech onset")
    if tail < MIN_MARGIN_SECONDS:
        warnings.append(f"only {tail * 1000:.0f} ms after speech offset (VAD needs room)")

    return TakeReport(
        id=item_id,
        seconds=round(seconds, 3),
        peak_dbfs=round(dbfs(peak), 2),
        active_dbfs=round(dbfs(active), 2),
        floor_dbfs=round(dbfs(floor_linear), 2),
        snr_db=round(snr, 2),
        clipped_samples=clipped,
        lead_seconds=round(lead, 3),
        tail_seconds=round(tail, 3),
        failures=failures,
        warnings=warnings,
    )


# --- session ---------------------------------------------------------------


def read_transcripts(path: Path = TRANSCRIPTS) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item_id, _, transcript = line.partition("\t")
        items.append((item_id.strip(), transcript.strip()))
    return items


def read_id_list(path: Path) -> list[str]:
    return [
        line.split("\t")[0].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_meta(meta_path: Path, meta: dict) -> None:
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", default="s1", choices=("s1", "s2", "s3"))
    parser.add_argument("--transcripts", type=Path, default=TRANSCRIPTS)
    parser.add_argument("--ids", type=Path, help="restrict to the ids in this file (s2/s3)")
    parser.add_argument("--device", help="index or substring; default: the USB capture device")
    parser.add_argument("--out", type=Path, help="default: data/audio/<session>")
    parser.add_argument("--redo", action="store_true", help="re-record ids already on disk")
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument(
        "--skip-floor",
        action="store_true",
        help="reuse the floor from a previous run of this session instead of measuring",
    )
    args = parser.parse_args(argv)

    if args.list_devices:
        list_devices()
        return 0

    out_dir = args.out or (AUDIO_DIR / args.session)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_path = out_dir / "session_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    items = read_transcripts(args.transcripts)
    if args.ids:
        wanted = set(read_id_list(args.ids))
        items = [(i, t) for i, t in items if i in wanted]
        missing = wanted - {i for i, _ in items}
        if missing:
            raise SystemExit(f"ids not in the transcript file: {sorted(missing)[:5]}")

    device, device_name = find_capture_device(args.device)
    print(f"capture device: [{device}] {device_name}")
    print(f"format:         {CAPTURE_RATE} Hz, S16_LE, mono -- no AGC, no processing")
    print(f"writing to:     {out_dir}")
    print()
    print("Before you start, confirm all four:")
    print("  [ ] on battery power (AC introduces 50 Hz hum; S0 measured 22 dB of it)")
    print("  [ ] AGC / noise suppression / 'voice enhancement' off")
    print("  [ ] mic at a fixed distance you can hold for 90 minutes")
    print("  [ ] room quiet: no fan, no traffic, phone silenced")
    print()

    # --- the room, recorded while the author is standing in it -------------
    # §3 of the dataset card has carried `TBD` for room and mic distance since it
    # was written. Asking here is the only moment the answer is actually known;
    # asked at write-up time it becomes a reconstruction.
    if not meta.get("room"):
        print("Two lines for dataset card §3 (Enter to leave blank and fill later):")
        meta["room"] = input("  room -- size, surfaces, time of day: ").strip()
        meta["mic_distance_cm"] = input("  mic distance in cm: ").strip()
        print()

    # --- room floor --------------------------------------------------------
    floor_dbfs = meta.get("noise_floor_dbfs")
    if floor_dbfs is None or not args.skip_floor:
        input(f"[Enter] record {SILENCE_REFERENCE_SECONDS:.0f}s of ROOM SILENCE (stay quiet) ")
        silence = record_fixed(device, SILENCE_REFERENCE_SECONDS)
        floor_dbfs = round(dbfs(rms(silence)), 2)
        sf.write(out_dir / "_room_silence.wav", silence, CAPTURE_RATE, subtype=CAPTURE_SUBTYPE)
        verdict = "PASS" if floor_dbfs <= MAX_ROOM_FLOOR_DBFS else "FAIL"
        print(f"  room floor: {floor_dbfs:.2f} dBFS  (need <= {MAX_ROOM_FLOOR_DBFS:.0f})  {verdict}")
        if verdict == "FAIL":
            print(
                "  A floor this high contaminates every nominal SNR level in Exp-3.\n"
                "  Fix the room (R-2 ladder) before recording; do not record around it."
            )
            if input("  type 'override' to record anyway: ").strip() != "override":
                return 2
    floor_linear = 10.0 ** (floor_dbfs / 20.0)

    meta.setdefault("session", args.session)
    meta["device"] = device_name
    meta["sample_rate"] = CAPTURE_RATE
    meta["subtype"] = CAPTURE_SUBTYPE
    meta["noise_floor_dbfs"] = floor_dbfs
    meta["started"] = meta.get("started") or _dt.datetime.now().astimezone().isoformat()
    meta.setdefault("takes", {})
    _write_meta(meta_path, meta)

    pending = [
        (i, t) for i, t in items if args.redo or not (out_dir / f"{i}.wav").exists()
    ]
    done = len(items) - len(pending)
    print(f"\n{len(pending)} to record, {done} already on disk.\n")

    for position, (item_id, transcript) in enumerate(pending, start=1):
        target = out_dir / f"{item_id}.wav"
        while True:
            print("=" * 72)
            print(f"[{position}/{len(pending)}]  id {item_id}")
            print()
            print(f"    {transcript}")
            print()
            command = input("[Enter] record · [s] skip · [q] save and quit  ").strip().lower()
            if command == "q":
                meta["ended"] = _dt.datetime.now().astimezone().isoformat()
                _write_meta(meta_path, meta)
                print(f"\nstopped at {item_id}. Re-run to continue -- finished ids are skipped.")
                return 0
            if command == "s":
                break

            print("  [Enter] to stop.")
            audio = record_until_enter(device)
            report = verify(item_id, audio, floor_linear)

            print(
                f"  {report.seconds:.2f}s · peak {report.peak_dbfs:.1f} dBFS · "
                f"speech {report.active_dbfs:.1f} dBFS · SNR {report.snr_db:.1f} dB"
            )
            for warning in report.warnings:
                print(f"  warn: {warning}")
            for failure in report.failures:
                print(f"  FAIL: {failure}")

            if not report.ok:
                print("  not written. Retaking.")
                continue

            choice = input("  [Enter] accept · [r] retake  ").strip().lower()
            if choice == "r":
                continue

            sf.write(target, audio, CAPTURE_RATE, subtype=CAPTURE_SUBTYPE)
            meta["takes"][item_id] = asdict(report)
            _write_meta(meta_path, meta)
            print(f"  wrote {target.name}")
            break

    meta["ended"] = _dt.datetime.now().astimezone().isoformat()
    _write_meta(meta_path, meta)

    recorded = sorted(p.stem for p in out_dir.glob("[0-9]*.wav"))
    print(f"\n{len(recorded)} / {len(items)} recorded in {out_dir}")
    if len(recorded) < len(items):
        print("Session incomplete -- Gate 5 needs all of them.")
        return 1
    print("Complete. Next: python data/resample.py --session " + args.session)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
