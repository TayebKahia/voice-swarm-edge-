"""Command Bus (PRD Sec. 4.1 Table 4, Sec. 4.3).

Table 4's responsibility for this module is narrow: "Publish and subscribe,
monotonic sequence numbers, branch tag." Nothing else. In particular, the
correctness rule Sec. 4.3 describes ("the state machine discards any Branch B
message whose sequence number is lower than the highest Branch A message
already applied") is NOT implemented here -- Sec. 4.3 assigns that check to
the state machine, and it is wired in `runtime/pipeline.py`'s `Dispatcher`,
which consumes this bus. Keeping the split matches Sec. 4's own decision 2:
"a minimal Command Bus, not a distributed middleware" -- roughly forty lines
behind an abstract interface, not a place to grow policy.

Transport is UDP/JSON per Table 4, because Figure 1 shows the bus crossing a
real network hop: Branch A and Branch B both publish from the Pi, and the
state machine that subscribes runs on the workstation, joined by Wi-Fi.

The sequence counter is per-`CommandBus` instance and shared across both
branches by construction -- `PipelineRuntime` (runtime/pipeline.py) holds one
`CommandBus` and calls `publish()` for both Branch A and Branch B traffic --
which is what makes the Sec. 4.3 ordering comparison meaningful: a Branch A
and a Branch B message drawn from the same counter can be compared directly.
"""

from __future__ import annotations

import itertools
import json
import socket
import threading
import time
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from schema.logger import get_structured_logger

__all__ = ["Branch", "BusMessage", "CommandBus", "DEFAULT_PORT"]

logger = get_structured_logger("runtime.bus")

Branch = Literal["A", "B"]

#: Arbitrary, unregistered port. Real deployment moves this to a config value;
#: nothing in this module hard-codes a network beyond the loopback tests.
DEFAULT_PORT = 8765

#: Generous against the roughly 18-40 byte wire form the schema produces
#: (Sec. 5); one JSON envelope per datagram, no fragmentation to reassemble.
MAX_DATAGRAM_BYTES = 4096


@dataclass(frozen=True)
class BusMessage:
    """One bus envelope: a sequence number, a branch tag, and a command.

    `command` is a plain dict (the command's wire fields, e.g.
    `{"intent": "hover"}`) rather than a schema model, so this module has no
    dependency on `schema.schema` beyond what `CommandBus.publish` accepts --
    the bus carries JSON, it does not interpret it.
    """

    seq: int
    branch: Branch
    command: dict
    t_publish: float

    def to_json(self) -> str:
        return json.dumps(
            {"seq": self.seq, "branch": self.branch, "command": self.command, "t_publish": self.t_publish}
        )

    @classmethod
    def from_json(cls, raw: str) -> "BusMessage":
        data = json.loads(raw)
        branch = data["branch"]
        if branch not in ("A", "B"):
            raise ValueError(f"bus message carries an unknown branch tag: {branch!r}")
        return cls(
            seq=int(data["seq"]),
            branch=branch,
            command=dict(data["command"]),
            t_publish=float(data["t_publish"]),
        )


class CommandBus:
    """UDP/JSON publish-subscribe with one monotonic sequence counter.

    A bus that only ever publishes needs no bound socket; `bind=True` opens
    the receiving side used by `Dispatcher.drain` (runtime/pipeline.py) and by
    the state machine across the Wi-Fi hop in the real deployment.
    """

    def __init__(self, *, host: str = "127.0.0.1", port: int = DEFAULT_PORT, bind: bool = False) -> None:
        self.host = host
        self.port = port
        self._seq_lock = threading.Lock()
        self._counter = itertools.count(0)
        self._send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._recv_sock: socket.socket | None = None
        if bind:
            self._recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._recv_sock.bind((host, port))

    def next_seq(self) -> int:
        """Reserve the next sequence number without publishing.

        Branch B (`runtime/pipeline.py`) reserves one when it *starts*
        processing an utterance, not when it eventually publishes. Sec. 4.3's
        ordering rule depends on that: a decode already in flight when Branch
        A triggers must still carry the number it was reserved *before* the
        trigger, all the way through to publish -- otherwise a slow message
        that finishes after a later Branch A trigger would be assigned a
        higher sequence number simply for finishing later, and the "discard
        anything lower than the highest Branch A seq already applied" rule
        would never catch it. Branch A has no such gap (detect, build, publish
        are one synchronous call), so it lets `publish()` reserve for it.
        """
        with self._seq_lock:
            return next(self._counter)

    def publish(self, branch: Branch, command: BaseModel | dict, *, seq: int | None = None) -> BusMessage:
        """Tag the branch and send, assigning a sequence number if one was
        not already reserved with `next_seq()`.

        Accepts either a schema model (Formation, Hover, ...) or a plain dict
        so Branch A -- which builds a Hover/Abort model directly, per Table 5
        -- and Branch B -- which publishes whatever `schema.validate.validate`
        returned -- share one call.
        """
        if branch not in ("A", "B"):
            raise ValueError(f"branch must be 'A' or 'B', got {branch!r}")
        if seq is None:
            seq = self.next_seq()
        payload = command.model_dump(exclude_none=True) if isinstance(command, BaseModel) else dict(command)
        msg = BusMessage(seq=seq, branch=branch, command=payload, t_publish=time.monotonic())
        data = msg.to_json().encode("utf-8")
        if len(data) > MAX_DATAGRAM_BYTES:
            raise ValueError(f"bus message of {len(data)} bytes exceeds {MAX_DATAGRAM_BYTES}")
        self._send_sock.sendto(data, (self.host, self.port))
        logger.info(
            "bus publish seq=%d branch=%s intent=%s",
            msg.seq,
            branch,
            payload.get("intent"),
            extra={"event": "bus_publish", "seq": msg.seq, "branch": branch, "intent": payload.get("intent")},
        )
        return msg

    def recv(self, timeout: float | None = None) -> BusMessage | None:
        """Receive one message, or `None` on timeout. Requires `bind=True`."""
        if self._recv_sock is None:
            raise RuntimeError("CommandBus was constructed with bind=False; cannot recv")
        self._recv_sock.settimeout(timeout)
        try:
            data, _addr = self._recv_sock.recvfrom(MAX_DATAGRAM_BYTES)
        except (socket.timeout, BlockingIOError):
            # `timeout=0.0` puts the socket in non-blocking mode, where a
            # datagram already sent but not yet delivered into the kernel's
            # receive queue raises `BlockingIOError` rather than timing out
            # (Errno 11, "resource temporarily unavailable"). Both cases mean
            # the same thing to a caller: nothing to read right now.
            return None
        return BusMessage.from_json(data.decode("utf-8"))

    def close(self) -> None:
        self._send_sock.close()
        if self._recv_sock is not None:
            self._recv_sock.close()

    def __enter__(self) -> "CommandBus":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
