"""The workstation side of the demonstration: bus consumer, state machine, link, simulation, display.

Figure 1 places the consumer of the bus, the flight state machine, the swarm controller and the
simulation on the workstation, joined to the Raspberry Pi by the wireless link. This process is
that side. Each message received goes through the ordering rule (`runtime.pipeline.Dispatcher`,
unchanged), the state machine it wraps, and the link (`swarm/link.py`) onto the controller; each
tick of the backend is reported back to the state machine by the link. `--backend numpy` is
Part A of Chapter 6's protocol (kinematic backend, separation clamp on, the run of record);
`--backend pyflyt` is Part B (rigid-body backend, no clamp, no criterion).

    python demo/workstation.py                          # Part A, listening on every interface
    python demo/workstation.py --backend pyflyt         # Part B
    python demo/workstation.py --headless --seconds 90  # no display, e.g. under a rehearsal

Keys in the display: [r] the reset out of ABORTED (step 8), [s] a screenshot, [f] full screen,
[q] quit. Everything the state machine and the link log -- every rejection with the intent
rejected and the state it arrived in -- goes, as structured JSON, to `<out>/workstation.jsonl`;
the trajectory goes to `<out>/trajectory.npz`; `<out>` is a fresh folder under `demo_runs/`.

**Pacing.** The backend is stepped against the wall clock: one step per `tick_seconds(env)`, 20 ms
on the kinematic backend and 41.67 ms on PyFlyt (Chapter 6: PyFlyt runs at 24 Hz effective). The
controller still integrates with its 20 ms `dt` on both, which is Chapter 6's limitation, kept
rather than corrected. The clock on the display orders events; it does not time them.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import logging
import signal
import queue
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):  # `python demo/workstation.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from runtime.bus import BusMessage, CommandBus
from runtime.pipeline import Dispatcher
from schema.logger import StructuredJsonFormatter, get_structured_logger
from swarm.control import CLAMP_DISTANCE, COLLISION_DISTANCE
from swarm.fsm import FlightState, FlightStateMachine
from swarm.link import GroundNumpyEnv, GroundPyFlytEnv, Link, tick_seconds

__all__ = ["Event", "Station", "build"]

REPO_ROOT = Path(__file__).resolve().parent.parent
BUS_PORT = 8766
logger = get_structured_logger("demo.station")

_PATH = {"A": "reflex", "B": "parse"}
_STATE_COLOUR = {
    FlightState.LANDED: "#7f7f7f", FlightState.TAKING_OFF: "#1f77b4", FlightState.FLYING: "#2ca02c",
    FlightState.LANDING: "#ff7f0e", FlightState.ABORTED: "#d62728",
}


def summarise(command: dict) -> str:
    rest = ", ".join(f"{k} {v}" for k, v in command.items() if k != "intent")
    return command.get("intent", "?") + (f" ({rest})" if rest else "")


@dataclass(frozen=True)
class Event:
    wall: _dt.datetime
    seq: int | None
    path: str | None
    received: str
    outcome: str
    state: FlightState

    def line(self) -> str:
        head = f"{self.wall:%H:%M:%S.%f}"[:-5]
        who = f"#{self.seq} {self.path}" if self.seq is not None else self.path
        return f"{head}  {who:<11} {self.received}  ->  {self.outcome}  [{self.state.value}]"


class Station:
    """The consumer: bus in, ordering rule, state machine, link. Drive it with `pump()` and `tick()`."""

    def __init__(self, bus: CommandBus, link: Link, *, echo: bool = True) -> None:
        self.bus = bus
        self.link = link
        self.dispatcher = Dispatcher(link.fsm)
        self.highest_reflex = -1
        self.events: deque[Event] = deque(maxlen=500)
        self.received = 0
        self._echo = echo
        self._inbox: queue.Queue[BusMessage] = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._receive, name="bus-receiver", daemon=True)
        self._thread.start()

    def _receive(self) -> None:
        while not self._stop.is_set():
            try:
                msg = self.bus.recv(timeout=0.2)
            except (ValueError, KeyError) as exc:          # malformed datagram or unknown path tag
                logger.warning("bus message refused: %s", exc, extra={"event": "bus_message_refused"})
                continue
            if msg is not None:
                self._inbox.put(msg)

    def pump(self) -> int:
        """Apply every message received so far, in arrival order."""
        n = 0
        while True:
            try:
                msg = self._inbox.get_nowait()
            except queue.Empty:
                return n
            self.handle(msg)
            n += 1

    def handle(self, msg: BusMessage) -> Event:
        self.received += 1
        stale = msg.branch == "B" and msg.seq < self.highest_reflex
        if msg.branch == "A":
            self.highest_reflex = max(self.highest_reflex, msg.seq)
        before = self.link.fsm.state
        cmd = self.dispatcher.apply(msg)
        asked = msg.command.get("intent")
        if stale:
            outcome = f"discarded: older than reflex #{self.highest_reflex}"
        elif cmd is None:
            outcome = ("logged, never dispatched" if asked == "unknown"
                       else f"logged no-op: abort in {before.value}" if asked == "abort"
                       else f"not dispatched: illegal in {before.value}, and so is a hold")
        else:
            action = self.link.dispatch(cmd, before)
            rejected = cmd.intent == "hover" and asked != "hover"
            outcome = (f"rejected in {before.value} -> {action}" if rejected else action)
        return self._record(msg.seq, _PATH[msg.branch], summarise(msg.command), outcome)

    def tick(self) -> None:
        """One backend step through the link, recording what the vehicles reported back."""
        before, motors = self.link.fsm.state, self.link.motors_on
        self.link.tick()
        after = self.link.fsm.state
        if after != before:
            what = {FlightState.FLYING: "take-off height reached",
                    FlightState.LANDED: "ground contact"}.get(after, "state changed")
            self._record(None, "vehicles", what, f"{before.value} -> {after.value}")
        elif motors and not self.link.motors_on:
            self._record(None, "vehicles", "ground contact", "motors off")

    def reset(self) -> bool:
        ok = self.link.reset()
        state = self.link.fsm.state
        if ok:
            outcome = "reset accepted"
        elif state != FlightState.ABORTED:
            outcome = "reset refused: not ABORTED"
        else:
            outcome = "reset refused: not every vehicle on the ground and at rest"
        self._record(None, "operator", "reset", outcome)
        return ok

    def _record(self, seq, path, received, outcome) -> Event:
        event = Event(_dt.datetime.now(), seq, path, received, outcome, self.link.fsm.state)
        self.events.append(event)
        logger.info("station: %s", event.line(),
                    extra={"event": "station", "seq": seq, "path": path, "received": received,
                           "outcome": outcome, "state": event.state.value})
        if self._echo:
            print(event.line(), flush=True)
        return event

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)


def build(backend: str, *, render: bool = False):
    env = GroundNumpyEnv() if backend == "numpy" else GroundPyFlytEnv(render=render)
    env.reset(0)
    return Link(env, FlightStateMachine(), clamp=backend == "numpy")


# ---------------------------------------------------------------------- display


class Display:
    """A 3D view and a top-down view of the backend's state, drawn at the positions it computed."""

    XLIM, YLIM, ZLIM = (-10.0, 10.0), (-8.0, 20.0), (0.0, 8.0)

    def __init__(self, station: Station, title: str, out: Path) -> None:
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec

        for key, drop in (("keymap.save", "s"), ("keymap.home", "r"), ("keymap.quit", "q")):
            plt.rcParams[key] = [k for k in plt.rcParams[key] if k != drop]
        self.plt = plt
        self.station, self.link, self.out, self.title = station, station.link, out, title
        self.closed = False

        fig = plt.figure(figsize=(16, 9))
        fig.canvas.manager.set_window_title("Swarm demonstration -- workstation")
        grid = GridSpec(3, 2, width_ratios=[1.35, 1], height_ratios=[1, 0.9, 0.55], figure=fig,
                        left=0.02, right=0.98, top=0.96, bottom=0.02, wspace=0.08, hspace=0.15)
        ax3 = fig.add_subplot(grid[0:2, 0], projection="3d")
        top = fig.add_subplot(grid[0, 1])
        text = fig.add_subplot(grid[1, 1])
        strip = fig.add_subplot(grid[2, :])
        text.axis("off")
        strip.axis("off")

        ax3.set_xlim(*self.XLIM), ax3.set_ylim(*self.YLIM), ax3.set_zlim(*self.ZLIM)
        ax3.set_box_aspect((np.ptp(self.XLIM), np.ptp(self.YLIM), np.ptp(self.ZLIM) * 1.5))
        ax3.set_xlabel("east (m)"), ax3.set_ylabel("north (m)"), ax3.set_zlabel("up (m)")
        ax3.view_init(elev=24, azim=-60)
        top.set_xlim(*self.XLIM), top.set_ylim(*self.YLIM), top.set_aspect("equal")
        top.set_xlabel("east (m)"), top.set_ylabel("north (m)"), top.grid(alpha=0.3)
        top.set_title("top view  (x: targets)", fontsize=10)

        p = self.link.env.positions
        self.drones3 = ax3.scatter(p[:, 0], p[:, 1], p[:, 2], s=70, c="#1f77b4", depthshade=False)
        self.targets3 = ax3.scatter(p[:, 0], p[:, 1], p[:, 2], s=40, marker="x", c="#999999")
        self.stems = [ax3.plot([x, x], [y, y], [0, z], c="#1f77b4", lw=0.8, alpha=0.5)[0] for x, y, z in p]
        self.drones2 = top.scatter(p[:, 0], p[:, 1], s=60, c="#1f77b4", zorder=3)
        self.targets2 = top.scatter(p[:, 0], p[:, 1], s=40, marker="x", c="#999999", zorder=2)
        self.labels = [top.text(x, y, f" {i}", fontsize=8) for i, (x, y, _) in enumerate(p)]

        self.clock = text.text(0.0, 0.98, "", fontsize=30, family="monospace", va="top",
                               transform=text.transAxes)
        text.text(0.0, 0.70, title, fontsize=11, va="top", transform=text.transAxes)
        self.state = text.text(0.0, 0.58, "", fontsize=22, family="monospace", weight="bold", va="top",
                               transform=text.transAxes)
        self.stats = text.text(0.0, 0.38, "", fontsize=9.5, family="monospace", va="top",
                               transform=text.transAxes)
        self.log = strip.text(0.0, 1.0, "", fontsize=9, family="monospace", va="top",
                              transform=strip.transAxes)
        strip.text(1.0, 1.0, "[r] reset out of ABORTED   [s] screenshot   [f] full screen   [q] quit",
                   fontsize=9, color="#555555", ha="right", va="top", transform=strip.transAxes)

        fig.canvas.mpl_connect("key_press_event", self._key)
        fig.canvas.mpl_connect("close_event", lambda _e: setattr(self, "closed", True))
        self.fig = fig
        plt.show(block=False)

    def _key(self, event) -> None:
        if event.key == "r":
            self.station.reset()
        elif event.key == "s":
            path = self.out / f"screenshot-{_dt.datetime.now():%H%M%S}.png"
            self.fig.savefig(path, dpi=110)
            print(f"screenshot: {path}", flush=True)
        elif event.key == "q":
            self.plt.close(self.fig)

    def update(self) -> None:
        link = self.link
        p, t = link.env.positions, link.controller.targets
        state = link.fsm.state
        colour = _STATE_COLOUR[state]
        self.drones3._offsets3d = (p[:, 0], p[:, 1], p[:, 2])
        self.drones3.set_color(colour)
        self.drones2.set_offsets(p[:, :2])
        self.drones2.set_color(colour)
        if link.controller.assigned:
            self.targets3._offsets3d = (t[:, 0], t[:, 1], t[:, 2])
            self.targets2.set_offsets(t[:, :2])
        for stem, (x, y, z) in zip(self.stems, p):
            stem.set_data_3d([x, x], [y, y], [0, z])
            stem.set_color(colour)
        for label, (x, y, _) in zip(self.labels, p):
            label.set_position((x, y))

        self.clock.set_text(f"{_dt.datetime.now():%H:%M:%S.%f}"[:-5])
        self.state.set_text(state.value)
        self.state.set_color(colour)
        d = np.linalg.norm(p[:, None] - p[None], axis=2)
        np.fill_diagonal(d, np.inf)
        clamp = (f"clamp activations {link.clamp_activations}  (acts below {CLAMP_DISTANCE} m)"
                 if link.clamp else "no separation clamp on this backend")
        self.stats.set_text(
            f"motors {'on ' if link.motors_on else 'off'}   sim time {link.ticks * tick_seconds(link.env):7.1f} s   "
            f"messages {self.station.received}   highest reflex #{self.station.highest_reflex}\n"
            f"closest pair {d.min():5.2f} m   minimum so far {link.min_pair_distance:5.2f} m\n"
            f"{clamp}\n"
            f"ticks under {COLLISION_DISTANCE} m: {link.collisions}")
        self.log.set_text("\n".join(e.line() for e in list(self.station.events)[-8:]))
        self.fig.canvas.draw_idle()

    def pause(self) -> None:
        self.plt.pause(0.001)


