"""The runtime as one process on the Raspberry Pi 5: microphone in, commands out over the bus.

Chapter 4 records that no entry point starts the runtime as one process; only `eval/exp2.py`
assembled the parts, for its trials. This module assembles the same parts the same way -- the
parser under `llama-server`, the trained spotter, the endpointer, the frame loop, and Table 7's
thread allocation, with `llama-server` spawned from cores 1-3 so it inherits their mask -- with
two differences: the frame source is the microphone (`runtime/audio.py`), and the bus addresses
the workstation, where the consumer, the state machine, the link and the simulation run
(`demo/workstation.py`). `Narrator` only prints and logs what each path did, for the camera.

One rule is added here and nowhere else, and it is demonstration-only: `ReflexGate` stops the parse
path publishing an utterance the reflex path already acted on. Both paths hear "swarm hold"; the
parse path's copy draws a newer sequence number than the reflex, so the consumer's ordering rule
(discard parse messages *older* than the last reflex) lets it through, and a misheard copy
overrides the hold. The first live run measured that: 10 spoken "swarm hold", 10 reflex triggers,
and parse-path copies of hover x6, unknown x1, abort x1 ("swarm, halt.") and a wedge formation x2
("swarm, horned."). No measured result was produced through this module, so none changes.

    python runtime/main.py --bus-host 10.42.0.1                 # the demonstration
    python runtime/main.py --level-check                        # microphone level, no pipeline
    python runtime/main.py --bus-host 127.0.0.1 --source take.wav   # rehearsal from a recording

`run_pipeline.sh` starts this file with `--model` and `--state`; `--state` is accepted and unused,
because the flight state lives on the workstation, and the bus host is read from `PFE_BUS_HOST`
when `--bus-host` is not given. The structured JSON log goes to `--log` (default under
`demo_runs/`), not to the terminal.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import logging
import os
import sys
import threading
import time
from collections import deque
from pathlib import Path

if __package__ in (None, ""):  # `python runtime/main.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from runtime.stream import FRAME, pin
from runtime.vad import RATE

REPO_ROOT = Path(__file__).resolve().parent.parent
#: Table 7, as eval/exp2.py pins it: capture, spotter and endpointer on core 0; recogniser and
#: language model on cores 1-3, never concurrently.
FRONT = {0}
BACK = {1, 2, 3}
#: The bus port the workstation listens on; eval/exp2.py's loopback bus used 8766 as well.
BUS_PORT = 8766

_KEYWORD = {"hover": "swarm hold", "abort": "swarm abort"}
_say_lock = threading.Lock()
logger = logging.getLogger("runtime.main")


def say(text: str) -> None:
    with _say_lock:
        print(f"{_dt.datetime.now():%H:%M:%S.%f}"[:-4] + "  " + text, flush=True)


class Narrator:
    """Wraps `PipelineRuntime`, printing and logging each path's outcome. Decides nothing."""

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    def on_wake_frame(self, frame):
        message = self._runtime.on_wake_frame(frame)
        if message is not None:
            intent = message.command.get("intent")
            say(f"REFLEX  '{_KEYWORD.get(intent, intent)}' -> {message.command}  seq={message.seq}")
        return message

    def process(self, audio_path: Path):
        say("PARSE   utterance endpointed; transcribing")
        trace = self._runtime.process(audio_path)
        say(f"PARSE   heard: \"{trace.transcript}\"")
        if trace.aborted:
            say(f"PARSE   decode stopped (seq={trace.seq}); nothing published")
        else:
            say(f"PARSE   -> {trace.message.command}  seq={trace.seq}")
        logger.info("parse path heard %r", trace.transcript, extra={
            "event": "parse_heard", "seq": trace.seq, "transcript": trace.transcript, "raw": trace.raw,
            "aborted": trace.aborted, "stt_ms": round(trace.stt_ms, 1),
            "parse_wall_ms": round(trace.parse_wall_ms, 1)})
        return trace


