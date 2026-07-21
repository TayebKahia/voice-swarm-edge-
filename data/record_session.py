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

#: Mains hum. S0 found the AC charger raising the floor by ~22 dB with 50/100 Hz
#: energy dominating, and it is the one contaminant on this chain that is
#: diagnosable from the signal rather than guessed at: a 3.5 mm lavalier through
#: an unshielded USB dongle is an antenna, so the *share* of energy in the mains
#: bands says whether the floor is room tone or pickup.
MAINS_HZ = 50.0
MAINS_HARMONICS = 3
MAINS_BANDWIDTH_HZ = 5.0
MAINS_SHARE_WARN = 0.25

#: The floor is estimated as this percentile of 20 ms frame energies, not as the
#: RMS of the whole capture. Room tone is stationary; the things that ruin a
#: five-second measurement --- a chair creak, a swallow, a keystroke, a car --- are
#: not, and a plain RMS is dominated by them. A `--check-room` log taken in a room
#: that was genuinely quiet still swung 20 dB window to window for exactly that
#: reason. A low percentile reads the quiet bed underneath the transients, which
#: is the quantity every nominal SNR in Exp-3 is actually defined against.
FLOOR_PERCENTILE = 20.0
FLOOR_FRAME_MS = 20.0

BLOCK_FRAMES = 2_400  # 50 ms at 48 kHz

#: Live meter, matching `spikes/test_boya_live.py` so the two read the same.
METER_WIDTH = 20
METER_FLOOR_DBFS = -60.0
METER_REFRESH_BLOCKS = 2  # redraw every ~100 ms; faster just flickers


def dbfs(level: float) -> float:
    return 20.0 * np.log10(max(level, 1e-12))


def centred(x: np.ndarray) -> np.ndarray:
    """The signal with its DC offset removed --- for *measurement only*.

    S0 measured this chain at a constant +0.0065, which is about -43.7 dBFS: more
    than 20 dB above the room floor it also measured. Any RMS taken without
    removing it is reading the hardware bias rather than the room, and every take
    in a session would then score ~0 dB over the "floor" and be refused as too
    quiet. The meter, the floor and `verify` all measure on the centred signal.

    The masters keep the offset. `audio/s1/` is what the ADC produced and is never
    written to (ADR-0005 D1); `data/resample.py` removes the offset in the derived
    16 kHz corpus, where it is a declared step and is recorded per file.
    """
    if x.size == 0:
        return x
    return x - float(np.mean(x, dtype=np.float64))


def noise_floor(audio: np.ndarray, sample_rate: int = CAPTURE_RATE) -> float:
    """Robust room-tone level: a low percentile of short-frame RMS, linear scale.

    Falls back to the whole-signal RMS when there is not enough audio to frame.
    """
    signal = centred(audio)
    frame = max(1, int(round(sample_rate * FLOOR_FRAME_MS / 1000.0)))
    if signal.size < frame * 4:
        return rms(signal)
    usable = (signal.size // frame) * frame
    frames = signal[:usable].reshape(-1, frame)
    energies = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1))
    return float(np.percentile(energies, FLOOR_PERCENTILE))


def mains_share(audio: np.ndarray, sample_rate: int = CAPTURE_RATE) -> float:
    """Fraction of the signal's energy sitting in the mains bands.

    Returns 0.0 for a signal too short to resolve 50 Hz. A high share is the
    fingerprint of electrical pickup rather than a noisy room, and the two have
    completely different fixes -- one is a cable or a power supply, the other is
    a fan or a window.
    """
    if audio.size < sample_rate // 4:
        return 0.0
    windowed = centred(audio) * np.hanning(audio.size)
    spectrum = np.abs(np.fft.rfft(windowed)) ** 2
    freqs = np.fft.rfftfreq(audio.size, 1.0 / sample_rate)
    total = float(spectrum.sum())
    if total <= 0.0:
        return 0.0
    hum = 0.0
    for harmonic in range(1, MAINS_HARMONICS + 1):
        centre = MAINS_HZ * harmonic
        band = (freqs >= centre - MAINS_BANDWIDTH_HZ) & (freqs <= centre + MAINS_BANDWIDTH_HZ)
        hum += float(spectrum[band].sum())
    return hum / total


