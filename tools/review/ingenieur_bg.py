#!/usr/bin/env python3
"""Pre-review checks for Ingénieur Ch2 (Background). See tools/review/lib.py.

The Background chapter (added 26 Sep, prd.md §3.1 item 2) states the foundations of the engineering
document only: speech pipelines, multirotor vehicles and their control, swarm control, real-time
systems and latency budgets, the single-board computer as a shared host, state machines and command
buses. It reports no result, makes no design decision and takes no position on the literature. The
foundations the Mémoire de Master defines get one sentence each (Table 3, write-once). So, beyond the
common checks, the script tests: the chapter's shape against prd.md §3.1; that nothing in it is a
result or a decision; that the Master's foundations are named, not re-explained; that the passages
moved here from the old state-of-the-art chapter are stated once; and the arithmetic behind three
textbook statements. Whether each definition is right is the agents' job; the MANUAL sheets are their
worklists.
"""

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import INGENIEUR, Chapter, Review, outline_check  # noqa: E402

r = Review("ingenieur_bg", "ingenieur", INGENIEUR[1], [INGENIEUR[0], *INGENIEUR[2:]])  # Background, Chapter 2 since 26 Sep
r.common()
text = r.ch.text
prose = r.ch.prose()

# -- Shape: prd.md §3.1 item 2, six foundation sections, the Master's named, a Conclusion --------
outline_check(r, 1, {"speech pipelines": r"speech pipelines",
                     "multirotor UAVs and the flight controller": r"multirotor",
                     "swarm control": r"^swarm control$",
                     "real-time systems and latency budgets": r"real-time",
                     "the single-board computer": r"single-board",
                     "state machines and command buses": r"state machines"})
titles = [t for lvl, t, _ in r.ch.sections() if lvl == "section"]
r.expect("outline", titles[-1:] == ["Conclusion"], f"closes with a Conclusion section (last section: {titles[-1:]})")
labels = re.findall(r"\\label\{(sec:bg-[^}]*)\}", text)
want = ["sec:bg-speech", "sec:bg-uav", "sec:bg-swarm", "sec:bg-realtime", "sec:bg-sbc", "sec:bg-fsm",
        "sec:bg-master", "sec:bg-conclusion"]
r.expect("outline", labels == want, f"section labels in outline order: {labels}")
r.expect("label", "\\label{chap:background}" in text, "carries \\label{chap:background}")
intro = text[: text.find("\\section{")]
for chap in ("chap:state-of-the-art", "chap:architecture"):
    r.expect("outline", f"\\ref{{{chap}}}" in intro, f"the opening hands the literature/decisions to \\ref{{{chap}}}")

# -- Foundations only: no result, no decision, no position (prd.md §3.1 item 2) -----------------
for pat, what in ((r"\\ref\{chap:(validation|demonstration|implementation)\}", "a reference to a results or build chapter"),
                  (r"\\ref\{(tab|fig):", "a table or figure of another chapter"),
                  (r"\b\d[\d{},]*~ms\b", "a latency figure (budgets and measurements belong to Chapters 4 and 6)"),
                  (r"\b0\.\d{2,}\b", "a measured or target value (0.xx)"),
                  (r"\b(Qwen|openWakeWord|Silero|whisper\.cpp|tiny\.en|Piper|Cortex|8~GB|core~0|cores~1)", "a component or setting this work chose"),
                  (r"\b(this (?:system|work|design) (?:uses|chose|deploys|runs)|is deployed|was selected|the reflex path|the parse path)\b",
                   "a design decision"),
                  (r"\b(Exp-\d|RQ\d|NFR-\d+|FR-\d+|Branch [AB]|C4)\b", "a project code")):
    hits = [(m.group(), r.ch.line_of(m.start())) for m in re.finditer(pat, prose)]
    r.expect("foundations", not hits, f"no {what} in the Background"
             if not hits else f"{what} in the Background: {hits[:3]} -- results and decisions belong to Chapters 3-6",
             hits[0][1] if hits else None)

