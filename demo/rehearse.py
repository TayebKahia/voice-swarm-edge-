"""Publish the demonstration script onto the bus, standing in for the Raspberry Pi.

Every command the device would publish for each utterance of tab:demo-script (Chapter 6), sent
over the real bus with the real sequence rule, so the workstation side -- consumer, state machine,
link, simulation, display -- can be rehearsed without the device, the microphone or the link.
Step 4 is sent the way the ordering rule meets it at its worst: the line's sequence number is
reserved first, the reflex hold is published, and the line is published afterwards with its older
number, as a decode the hold did not stop would be. The workstation must discard it.

    python demo/rehearse.py                       # to a workstation on this machine
    python demo/rehearse.py --host 10.42.0.1      # across the link, from the Pi
    python demo/rehearse.py --rejections          # also send commands that must produce no motion
    python demo/rehearse.py --step                # wait for Enter before each step
    python demo/rehearse.py --part b              # Part B: steps 1, 2, 5 and 6 only

Restart the workstation before each rehearsal: a new bus starts its sequence numbers at 0, and a
consumer that has already applied a higher reflex number discards everything older, by design.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):  # `python demo/rehearse.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runtime.bus import CommandBus

__all__ = ["Step", "SCRIPT", "PART_B", "REJECTIONS", "publish_step"]

#: Each action is (path, command). Path "B" is the parse path, "A" the reflex path, and "B-stale"
#: a parse-path command published with a number reserved before the step's reflex command.


@dataclass(frozen=True)
class Step:
    number: str
    utterance: str
    actions: tuple[tuple[str, dict], ...]
    state_after: str
    seconds: float      # simulated time to let the step play out before the next


SCRIPT: tuple[Step, ...] = (
    Step("1", "take off to five metres", (("B", {"intent": "takeoff", "z": 5.0}),), "FLYING", 10),
    Step("2", "form a circle with radius five metres",
         (("B", {"intent": "formation", "shape": "circle", "radius": 5.0}),), "FLYING", 12),
    Step("3", "move north ten metres",
         (("B", {"intent": "move", "dir": "north", "dist": 10.0}),), "FLYING", 12),
    Step("4", "form a line with spacing three metres / swarm hold",
         (("B-stale", {"intent": "formation", "shape": "line", "spacing": 3.0}),
          ("A", {"intent": "hover"})), "FLYING", 5),
    Step("5", "form a line with spacing three metres",
         (("B", {"intent": "formation", "shape": "line", "spacing": 3.0}),), "FLYING", 12),
    Step("6", "land", (("B", {"intent": "land"}),), "LANDED", 12),
    Step("7a", "take off to five metres", (("B", {"intent": "takeoff", "z": 5.0}),), "FLYING", 10),
    Step("7b", "swarm abort", (("A", {"intent": "abort"}),), "ABORTED", 12),
)

#: Chapter 6: Part B repeats the take-off, the circle, the line and the landing.
PART_B = tuple(step for step in SCRIPT if step.number in ("1", "2", "5", "6"))

#: Commands the third success criterion says must produce no motion, sent while LANDED at the
#: start: illegal there, and hover is illegal there too, so each is a logged no-op.
REJECTIONS: tuple[Step, ...] = (
    Step("R1", "form a circle (while landed)",
         (("B", {"intent": "formation", "shape": "circle", "radius": 5.0}),), "LANDED", 2),
    Step("R2", "move north (while landed)",
         (("B", {"intent": "move", "dir": "north", "dist": 10.0}),), "LANDED", 2),
    Step("R3", "an utterance the parser resolves to unknown", (("B", {"intent": "unknown"}),), "LANDED", 2),
)


def publish_step(bus: CommandBus, step: Step) -> int:
    """Publish one step's actions in order. Returns the number of messages sent."""
    reserved = [bus.next_seq() for path, _ in step.actions if path == "B-stale"]
    sent = 0
    for path, command in step.actions:
        if path == "B-stale":
            continue
        bus.publish(path, command)
        sent += 1
    for seq, (_, command) in zip(reserved, [a for a in step.actions if a[0] == "B-stale"]):
        bus.publish("B", command, seq=seq)
        sent += 1
    return sent


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--part", choices=("a", "b"), default="a")
    ap.add_argument("--rejections", action="store_true")
    ap.add_argument("--step", action="store_true", help="wait for Enter before each step")
    ap.add_argument("--speed", type=float, default=1.0, help=">1 shortens the waits between steps")
    args = ap.parse_args(argv)

    steps = (REJECTIONS if args.rejections else ()) + (SCRIPT if args.part == "a" else PART_B)
    for handler in logging.getLogger("runtime").handlers:   # the bus's JSON; this prints its own lines
        handler.setLevel(logging.ERROR)
    with CommandBus(host=args.host, port=args.port) as bus:
        for step in steps:
            if args.step:
                input(f"[Enter] step {step.number}: \"{step.utterance}\" ")
            publish_step(bus, step)
            print(f"{time.strftime('%H:%M:%S')}  step {step.number:>3}  \"{step.utterance}\"  "
                  f"-> expect {step.state_after}", flush=True)
            if not args.step:
                time.sleep(step.seconds / args.speed)
    if args.part == "a":
        print("script sent. Step 8: press [r] on the workstation once every vehicle is on the ground.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
