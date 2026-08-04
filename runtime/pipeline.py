"""End-to-end wiring: wake -> ASR -> LLM -> validator -> FSM.

This module contains no new decision logic of its own. Every stage it calls
already exists and is frozen or previously built:

    wake        runtime/branch_a.py    Table 5's two-intent membership rule
    ASR         runtime/stt.py         wraps data/asr.py's whisper.cpp config
    LLM         runtime/parser.py      wraps llama.cpp under the GBNF grammar
    validator   schema/validate.py     layer 2 -- clamps and logs, never rejects
    FSM         swarm/fsm.py           layer 3 -- Table 9 legality

What is new here is the wiring between them: which stage's output feeds the
next, and PRD Sec. 4.3's correctness rule for the one place both branches
meet -- the bus.

Audio capture and VAD (Table 4's `runtime/audio.py`, `runtime/vad.py`) are
NOT built here. This task's scope, as given, is exactly the five stages
above; Branch B's entry point below is therefore a already-segmented
utterance (a WAV path), not a live audio stream. Building the capture and
endpointing stages is separate work.

Similarly, no trained openWakeWord model exists yet (see
`runtime/branch_a.py`'s docstring) -- `on_wake_frame` below is exercised in
tests against a fake `WakeDetector`, and will run unchanged once a trained
model is injected.
"""

from __future__ import annotations

from pathlib import Path

from schema.logger import get_structured_logger
from schema.schema import Command
from schema.validate import validate
from swarm.fsm import FlightStateMachine

from runtime.branch_a import BranchA
from runtime.bus import BusMessage, CommandBus
from runtime.parser import CommandParser, ParseAborted
from runtime.stt import transcribe_utterance

__all__ = ["Dispatcher", "PipelineRuntime"]

logger = get_structured_logger("runtime.pipeline")


class Dispatcher:
    """The bus's consumer side. Owns PRD Sec. 4.3's correctness rule and the FSM.

    Verbatim, Sec. 4.3: "The state machine discards any Branch B message
    whose sequence number is lower than the highest Branch A message already
    applied. A stale Branch B result therefore cannot take effect, whether or
    not its decode was stopped."

    The rule lives here rather than inside `swarm.fsm.FlightStateMachine`
    itself: the FSM's job (Table 9 legality) does not change based on which
    branch a command arrived from, and folding a bus-specific staleness check
    into it would make `swarm/fsm.py` -- already built, not to be
    reimplemented -- depend on the bus. `Dispatcher` is the seam instead.
    """

    def __init__(self, fsm: FlightStateMachine) -> None:
        self.fsm = fsm
        self._highest_branch_a_seq = -1

    def apply(self, msg: BusMessage) -> Command | None:
        if msg.branch == "A":
            self._highest_branch_a_seq = max(self._highest_branch_a_seq, msg.seq)
        elif msg.seq < self._highest_branch_a_seq:
            logger.info(
                "Stale Branch B message discarded: seq=%d < highest_branch_a_seq=%d",
                msg.seq,
                self._highest_branch_a_seq,
                extra={
                    "event": "bus_stale_branch_b_discarded",
                    "seq": msg.seq,
                    "highest_branch_a_seq": self._highest_branch_a_seq,
                },
            )
            return None
        return self.fsm.handle_command(msg.command)

    #: After the first message, a short grace period rather than a hard 0.0:
    #: a burst published just before `drain()` is called can still be sitting
    #: in the kernel's UDP receive queue a beat later, and a true zero
    #: timeout would stop draining before it catches up (observed as a
    #: flaky `BlockingIOError` race in `runtime/test_pipeline.py`).
    _DRAIN_GRACE_SECONDS = 0.05

    def drain(self, bus: CommandBus, *, timeout: float | None = None) -> list[Command | None]:
        """Apply every currently-available message, in arrival order.

        Only the wait for the *first* message honours `timeout` in full;
        subsequent messages use the short grace period above so a burst does
        not wait the full `timeout` per message.
        """
        applied: list[Command | None] = []
        remaining_timeout = timeout
        while True:
            msg = bus.recv(timeout=remaining_timeout)
            if msg is None:
                break
            applied.append(self.apply(msg))
            remaining_timeout = self._DRAIN_GRACE_SECONDS
        return applied


class PipelineRuntime:
    """The two publishing paths, wired against one bus and one parser.

    Branch A: a wake-frame poll that, on trigger, both raises Figure 1's
    "preempt" flag (aborting any in-flight Branch B decode) and publishes
    immediately -- Branch A never waits on Branch B.

    Branch B: transcribe -> parse -> validate -> publish. A decode aborted by
    Branch A (or by any transport fault) simply publishes nothing; Sec. 4.3
    does not require it to -- the correctness guarantee is the sequence
    number on whatever Branch A already published, not the absence of a
    Branch B message.
    """

    def __init__(self, *, bus: CommandBus, branch_a: BranchA, parser: CommandParser) -> None:
        self.bus = bus
        self.branch_a = branch_a
        self.parser = parser

    def on_wake_frame(self, frame: object) -> BusMessage | None:
        command = self.branch_a.poll(frame)
        if command is None:
            return None
        self.parser.abort()
        return self.bus.publish("A", command)

    def on_utterance(self, audio_path: Path) -> BusMessage | None:
        # Reserved *before* transcription/decode starts, not at publish time
        # (see `CommandBus.next_seq`) -- Sec. 4.3's ordering rule depends on a
        # slow, later-preempted decode still carrying the older number.
        seq = self.bus.next_seq()
        transcript = transcribe_utterance(audio_path)
        try:
            result = self.parser.parse(transcript)
        except ParseAborted:
            logger.info(
                "Branch B utterance produced no command",
                extra={"event": "branch_b_no_command", "audio_path": str(audio_path)},
            )
            return None
        command = validate(result.raw)
        return self.bus.publish("B", command, seq=seq)