def meter(rms_dbfs: float, peak_dbfs: float, status: str) -> str:
    """One line of VU, `[####----------------] -47.2 dBFS | Pk: -37.5 dB | OK`."""
    filled = int(np.clip((rms_dbfs - METER_FLOOR_DBFS) / -METER_FLOOR_DBFS, 0.0, 1.0) * METER_WIDTH)
    bar = "#" * filled + "-" * (METER_WIDTH - filled)
    return f"[{bar}] {rms_dbfs:6.1f} dBFS | Pk: {peak_dbfs:6.1f} dB | {status}"


def live_status(peak_dbfs: float, floor_dbfs: float, clipped: int) -> str:
    """What the meter says about the take *in progress*.

    Thresholded against the room floor measured at session start rather than
    against absolute dBFS: the BOYA runs 16 dB under Table 22's target, so a fixed
    "-20 dBFS or it is too quiet" rule would condemn every usable take.
    """
    if clipped:
        return "\u274c CLIPPED"
    over = peak_dbfs - floor_dbfs
    if over < MIN_SNR_DB:
        return "\u274c TOO QUIET"
    if over < GOOD_SNR_DB:
        return "\u26a0\ufe0f  QUIET"
    return "\u2705 OK"


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


def record_until_enter(
    device: int, floor_dbfs: float = -60.0, max_seconds: float = MAX_SECONDS
) -> np.ndarray:
    """Stream mono float32 at 48 kHz until the author presses Enter or the cap hits.

    Draws a live VU meter while it runs. Watching the level is the only way to
    catch a mic knocked off-axis, a dead USB adapter or a hot take *during* the
    90 minutes; `verify` catches them afterwards, which costs a retake each time.
    """
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
    peak_dbfs = -120.0
    clipped = 0
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

            centred_block = centred(block)
            block_peak = float(np.max(np.abs(centred_block))) if centred_block.size else 0.0
            peak_dbfs = max(peak_dbfs, dbfs(block_peak))
            clipped += int(np.count_nonzero(np.abs(block) >= CLIP_LEVEL))
            if len(collected) % METER_REFRESH_BLOCKS == 0:
                rms_dbfs = dbfs(rms(centred_block))
                status = live_status(peak_dbfs, floor_dbfs, clipped)
                print(
                    f"\033[2K\r  {total / CAPTURE_RATE:5.1f}s {meter(rms_dbfs, peak_dbfs, status)}",
                    end="",
                    flush=True,
                )
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
    """Capture of a known length, metered --- used for the silence reference.

    Metered because watching the floor for five seconds is how a fan, a fridge
    compressor or a passing car gets noticed before it is baked into the number
    every nominal SNR in Exp-3 is measured against.
    """
    sd = _sounddevice()
    total_frames = int(seconds * CAPTURE_RATE)
    collected: list[np.ndarray] = []
    peak_dbfs = -120.0

    with sd.InputStream(
        device=device,
        samplerate=CAPTURE_RATE,
        channels=1,
        dtype="float32",
        blocksize=BLOCK_FRAMES,
    ) as stream:
        stream.read(int(WARMUP_SECONDS * CAPTURE_RATE))
        gathered = 0
        while gathered < total_frames:
            block, _ = stream.read(min(BLOCK_FRAMES, total_frames - gathered))
            mono = block[:, 0].copy()
            collected.append(mono)
            gathered += mono.size

            centred_block = centred(mono)
            peak_dbfs = max(peak_dbfs, dbfs(float(np.max(np.abs(centred_block)))))
            if len(collected) % METER_REFRESH_BLOCKS == 0:
                rms_dbfs = dbfs(rms(centred_block))
                print(
                    f"\033[2K\r  {gathered / CAPTURE_RATE:5.1f}s "
                    f"{meter(rms_dbfs, peak_dbfs, 'room tone')}",
                    end="",
                    flush=True,
                )
    print()
    return np.concatenate(collected).astype(np.float32) if collected else np.zeros(0, dtype=np.float32)


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
    dc_offset: float
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
    """Measure the take. Levels come from the centred signal, clipping from the raw.

    The split matters. Every level here is a comparison against the room floor, and
    a DC offset inflates both sides of that comparison by a constant that has
    nothing to do with the room --- on this chain S0 measured +0.0065, some 20 dB
    above the floor itself, which is enough to make every take read as ~0 dB of
    headroom and be refused. Clipping is the opposite case: it is a property of the
    samples the ADC actually wrote, so it is counted on the raw signal, where a
    offset that pushes peaks into the rail is exactly what must be caught.
    """
    seconds = audio.size / CAPTURE_RATE
    signal = centred(audio)
    offset = float(np.mean(audio, dtype=np.float64)) if audio.size else 0.0
    peak = float(np.max(np.abs(signal))) if signal.size else 0.0
    active = active_speech_rms(signal, CAPTURE_RATE) if signal.size else 0.0
    clipped = int(np.count_nonzero(np.abs(audio) >= CLIP_LEVEL))
    snr = dbfs(active) - dbfs(floor_linear)
    lead, tail = _speech_bounds(signal, floor_linear)

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
        dc_offset=round(offset, 6),
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


