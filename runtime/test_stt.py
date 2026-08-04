"""runtime/stt.py -- wiring against the real whisper.cpp binary and model.

`data/asr.py` already owns and tests the `whisper.cpp` invocation itself
(batch transcription, sidecar handling, the domain prompt); what this module
adds is the single-utterance entry point the live pipeline calls, so this
test is about wiring, not re-testing `data/asr.py`. It runs against the real
binary and the real `tiny.en` model already on this workstation (Session 03's
`find_whisper()` discovery), and a real golden-set clip -- skipped, not
failed, on a checkout that has none of those.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from data.harvest_asr_garbage import find_whisper
from runtime.stt import transcribe_utterance

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_CLIP = REPO_ROOT / "data" / "audio" / "s1_16k" / "0001.wav"


@pytest.mark.slow
def test_transcribe_utterance_runs_the_real_binary() -> None:
    try:
        find_whisper()
    except FileNotFoundError:
        pytest.skip("whisper.cpp binary/model not found on this machine")
    if not GOLDEN_CLIP.is_file():
        pytest.skip(f"golden clip not present at {GOLDEN_CLIP}")

    text = transcribe_utterance(GOLDEN_CLIP)

    assert isinstance(text, str)
    assert text != "", "a real, in-domain clip must not come back empty"


def test_transcribe_utterance_returns_empty_string_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from data.asr import Transcription

    def fake_transcribe(path: Path, **_: object) -> Transcription:
        return Transcription(path, "", False, "whisper exit 1")

    monkeypatch.setattr("runtime.stt.transcribe", fake_transcribe)

    assert transcribe_utterance(Path("nonexistent.wav")) == ""
