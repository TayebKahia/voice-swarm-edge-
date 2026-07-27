#!/usr/bin/env python3
"""The deployed `whisper.cpp` configuration, in one place.

Round-trip augmentation is only worth doing if the transcripts it produces carry
**the error distribution of the model that will actually run** (`02_dataset_plan.md`
§4). That means the same weights, the same decoding flags and the same initial
prompt as the runtime path --- a round-trip through a differently-configured
decoder teaches the LLM to repair errors it will never see, and leaves the ones it
will. So the configuration lives here, and both the augmentation pipeline and the
runtime read it from this module rather than each carrying a copy that can drift.

`tiny.en` with the domain prompt is the spike S6 decision: it matched `base.en`
accuracy at a quarter of the compute, and the prompt is what stops "swarm" being
heard as "swam" (`spikes/reports/S6_asr_accent_check.md` §3).
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # `python data/asr.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.harvest_asr_garbage import find_whisper

#: Verbatim from `spikes/s6_asr_accent_check.py:46`. Changing this changes the
#: error distribution of every round-trip transcript, so it is a dataset-level
#: constant, not a tuning knob.
DOMAIN_PROMPT = (
    "swarm, drone, takeoff, land, hover, abort, move, north, south, east, west, "
    "forward, back, up, down, altitude, rotate, degrees, formation, circle, line, "
    "wedge, grid, speed, stop"
)

#: Threads. Four on the workstation; the Pi runtime pins three (Table 7). Thread
#: count does not affect greedy decoding output, only wall-clock.
DEFAULT_THREADS = 4

#: Files per `whisper-cli` invocation. The model load dominates a single short
#: clip, so batching is most of the speed-up; the cap keeps the argv short and
#: keeps a crash from losing more than a batch.
BATCH_SIZE = 32


@dataclass(frozen=True)
class Transcription:
    """One file's transcript, or the reason there is not one."""

    path: Path
    text: str
    ok: bool
    error: str = ""


def _clean(text: str) -> str:
    """Collapse `whisper.cpp`'s output to a single stripped line.

    Multi-sentence audio comes back as several lines; the corpus is one utterance
    per file, so they are joined rather than treated as separate items.
    """
    return " ".join(line.strip() for line in text.splitlines() if line.strip()).strip()


def transcribe_batch(
    paths: Sequence[Path],
    *,
    binary: Path | None = None,
    model: Path | None = None,
    prompt: str | None = DOMAIN_PROMPT,
    threads: int = DEFAULT_THREADS,
    batch_size: int = BATCH_SIZE,
) -> list[Transcription]:
    """Transcribe `paths`, returning one result per input in the same order.

    `-otxt` is used rather than parsing stdout. Stdout gives one line per
    *sentence*, not per file, so a two-sentence clip or a clip whisper declines to
    transcribe at all would silently shift every subsequent transcript onto the
    wrong row --- a failure that produces a plausible-looking corpus with
    systematically mismatched labels.

    The sidecars are removed before the run and again after being read. Leaving them
    in place turns a *later* failure into silent bad data: if whisper declines a file
    on a second run, an untouched sidecar from the first is still on disk, still
    readable, and would be returned as though it were this run's output. Deleting up
    front means a missing sidecar always means "this invocation produced nothing",
    which is what the branch below assumes.
    """
    if binary is None or model is None:
        found_binary, found_model = find_whisper()
        binary = binary or found_binary
        model = model or found_model

    results: list[Transcription] = []
    for start in range(0, len(paths), batch_size):
        batch = list(paths[start : start + batch_size])
        command = [str(binary), "-m", str(model), "-nt", "-otxt", "-t", str(threads)]
        if prompt:
            command += ["--prompt", prompt]
        for path in batch:
            command += ["-f", str(path)]

        sidecars = [path.with_name(path.name + ".txt") for path in batch]
        for sidecar in sidecars:
            sidecar.unlink(missing_ok=True)

        completed = subprocess.run(command, capture_output=True, text=True)
        for path, sidecar in zip(batch, sidecars):
            if completed.returncode != 0 and not sidecar.is_file():
                results.append(
                    Transcription(path, "", False, f"whisper exit {completed.returncode}")
                )
                continue
            if not sidecar.is_file():
                results.append(Transcription(path, "", False, "no transcript written"))
                continue
            results.append(Transcription(path, _clean(sidecar.read_text(encoding="utf-8")), True))

        for sidecar in sidecars:
            sidecar.unlink(missing_ok=True)
    return results


def transcribe(path: Path, **kwargs) -> Transcription:
    """Transcribe a single file. Prefer `transcribe_batch` for a corpus."""
    return transcribe_batch([path], **kwargs)[0]