class ReflexGate:
    """The parse path does not publish an utterance a reflex fired during, or after, before its parse began.

    Wraps both the runtime and the endpointer, so `StreamLoop` is given this one object twice. A
    reflex trigger is kept with the stream time of the frame that fired it; an utterance, with the
    stream time of its start (onset pad included). When the parse worker picks an utterance up,
    any reflex at or after that start suppresses it: the operator said the reflex phrase inside
    it, or after it, and the reflex has already acted. Three cases this closes:

    * the reflex phrase's own parse-path copy (the measured failure above);
    * a trigger the spotter reports just after the endpointer has closed the utterance (seen
      in replay: 0.15 s after, for a command and "swarm hold" spoken in one breath);
    * a command still queued behind a slow parse when the reflex fires. `PipelineRuntime`
      draws the parse sequence number when the worker starts the utterance, not at its
      endpoint, so without this the queued command would be numbered after the hold and
      override it.

    Once a parse has started, it is the ordering rule's business, as before: its number was drawn
    first, so a reflex that fires during transcription or decode discards it on the consumer.
    The window between this check and `PipelineRuntime.process` drawing its number is not closed;
    it is the length of a function call.

    A suppressed utterance is never transcribed: no sequence number is drawn and nothing is
    published.
    """

    def __init__(self, runtime, endpointer) -> None:
        self._runtime = runtime
        self._endpointer = endpointer
        self._stream_s = 0.0                              # frame thread only
        self._lock = threading.Lock()
        self._fired: list[tuple[float, object]] = []      # (stream time, BusMessage), under _lock
        self._pending: deque = deque()                    # Utterances, in StreamLoop's queue order

    def on_wake_frame(self, frame):
        self._stream_s += np.asarray(frame).size / RATE   # end of this frame, as StreamLoop counts it
        message = self._runtime.on_wake_frame(frame)
        if message is not None:
            with self._lock:
                self._fired.append((self._stream_s, message))
            logger.info("reflex fired", extra={
                "event": "reflex_fired", "seq": message.seq, "intent": message.command.get("intent"),
                "stream_s": round(self._stream_s, 3)})
        return message

    def feed(self, chunk):
        utterances = self._endpointer.feed(chunk)
        self._pending.extend(utterances)
        return utterances

    def process(self, audio_path: Path):
        from runtime.pipeline import BranchBTrace

        utterance = self._pending.popleft()               # StreamLoop's worker takes them in order
        with self._lock:
            self._fired = [(t, m) for t, m in self._fired if t >= utterance.start_s]   # later starts only
            fired, owner = self._fired[0] if self._fired else (None, None)
        if owner is None:
            return self._runtime.process(audio_path)
        intent = owner.command.get("intent")
        when = "during it" if fired <= utterance.t0_s else "after it"
        say(f"PARSE   utterance endpointed; reflex #{owner.seq} '{_KEYWORD.get(intent, intent)}' "
            f"fired {when} -- not parsed, the reflex already acted")
        logger.info("parse path suppressed: reflex seq=%d fired %s", owner.seq, when, extra={
            "event": "parse_suppressed_by_reflex", "reflex_seq": owner.seq, "intent": intent,
            "reflex_stream_s": round(fired, 3), "start_s": round(utterance.start_s, 3),
            "end_s": round(utterance.end_s, 3), "t0_s": round(utterance.t0_s, 3)})
        now = time.monotonic()
        return BranchBTrace(seq=-1, transcript="", raw=None, message=None,
                            t_start=now, t_transcribed=now, t_parsed=now, t_published=None)


def _route_logs(path: Path) -> None:
    """Structured JSON to `path`; the terminal keeps only errors, so the camera sees `say()`."""
    from schema.logger import StructuredJsonFormatter

    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(StructuredJsonFormatter())
    for root in ("runtime", "schema", "swarm"):
        logger = logging.getLogger(root)
        logger.setLevel(logging.INFO)
        for existing in logger.handlers:
            existing.setLevel(logging.ERROR)
        logger.addHandler(handler)


def _pin(cores: set[int]) -> None:
    if max(cores) < (os.cpu_count() or 1):
        pin(cores)