# -- Write-once with the Master: its foundations are named in sec:bg-master and nowhere else here --
master_sec = text[text.find("\\label{sec:bg-master}"): text.find("\\section{Conclusion}")]
rest = text.replace(master_sec, "")
for pat, what in ((r"low-rank|\\gls\{lora\}", "LoRA"), (r"quantis", "quantisation"), (r"\\gls\{gbnf\}|token mask", "GBNF masking"),
                  (r"McNemar", "McNemar's test"), (r"memory-bound|memory bandwidth\b.*decod", "memory-bound decoding"),
                  (r"\\gls\{em\}|exact match", "exact match"), (r"throttl", "thermal throttling")):
    here = re.search(pat, master_sec, flags=re.I)
    there = [r.ch.line_of(m.start()) for m in re.finditer(pat, rest, flags=re.I)]
    r.expect("write-once", not there, f"{what}: named only in sec:bg-master" if not there
             else f"{what} also explained outside sec:bg-master (l.{there[:3]}) -- the Master owns it; one sentence "
             "and a cross-reference")
    if what not in ("memory-bound decoding", "thermal throttling"):
        r.expect("write-once", bool(here), f"{what}: named in sec:bg-master")
sentences = [s for s in re.split(r"(?<=[.])\s+(?=[A-Z\\])", re.sub(r"\\(section|label)\{[^}]*\}", "", master_sec)) if s.strip()]
r.expect("write-once", len(sentences) <= 10, f"sec:bg-master is {len(sentences)} sentences -- one per foundation, "
         "no re-explanation" if len(sentences) <= 10 else f"sec:bg-master runs to {len(sentences)} sentences -- "
         "it names the Master's foundations, it does not teach them", warn=True)
r.expect("write-once", "M\\'emoire de Master" in text or "M\\'emoire\nde Master" in text, "the Master is named as the owner")

# -- Moved passages: stated here once, and no longer in the state of the art or Architecture ------
others = {rel: Chapter.load("ingenieur", rel) for rel in (INGENIEUR[2], INGENIEUR[3])}
moved = [("avoid collisions with them, match their\nvelocity, and stay close to them", "Reynolds' three rules (from the old Ch2 swarm section)"),
         ("It is a task distinct from full speech recognition", "keyword spotting as a distinct task (from the old Ch2 speech section)")]
for needle, what in moved:
    here = r.ch.find(needle)
    r.expect("write-once", bool(here), f"{what}: stated in the Background", here[0] if here else None)
    flat = re.sub(r"\s+", " ", needle)
    for rel, ch in others.items():
        dup = flat in re.sub(r"\s+", " ", ch.text)
        r.expect("write-once", not dup, f"{what}: not repeated in {rel}" if not dup
                 else f"{what}: also in {rel} -- state once, cross-reference")

# -- Arithmetic behind three textbook statements -------------------------------------------------
r.text_claim("claim", "every\n10~dB fall multiplies the relative power of the noise by ten", 10 ** (10 / 10) == 10,
             "10 dB = a power ratio of 10^(10/10) = 10")
eta, d0, d, h = 6.0, 1.5, 0.9, 1e-6
U = lambda x: 0.5 * eta * (1 / x - 1 / d0) ** 2  # noqa: E731
grad = -(U(d + h) - U(d - h)) / (2 * h)
r.text_claim("claim", "The magnitude\nof the resulting force is $\\eta\\,(1/d - 1/d_0)/d^2$",
             math.isclose(grad, eta * (1 / d - 1 / d0) / d ** 2, rel_tol=1e-6),
             "-dU/dd of eq:apf equals eta (1/d - 1/d0)/d^2 (numerical derivative at d = 0.9, d0 = 1.5)")
kp = 2.0  # x'' = -kp x - kd x': characteristic s^2 + kd s + kp, critically damped at kd^2 = 4 kp
r.text_claim("claim", "\\emph{critically damped} when $k_d = 2\\sqrt{k_p}$", math.isclose((2 * math.sqrt(kp)) ** 2, 4 * kp),
             "discriminant kd^2 - 4 kp = 0 at kd = 2 sqrt(kp) for a unit mass")

