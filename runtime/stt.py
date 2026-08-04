"""Branch B, stage 1 -- speech recognition (Table 4's `stt.py`).

Wraps `data/asr.py`'s single-file `transcribe()` rather than re-deriving the
`whisper.cpp` invocation. `data/asr.py`'s own docstring is explicit about why
that module, and not a second copy, owns the command line: the augmentation
pipeline and the runtime must decode with the same weights, the same flags and
the same initial prompt, or the round-trip corpus stops describing the error
distribution the deployed model will actually see. Duplicating the invocation
here would silently reopen exactly that gap.

No new decoding logic lives in this module. `find_whisper()` (via
`data/asr.py`) locates the binary and model the same way the offline corpus
tooling does, so a workstation and a Pi checkout each find their own without
a runtime-specific config path to keep in sync.
"""

from __future__ import annotations

from pathlib import Path

from data.asr import DEFAULT_THREADS, DOMAIN_PROMPT, Transcription, transcribe

__all__ = ["transcribe_utterance"]


def transcribe_utterance(path: Path, *, threads: int = DEFAULT_THREADS) -> str:
    """Transcript for one segmented utterance.

    Returns `""` on failure rather than raising: an empty or garbled
    transcript is not a new failure mode for the downstream stages to learn --
    it is the same "no valid command" input the LLM and the validator already
    have to handle for an out-of-domain utterance (NFR-18's failure mode,
    STATE.md), so it is passed through rather than special-cased here.
    """
    result: Transcription = transcribe(path, prompt=DOMAIN_PROMPT, threads=threads)
    return result.text if result.ok else ""