# ---------------------------------------------------------------------- main


def _route_logs(path: Path) -> None:
    """Structured JSON to `path`; the terminal keeps only errors and the station's own lines."""
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(StructuredJsonFormatter())
    for root in ("demo", "runtime", "schema", "swarm"):
        get_structured_logger(root)
        log = logging.getLogger(root)
        log.setLevel(logging.INFO)
        for existing in log.handlers:
            existing.setLevel(logging.ERROR)
        log.addHandler(handler)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=("numpy", "pyflyt"), default="numpy")
    ap.add_argument("--bind", default="0.0.0.0", help="address to listen on (default: every interface)")
    ap.add_argument("--port", type=int, default=BUS_PORT)
    ap.add_argument("--headless", action="store_true", help="no display")
    ap.add_argument("--pybullet-gui", action="store_true", help="Part B: also open PyBullet's own 3D window")
    ap.add_argument("--seconds", type=float, default=None, help="stop after this long (default: until [q]/Ctrl-C)")
    ap.add_argument("--out", type=Path, default=None, help="run folder (default demo_runs/<time>-<backend>)")
    args = ap.parse_args(argv)

    out = args.out or REPO_ROOT / "demo_runs" / f"{_dt.datetime.now():%Y%m%d-%H%M%S}-{args.backend}"
    out.mkdir(parents=True, exist_ok=True)
    _route_logs(out / "workstation.jsonl")

    part = ("Part A -- kinematic backend, separation clamp on" if args.backend == "numpy"
            else "Part B -- PyFlyt rigid-body backend, no separation clamp")
    link = build(args.backend, render=args.pybullet_gui)
    bus = CommandBus(host=args.bind, port=args.port, bind=True)
    station = Station(bus, link)
    display = None if args.headless else Display(station, part, out)
    period = tick_seconds(link.env)
    print(f"{part}\nlistening on {args.bind}:{args.port}; tick {period * 1000:.2f} ms; run folder {out}",
          flush=True)

    record_every = max(1, int(round(0.1 / period)))          # trajectory at 10 Hz
    trajectory: dict[str, list] = {"t": [], "wall": [], "state": [], "positions": [], "targets": []}
    states = list(FlightState)
    t0, n = time.monotonic(), 0
    # Ctrl-C only sets a flag: a KeyboardInterrupt raised while Tk is redrawing
    # is caught and printed by Tk's own callback handler and never reaches this loop.
    stop: list[int] = []
    previous = signal.signal(signal.SIGINT, lambda signum, _frame: stop.append(signum))
    try:
        while not stop and not (display and display.closed):
            elapsed = time.monotonic() - t0
            if args.seconds is not None and elapsed >= args.seconds:
                break
            station.pump()
            due = int(elapsed / period)
            if due - n > int(1.0 / period):                  # a second behind: re-anchor, never fast-forward
                logger.warning("simulation fell %d ticks behind the wall clock; re-anchored", due - n,
                               extra={"event": "pacing_reanchored", "behind_ticks": due - n})
                t0, due = time.monotonic() - n * period, n + 1
            while n < due:
                station.tick()
                n += 1
                station.pump()
                if n % record_every == 0:
                    trajectory["t"].append(n * period)
                    trajectory["wall"].append(time.time())
                    trajectory["state"].append(states.index(link.fsm.state))
                    trajectory["positions"].append(link.env.positions)
                    trajectory["targets"].append(link.controller.targets)
            if display:
                display.update()
                display.pause()
            else:
                time.sleep(min(period, 0.01))
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, previous)
        station.close()
        bus.close()
        if hasattr(link.env, "close"):
            link.env.close()
        np.savez_compressed(out / "trajectory.npz", states=np.array([s.value for s in states]),
                            **{k: np.asarray(v) for k, v in trajectory.items()})
        print(f"final state {link.fsm.state.value}; closest approach {link.min_pair_distance:.2f} m; "
              f"clamp activations {link.clamp_activations}; saved {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