# -- Numbers that belong to a cited paper: the citation agent's worklist --------------------------
rows = ["| line | claim | must be found in |", "|---|---|---|"]
for anchor, key in (("680{,}000 hours", "whisper"), ("39~million parameters upwards", "whisper")):
    where = r.ch.find(anchor)
    r.expect("paper-number", bool(where), f"anchor `{anchor}` present", where[0] if where else None)
    if where:
        rows.append(f"| {where[0]} | {anchor} | {key} |")
r.manual.append("### Numbers quoted from sources (citation agent: find each)\n\n" + "\n".join(rows))

todos = [(m.group(1)[:70], r.ch.line_of(m.start())) for m in re.finditer(r"\\TODO\{([^}]*)", text)]
r.manual.append("### Known markers (do not re-report; check the claim each sits on)\n\n"
                + "\n".join(f"- l.{ln}: {t}..." for t, ln in todos))
defs = [("sec:bg-speech", "frames; keyword spotting (speechcmd); false accepts per hour, false rejects per spoken "
                          "phrase; refractory interval; ROC and operating point; threshold chosen on held-apart data; "
                          "VAD; endpointing silence rule and its trade-off; seq2seq recognisers; Whisper facts; WER "
                          "definition and that it can exceed one; SNR in dB, eq:snr; cascade vs direct"),
        ("sec:bg-uav", "quadrotor lift and tilt; hover; kinetic/potential energy and harm; nested control loops and "
                       "setpoints; PID law eq:pid and each term's role; integral wind-up; double integrator, critical "
                       "damping kd = 2 sqrt(kp) at unit mass; semi-implicit Euler and its stability claim"),
        ("sec:bg-swarm", "Reynolds' three rules and 'no leader'; central-force form 'avoided' by Reynolds; slots; "
                         "greedy nearest-slot assignment can cross paths; total squared distance = linear assignment; "
                         "eq:apf and its gradient; Koren's three failure modes; soft vs hard; SIL; kinematic vs physics "
                         "simulators; PyFlyt (pyflyt); seeded trials repeatable"),
        ("sec:bg-realtime", "hard vs soft real-time; latency needs two named events; nearest-rank percentile "
                            "ceil(qn/100); percentiles do not add; budgets as ceilings; periodic task backlog; "
                            "preemption vs cooperative cancellation and its latency bound"),
        ("sec:bg-sbc", "Linux scheduler gives no timing guarantee; processor affinity; shared bandwidth, cache and "
                       "heat"),
        ("sec:bg-fsm", "FSM definition; legality table and exhaustive testing; state machine as a gate; "
                       "publish/subscribe decoupling; JSON; UDP connectionless, no retransmission, no delivery or "
                       "order guarantee; sequence numbers from a shared counter give one order"),
        ("sec:bg-master", "each one-sentence summary agrees with the Master's Background (thesis/master/ch2_background.tex)")]
r.manual.append("### Definitions to verify (argument agent: each must be textbook-correct)\n\n| section | claims |\n"
                "|---|---|\n" + "\n".join(f"| {s} | {c} |" for s, c in defs))
r.manual.append("### For the argument agent\n\n- prd.md §3.1 item 2: foundations only. Any sentence that states what "
                "*this system chose* belongs in Chapters 4-5; any sentence that states what *the literature has "
                "measured* belongs in Chapter 3. List each.\n- Level: a jury member outside the sub-field. List any "
                "definition that assumes what it should define, and any that is longer than the document needs.\n"
                "- Consistency with the later chapters: the vocabulary here (operating point, end of speech, "
                "refractory interval, setpoint, clamp as a hard mechanism, stage allowances as ceilings, affinity, "
                "sequence numbers) must mean what Chapters 4-6 use it to mean. A difference in meaning is a finding.\n"
                "- Write-once: sec:bg-master against the Master's Background; sec:bg-sbc must not re-explain the Pi's "
                "hardware, memory-bound decode or throttling.")
sys.exit(r.finish())
