"""runtime/pipeline.py -- the wiring, and PRD Sec. 4.3's correctness rule.

`Dispatcher` is tested against a real `CommandBus` (real UDP loopback
sockets) and a real `swarm.fsm.FlightStateMachine` -- both already exist and
are not reimplemented here, only wired together. `PipelineRuntime` is tested
with fakes standing in for the not-yet-trained wake model and the LLM decode,
which is exactly the seam `runtime/branch_a.py` and `runtime/parser.py` were
built to expose.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from runtime.branch_a import BranchA
from runtime.bus import CommandBus
from runtime.parser import ParseAborted, ParseResult
from runtime.pipeline import Dispatcher, PipelineRuntime
from schema.schema import Abort, Hover
from swarm.fsm import FlightState, FlightStateMachine


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def bus():
    with CommandBus(port=_free_port(), bind=True) as b:
        yield b


def _flying_fsm() -> FlightStateMachine:
    fsm = FlightStateMachine()
    fsm.handle_command({"intent": "takeoff"})
    fsm.on_altitude_reached()
    assert fsm.state == FlightState.FLYING
    return fsm


# --------------------------------------------------------------------------
# Dispatcher / Sec. 4.3 correctness rule


def test_branch_a_message_is_applied_to_the_fsm(bus: CommandBus) -> None:
    fsm = _flying_fsm()
    dispatcher = Dispatcher(fsm)
    bus.publish("A", Abort(intent="abort"))

    applied = dispatcher.drain(bus, timeout=2.0)

    assert len(applied) == 1
    assert applied[0] == Abort(intent="abort")
    assert fsm.state == FlightState.ABORTED


def test_stale_branch_b_message_is_discarded_after_a_later_branch_a_trigger(bus: CommandBus) -> None:
    """The scenario Sec. 4.3 describes verbatim: Branch A triggers while
    Branch B is mid-inference. The sequence number Branch B's message carries
    was reserved *before* Branch A published (representing the moment Branch
    B started decoding), even though Branch B's message is sent *after*.
    """
    fsm = _flying_fsm()
    dispatcher = Dispatcher(fsm)

    # Branch B starts processing an utterance -- reserves its slot in the
    # sequence before it has anything to publish.
    branch_b_seq = bus.next_seq()

    # While Branch B is still decoding, the operator says "swarm abort".
    bus.publish("A", Abort(intent="abort"))

    # Branch B's decode finally finishes and publishes -- late, but still
    # carrying the sequence number it reserved before the abort.
    bus.publish("B", {"intent": "move", "dir": "north", "dist": 10.0}, seq=branch_b_seq)

    applied = dispatcher.drain(bus, timeout=2.0)

    assert applied[0] == Abort(intent="abort")
    assert applied[1] is None, "the stale move must never reach the FSM"
    assert fsm.state == FlightState.ABORTED, "the stale move must not undo the abort"


def test_branch_b_message_after_the_last_branch_a_trigger_is_applied(bus: CommandBus) -> None:
    """The discard rule must not be trigger-happy: a Branch B message that
    genuinely postdates the last Branch A trigger is legitimate and must
    reach the FSM."""
    fsm = _flying_fsm()
    dispatcher = Dispatcher(fsm)

    bus.publish("A", Hover(intent="hover"))
    bus.publish("B", {"intent": "rotate", "yaw": 45.0})

    applied = dispatcher.drain(bus, timeout=2.0)

    assert len(applied) == 2
    assert applied[1] is not None
    assert applied[1].intent == "rotate"


def test_drain_returns_empty_when_bus_is_idle(bus: CommandBus) -> None:
    fsm = FlightStateMachine()
    dispatcher = Dispatcher(fsm)
    assert dispatcher.drain(bus, timeout=0.05) == []


# --------------------------------------------------------------------------
# PipelineRuntime wiring


@dataclass
class FakeWakeDetector:
    scores: dict[str, float] = field(default_factory=dict)

    def predict(self, frame: object) -> dict[str, float]:
        return self.scores


@dataclass
class FakeParser:
    result: ParseResult | None = None
    abort_called: bool = False
    parse_calls: list[str] = field(default_factory=list)

    def abort(self) -> None:
        self.abort_called = True

    def parse(self, transcript: str) -> ParseResult:
        self.parse_calls.append(transcript)
        if self.result is None:
            raise ParseAborted("no result configured")
        return self.result


def test_on_wake_frame_publishes_and_preempts_the_parser(bus: CommandBus) -> None:
    parser = FakeParser()
    branch_a = BranchA(FakeWakeDetector({"swarm_abort": 0.9}))
    runtime = PipelineRuntime(bus=bus, branch_a=branch_a, parser=parser)

    msg = runtime.on_wake_frame(frame=None)

    assert msg is not None
    assert msg.branch == "A"
    assert msg.command == {"intent": "abort"}
    assert parser.abort_called, "Figure 1's preempt edge must fire on a Branch A trigger"


def test_on_wake_frame_returns_none_when_nothing_triggers(bus: CommandBus) -> None:
    parser = FakeParser()
    branch_a = BranchA(FakeWakeDetector({}))
    runtime = PipelineRuntime(bus=bus, branch_a=branch_a, parser=parser)

    assert runtime.on_wake_frame(frame=None) is None
    assert not parser.abort_called


def test_on_utterance_publishes_the_validated_command(bus: CommandBus, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("runtime.pipeline.transcribe_utterance", lambda path, **_: "go north ten metres")
    parser = FakeParser(result=ParseResult(raw='{"intent":"move","dir":"north","dist":10.0}',
                                            prefill_ms=12.0, decode_ms=34.0))
    branch_a = BranchA(FakeWakeDetector({}))
    runtime = PipelineRuntime(bus=bus, branch_a=branch_a, parser=parser)

    msg = runtime.on_utterance(Path("unused.wav"))

    assert msg is not None
    assert msg.branch == "B"
    assert msg.command["intent"] == "move"
    assert parser.parse_calls == ["go north ten metres"]


def test_on_utterance_reserves_its_sequence_before_transcription(
    bus: CommandBus, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sec. 4.3's ordering guarantee requires the sequence number to be
    reserved before the (possibly slow) transcribe/decode work runs, not
    after -- this is the property `test_stale_branch_b_message_is_discarded`
    relies on, checked here at the `PipelineRuntime` level."""
    seen_seq_at_transcribe_time = {}

    def fake_transcribe(path: Path, **_: object) -> str:
        seen_seq_at_transcribe_time["reserved"] = bus.next_seq() - 1
        return "hold position"

    monkeypatch.setattr("runtime.pipeline.transcribe_utterance", fake_transcribe)
    parser = FakeParser(result=ParseResult(raw='{"intent":"hover"}', prefill_ms=1.0, decode_ms=1.0))
    runtime = PipelineRuntime(bus=bus, branch_a=BranchA(FakeWakeDetector({})), parser=parser)

    msg = runtime.on_utterance(Path("unused.wav"))

    assert msg is not None
    assert msg.seq == seen_seq_at_transcribe_time["reserved"]


def test_on_utterance_publishes_nothing_when_the_decode_is_aborted(bus: CommandBus, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("runtime.pipeline.transcribe_utterance", lambda path, **_: "irrelevant")
    parser = FakeParser(result=None)  # raises ParseAborted
    runtime = PipelineRuntime(bus=bus, branch_a=BranchA(FakeWakeDetector({})), parser=parser)

    assert runtime.on_utterance(Path("unused.wav")) is None
    assert bus.recv(timeout=0.05) is None
