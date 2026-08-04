"""runtime/bus.py -- Table 4's Command Bus.

Real UDP sockets on loopback, not a mock transport: Table 4 specifies
UDP/JSON, and a fake transport would not catch a serialisation mistake that
only shows up once bytes actually cross a socket.
"""

from __future__ import annotations

import socket

import pytest

from runtime.bus import BusMessage, CommandBus
from schema.schema import Abort, Hover


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def bus():
    port = _free_port()
    with CommandBus(port=port, bind=True) as b:
        yield b


def test_publish_recv_roundtrip(bus: CommandBus) -> None:
    published = bus.publish("A", {"intent": "hover"})
    received = bus.recv(timeout=2.0)
    assert received is not None
    assert received == published


def test_recv_timeout_returns_none(bus: CommandBus) -> None:
    assert bus.recv(timeout=0.05) is None


def test_publish_accepts_pydantic_model(bus: CommandBus) -> None:
    bus.publish("A", Hover(intent="hover"))
    received = bus.recv(timeout=2.0)
    assert received is not None
    assert received.command == {"intent": "hover"}
    assert received.branch == "A"


def test_sequence_is_monotonic_across_both_branches(bus: CommandBus) -> None:
    """One counter, shared by both branches -- this is what makes Sec. 4.3's
    'lower than the highest Branch A message already applied' comparison
    meaningful at all: without a shared counter, a Branch A and a Branch B
    sequence number would not be comparable."""
    msgs = [
        bus.publish("B", {"intent": "move", "dir": "north", "dist": 5.0}),
        bus.publish("A", Hover(intent="hover")),
        bus.publish("B", {"intent": "unknown"}),
        bus.publish("A", Abort(intent="abort")),
    ]
    seqs = [m.seq for m in msgs]
    assert seqs == sorted(seqs)
    assert len(set(seqs)) == len(seqs)


def test_next_seq_reserves_ahead_of_publish(bus: CommandBus) -> None:
    """Branch B reserves a sequence number when it *starts* processing an
    utterance (`PipelineRuntime.on_utterance`), then publishes with that same
    number once the (possibly slow) decode finishes -- not a fresh one drawn
    at publish time. `next_seq()` is the primitive that makes that possible."""
    reserved = bus.next_seq()
    # Something else publishes in between, as Branch A would while Branch B
    # is still decoding.
    bus.publish("A", Hover(intent="hover"))
    msg = bus.publish("B", {"intent": "land"}, seq=reserved)
    assert msg.seq == reserved


def test_invalid_branch_rejected(bus: CommandBus) -> None:
    with pytest.raises(ValueError):
        bus.publish("C", {"intent": "hover"})  # type: ignore[arg-type]


def test_recv_without_bind_raises() -> None:
    with CommandBus(port=_free_port(), bind=False) as unbound:
        with pytest.raises(RuntimeError):
            unbound.recv(timeout=0.01)


def test_message_json_roundtrip() -> None:
    original = BusMessage(seq=7, branch="B", command={"intent": "abort"}, t_publish=123.456)
    restored = BusMessage.from_json(original.to_json())
    assert restored == original


def test_message_from_json_rejects_unknown_branch() -> None:
    bad = '{"seq": 1, "branch": "Z", "command": {}, "t_publish": 0.0}'
    with pytest.raises(ValueError):
        BusMessage.from_json(bad)