def measure_room(device: int, seconds: float = SILENCE_REFERENCE_SECONDS) -> tuple[float, float, float]:
    """Record room tone and return (floor dBFS, mains share, DC offset)."""
    silence = record_fixed(device, seconds)
    dc = float(np.mean(silence, dtype=np.float64)) if silence.size else 0.0
    return dbfs(noise_floor(silence)), mains_share(silence), dc


def report_room(floor_dbfs: float, hum: float, dc: float) -> bool:
    """Print the verdict and the diagnosis. Returns True if the room passes."""
    passed = floor_dbfs <= MAX_ROOM_FLOOR_DBFS
    print(f"  DC offset:  {dc:+.6f}  ({dbfs(abs(dc)):.1f} dBFS) -- removed before measuring")
    print(
        f"  room floor: {floor_dbfs:6.2f} dBFS  (need <= {MAX_ROOM_FLOOR_DBFS:.0f})  "
        f"{'PASS' if passed else 'FAIL'}"
    )
    print(
        f"  mains hum:  {hum:6.1%} of the energy at {MAINS_HZ:.0f} Hz and its harmonics"
        f"   [floor = p{FLOOR_PERCENTILE:.0f} of 20 ms frames]"
    )
    if hum >= MAINS_SHARE_WARN:
        print(
            "\n  That is electrical pickup, not a noisy room, and no amount of quiet\n"
            "  fixes it. In order of how often it works:\n"
            "    1. Unplug the AC charger -- S0 measured it adding ~22 dB of exactly this.\n"
            "    2. Move the mic cable away from power cables, power strips and chargers.\n"
            "    3. Unplug anything else from USB; move away from monitors and fluorescents.\n"
            "    4. Try a different room, or a different wall."
        )
    elif not passed:
        print(
            "\n  Broadband, so it is the room rather than the wiring: a fan, a fridge,\n"
            "  a computer, traffic through a window. Find it and stop it."
        )
    return passed


def check_room(device: int) -> int:
    """Loop the room measurement so the author can hunt a hum source live."""
    print("Room check. Ctrl+C to stop.\n")
    try:
        while True:
            floor_dbfs, hum, dc = measure_room(device, seconds=3.0)
            report_room(floor_dbfs, hum, dc)
            print()
    except KeyboardInterrupt:
        return 0


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
        "--check-room",
        action="store_true",
        help="measure the floor and the mains-hum share on a loop; record nothing",
    )
    parser.add_argument(
        "--skip-floor",
        action="store_true",
        help="reuse the floor from a previous run of this session instead of measuring",
    )
    args = parser.parse_args(argv)

    if args.list_devices:
        list_devices()
        return 0

    if args.check_room:
        device, device_name = find_capture_device(args.device)
        print(f"capture device: [{device}] {device_name}\n")
        return check_room(device)

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
        measured, hum, dc = (
            round(dbfs(noise_floor(silence)), 2),
            mains_share(silence),
            float(np.mean(silence, dtype=np.float64)) if silence.size else 0.0,
        )
        meta["floor_rms_dbfs"] = round(dbfs(rms(centred(silence))), 2)
        floor_dbfs = measured
        meta["dc_offset"] = round(dc, 6)
        meta["mains_share"] = round(hum, 4)
        sf.write(out_dir / "_room_silence.wav", silence, CAPTURE_RATE, subtype=CAPTURE_SUBTYPE)
        if not report_room(measured, hum, dc):
            print(
                "\n  A floor this high contaminates every nominal SNR level in Exp-3 --\n"
                "  it is the denominator of every one of them. Fix it before recording.\n"
                "  `python data/record_session.py --check-room` loops this measurement."
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
            audio = record_until_enter(device, floor_dbfs)
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