def level_check(device: str | None, gain_db: float | None, seconds: float) -> int:
    from runtime.audio import MicSource

    source = MicSource(device, gain_db=gain_db)
    print(f"gain {source.gain_db:+.2f} dB. Speak commands at the golden set's distance (10 cm).")
    print("S1's takes, after its gain, peak between about -28 and -14 dBFS; Ctrl-C to stop.")
    window: list[np.ndarray] = []
    deadline = time.monotonic() + seconds
    try:
        for frame, _ in source:
            window.append(frame)
            if len(window) * FRAME >= RATE:
                x = np.concatenate(window).astype(np.float64) / 32768.0
                peak = 20 * np.log10(np.max(np.abs(x)) + 1e-9)
                rms = 20 * np.log10(np.sqrt(np.mean(x**2)) + 1e-9)
                bar = "#" * max(0, int((peak + 60) / 2))
                print(f"{source.device_name}  peak {peak:6.1f} dBFS  rms {rms:6.1f} dBFS  "
                      f"overruns {source.overflows}  {bar}", flush=True)
                window.clear()
            if time.monotonic() > deadline:
                break
    except KeyboardInterrupt:
        pass
    finally:
        source.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bus-host", default=os.environ.get("PFE_BUS_HOST"),
                    help="the workstation's address on the device-workstation link (or PFE_BUS_HOST)")
    ap.add_argument("--bus-port", type=int, default=BUS_PORT)
    ap.add_argument("--model", type=Path, default=None, help="GGUF (default: the deployed parser, eval/exp3.GGUF)")
    ap.add_argument("--device", default=None, help="capture device name or index (default: the USB microphone)")
    ap.add_argument("--gain-db", type=float, default=None, help="fixed capture gain (default: S1's session gain)")
    ap.add_argument("--source", type=Path, default=None, help="replay a 16 kHz WAV instead of the microphone")
    ap.add_argument("--level-check", action="store_true", help="print the microphone level and exit")
    ap.add_argument("--seconds", type=float, default=60.0, help="--level-check duration")
    ap.add_argument("--log", type=Path, default=None, help="structured JSON log (default demo_runs/pi-<time>.jsonl)")
    ap.add_argument("--state", default=None, help=argparse.SUPPRESS)  # run_pipeline.sh passes it; unused
    args = ap.parse_args(argv)

    if args.level_check:
        return level_check(args.device, args.gain_db, args.seconds)
    if not args.bus_host:
        ap.error("--bus-host (or PFE_BUS_HOST) is required: the workstation's address on the link")

    log = args.log or REPO_ROOT / "demo_runs" / f"pi-{_dt.datetime.now():%Y%m%d-%H%M%S}.jsonl"

    from eval.exp3 import GGUF
    from runtime.branch_a import load_trained
    from runtime.bus import CommandBus
    from runtime.parser import CommandParser
    from runtime.pipeline import PipelineRuntime
    from runtime.stream import StreamLoop, WavSource
    from runtime.vad import Endpointer

    _route_logs(log)
    gguf = args.model or GGUF
    say(f"starting llama-server on {gguf.name} (cores {sorted(BACK)}); this takes a few seconds")
    _pin(BACK)                          # llama-server inherits the spawning thread's mask
    parser, server = CommandParser.for_gguf(gguf)
    _pin(FRONT)

    bus = CommandBus(host=args.bus_host, port=args.bus_port)
    source = None
    try:
        runtime = PipelineRuntime(bus=bus, branch_a=load_trained(), parser=parser)
        gate = ReflexGate(Narrator(runtime), Endpointer())
        loop = StreamLoop(gate, gate, front_cores=FRONT, back_cores=BACK)
        if args.source is not None:
            import soundfile as sf

            audio, rate = sf.read(args.source, dtype="int16")
            if rate != RATE or audio.ndim != 1:
                ap.error(f"{args.source}: need 16 kHz mono, got {rate} Hz, shape {audio.shape}")
            pad = np.zeros(RATE, dtype=np.int16)
            source = WavSource(np.concatenate([pad, audio, pad]))
            what = f"replaying {args.source}"
        else:
            from runtime.audio import MicSource

            source = MicSource(args.device, gain_db=args.gain_db)
            what = f"live microphone, gain {source.gain_db:+.2f} dB"
        say(f"READY   {what}; publishing to {args.bus_host}:{args.bus_port}; log {log}")
        result = loop.run(source)
        say(f"source ended: {len(result.branch_a)} reflex, {len(result.branch_b)} parse-path utterances")
    except KeyboardInterrupt:
        say("stopped")
    finally:
        if hasattr(source, "close"):
            source.close()
        server.stop()
        bus.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
