"""The full chain, for real: ASR -> LLM -> validator -> FSM, one golden clip.

Branch A is exercised elsewhere (`runtime/test_branch_a.py`,
`runtime/test_pipeline.py`) against a fake detector, because no trained
keyword-spotter model exists yet -- see `runtime/branch_a.py`'s module
docstring. Everything downstream of a transcript, though, has a real binding
already on this workstation, so this test runs the real chain: the real
`whisper.cpp` binary transcribes a real golden-set clip, the real
`llama-server` decodes it under the real GBNF grammar, the real
`schema.validate.validate` clamps the result, it crosses a real UDP socket,
and the real `swarm.fsm.FlightStateMachine` applies it. Nothing in this
file is a mock. Skipped, not failed, on a checkout missing any of the
binaries or assets -- see each skip reason for which.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from data.harvest_asr_garbage import find_whisper
from runtime.branch_a import BranchA
from runtime.bus import CommandBus
from runtime.parser import LLAMA_SERVER, REPO_ROOT, CommandParser
from runtime.pipeline import Dispatcher, PipelineRuntime
from schema.schema import COMMAND_MODELS
from swarm.fsm import FlightState, FlightStateMachine

GGUF = REPO_ROOT / "gguf" / "smollm2-360m-instruct-Q4_K_M.gguf"
GOLDEN_CLIP = REPO_ROOT / "data" / "audio" / "s1_16k" / "0001.wav"


class _NeverTriggers:
    """A `WakeDetector` that never fires -- this test is Branch B only."""

    def predict(self, frame: object) -> dict[str, float]:
        return {}


def _free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.mark.slow
def test_golden_clip_reaches_the_fsm_through_the_real_chain() -> None:
    try:
        find_whisper()
    except FileNotFoundError:
        pytest.skip("whisper.cpp binary/model not found on this machine")
    if not LLAMA_SERVER.is_file():
        pytest.skip(f"llama-server not built at {LLAMA_SERVER}")
    if not GGUF.is_file():
        pytest.skip(f"gguf artefact not present at {GGUF}")
    if not GOLDEN_CLIP.is_file():
        pytest.skip(f"golden clip not present at {GOLDEN_CLIP}")

    with CommandBus(port=_free_udp_port(), bind=True) as bus:
        fsm = FlightStateMachine()
        fsm.handle_command({"intent": "takeoff"})
        fsm.on_altitude_reached()
        assert fsm.state == FlightState.FLYING

        dispatcher = Dispatcher(fsm)
        parser, server = CommandParser.for_gguf(GGUF, port=_free_tcp_port())
        try:
            runtime = PipelineRuntime(bus=bus, branch_a=BranchA(_NeverTriggers()), parser=parser)

            published = runtime.on_utterance(GOLDEN_CLIP)
            assert published is not None, "a real golden clip must produce a Branch B command"
            assert published.branch == "B"

            applied = dispatcher.drain(bus, timeout=5.0)
        finally:
            server.stop()

    assert len(applied) == 1
    assert applied[0] is None or isinstance(applied[0], COMMAND_MODELS)
    # The FSM either dispatched the command or, if it was illegal for FLYING /
    # fell back to Hover, that fallback is itself the correct behaviour --
    # this test's claim is that the chain runs end to end and the FSM sees
    # exactly one well-formed decision, not that any one intent was decoded.
