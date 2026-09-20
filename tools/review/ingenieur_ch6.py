#!/usr/bin/env python3
"""Pre-review checks for Ingénieur Ch6 (Demonstration, limitations, and conclusion). See tools/review/lib.py.

Ch6 concludes the document: Section 6.1 fixes the demonstration protocol before the defence, Section 6.2
states the limitations, Section 6.3 details the future work, and Section 6.4 gives direct, unhedged answers
to RQ2 and RQ3.

All measured numbers are inherited from Chapter 5 (and its underlying results/ files). The script asserts
that:
  - Every figure in Ch6 is traced to results/ or earlier chapters; no new measurement is introduced.
  - Hedging words in Section 6.4 (Conclusion) FAIL.
  - Required outline topics exist.
  - Key claims and anchors across 6.1-6.4 match results/ exactly.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (  # noqa: E402
    INGENIEUR,
    RESULTS,
    THESIS,
    Chapter,
    Review,
    csv_rows,
    numbers,
    outline_check,
    significant,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from swarm.control import CLAMP_DISTANCE, COLLISION_DISTANCE  # noqa: E402

r = Review("ingenieur_ch6", "ingenieur", INGENIEUR[6], INGENIEUR[:6])  # closing chapter, Chapter 7 since 26 Sep
r.common()
text, prose = r.ch.text, r.ch.prose()

outline_check(r, 6, {
    "demonstration protocol": r"demonstration",
    "limitations": r"limitations",
    "future work": r"future work",
    "conclusion": r"conclusion",
})

# -- Data sources from results/ ----------------------------------------------------------------
E = {(x["measure"], x["condition"]): x for x in csv_rows(RESULTS / "exp2.csv")}


def g(measure: str, cond: str, col: str = "p95") -> float:
    return float(E[(measure, cond)][col])


e2e_p95 = g("e2e_t0", "branch_b")
e2e_ep_p95 = g("e2e_speech_end", "branch_b")
stt_p95 = g("stt", "branch_b")
prefill_p95 = g("prefill", "branch_b")
decode_p95 = g("decode", "branch_b")
vad_wait_p95 = g("vad_wait", "branch_b")
reflex_idle_p95 = g("a_offset", "idle")
reflex_loaded_p95 = g("a_offset", "loaded")
recovery_p95 = g("recovery", "loaded")

exp3_pi = {x["condition"]: x for x in csv_rows(RESULTS / "exp3_pi.csv")}
exp4 = csv_rows(RESULTS / "exp4.csv")
wake_real = {x["class"]: x for x in json.loads((RESULTS / "wake_real_voice.json").read_text(encoding="utf-8"))["rows"]}
wake_train = json.loads((RESULTS / "wake_training.json").read_text(encoding="utf-8"))

# -- 6.1 Demonstration Protocol ----------------------------------------------------------------
r.expect("protocol", r"Table~\ref{tab:demo-script}" in text, "Table tab:demo-script referenced")
r.expect("protocol", "Part~A" in text and "Part~B" in text, "Both Part A and Part B defined")
r.expect("protocol", "Four criteria are fixed for Part~A" in text, "Four success criteria stated")

# -- 6.2 Limitations ---------------------------------------------------------------------------
r.number("median 4.06~s for the circle", 4.06, "circle convergence median")
r.number("3.26~s for the line", 3.26, "line convergence median")
r.number("2.30~s for\nthe wedge", 2.30, "wedge convergence median")
r.number("stepping at 240~Hz", 240, "PyFlyt physics rate")
r.number("effective control rate of 24~Hz", 24, "PyFlyt effective control rate")
r.number("advances 10 physics steps", 10, "QuadX 10 physics steps per tick")
r.number("(41.67~ms)", 41.67, "QuadX tick duration ms", places=2)
r.number("evaluate 25~s", 25, "PyFlyt flight duration seconds")
r.number("12~s at the nominal 20~ms tick", 12, "PyFlyt test duration (nominal)")
r.number("600 ticks: 12~s", 600, "PyFlyt test ticks")
r.number("clamp intervened 432 times", sum(int(x["clamp_activations"]) for x in exp4), "total clamp interventions")
r.number("across 144 of the 150 trials", sum(1 for x in exp4 if int(x["clamp_activations"]) > 0), "trials needing clamp")
r.number("distance drops below 0.800~m", CLAMP_DISTANCE, "clamp distance (swarm/control.py)", places=3)
# Read from the code, not typed: a literal 0.50 here once let the prose's wrong 0.50 m pass review.
r.number("against a threshold of 0.35~m", COLLISION_DISTANCE, "collision threshold (swarm/control.py)", places=2)
r.number(r"2.0~m/s for \texttt{move}", 2.0, "commanded velocity ceiling", places=1)
r.number("hard ceiling of 3.0~m/s", 3.0, "backend speed ceiling", places=1)
r.number("safe-failure rate is 0.032", float(exp3_pi["clean"]["safe_failure_rate"]), "clean safe-failure rate", places=3)
r.number("remains between 0.014 and\n0.039", min(float(x["safe_failure_rate"]) for x in exp3_pi.values()), "min noise safe-failure rate", places=3)
r.number("remains between 0.014 and\n0.039", max(float(x["safe_failure_rate"]) for x in exp3_pi.values()), "max noise safe-failure rate", places=3, nth=1)
r.number("golden set yields 13\nfailures", 13, "reference text failures")
r.number("zero safe failures", 0, "reference text safe failures")
r.number("Seven criteria\nmet", 7, "met criteria count")
r.number("five missed", 5, "missed criteria count")
r.number("two not demonstrated", 2, "not demonstrated count")
r.number("two not yet run", 2, "not yet run count")
r.number("one planned for the defence", 1, "planned criteria count")
r.number("545~ms idle", reflex_idle_p95, "reflex idle p95", places=0)
r.number("547~ms loaded", reflex_loaded_p95, "reflex loaded p95", places=0)
r.number("at p95 against 150~ms", 150, "reflex budget p95")
r.number("missed in 540~ms that combine", 540, "spotter delay + quantisation + anchor error")
r.number("80~ms frame quantisation", 80, "spotter frame quantisation")
r.number("6~ms idle", g("a_system", "idle"), "idle board computation p95", places=0)
r.number("18~ms loaded", g("a_system", "loaded"), "loaded board computation p95", places=0)
r.number("End-to-end latency (3{,}122~ms", e2e_p95, "e2e p95", places=0, tol=0.5,
         note="x.5 in exp2.csv; the \\input table prints it half-to-even, and the prose follows the table")
r.number("against 2{,}500~ms", 2500, "e2e budget p95")
r.number("missed by 622~ms", e2e_p95 - 2500, "e2e shortfall ms", places=0, tol=0.5,
         note="x.5 in exp2.csv; the \\input table prints it half-to-even, and the prose follows the table")
r.number("or\n25\\%)", 100 * (e2e_p95 / 2500 - 1), "e2e shortfall pct", places=0)
r.number("recognition (1{,}449~ms", stt_p95, "stt p95", places=0)
r.number("against 1{,}200~ms allowance", 1200, "stt allowance")
r.number("prompt prefill\n(751~ms", prefill_p95, "prefill p95", places=0)
r.number("against 250~ms allowance", 250, "prefill allowance")
r.number("Preemption recovery\n(1{,}195~ms", recovery_p95, "recovery p95", places=0)
r.number("against 300~ms", 300, "recovery budget")
r.number(r"Clean-audio recognition (\gls{crr} 0.690", float(exp3_pi["clean"]["crr"]), "clean crr", places=3)
r.number("against 0.80", 0.80, "clean crr target", places=2)
r.number("22 failures from endpointer pauses", 22, "endpointer pause failures")
r.number(r"Recognition in noise (\gls{crr} 0.590", float(exp3_pi["10"]["crr"]), "10 dB crr", places=3)
r.number("against\n0.65", 0.65, "10 dB crr target", places=2)
r.number("false accepts (2.33/h", wake_train["test"]["ambient"]["per_hour"], "ambient fa per hour", places=2)
r.number(r"against $\leq 1$/h", 1, "ambient fa target")
r.number("hold 0.050", wake_real["swarm_hold"]["frr"], "author hold frr", places=3)
r.number("abort 0.000", wake_real["swarm_abort"]["frr"], "author abort frr", places=3)

# -- 6.3 Future Work ---------------------------------------------------------------------------
r.expect("future_work", r"\cite{koren1991}" in text, "Cites koren1991 for potential field collision avoidance")
r.number("from 751~ms towards its 250~ms allowance", prefill_p95, "prefill p95", places=0)
r.number("from 751~ms towards its 250~ms allowance", 250, "prefill allowance", nth=1)
r.expect("future_work", "is expected to shorten preemption recovery" in text,
         "polling fix stated as expected, not promised (Ch5: p95 and max exceed the 1 s period)")

# -- 6.4 Conclusion ----------------------------------------------------------------------------
r.expect("rq2", "Research Question~2 (RQ2)" in text, "RQ2 explicitly answered")
r.expect("rq3", "Research Question~3 (RQ3)" in text, "RQ3 explicitly answered")
r.expect("rq1", "Research Question~1 (RQ1)" in text and r"M\'emoire de Master" in text, "RQ1 cited in one sentence")
r.text_claim("claim", "zero collisions were observed, backed\nby a hard geometric separation clamp",
             sum(int(x["collisions"]) for x in exp4) == 0, "locked collision phrasing with zero collisions")
r.number("Formation accuracy reached 1.000", 1.000, "formation accuracy", places=3)
r.number(r"exceeding the $\geq 0.85$ requirement", 0.85, "formation accuracy requirement", places=2)
r.number("cancelled 78 of 78 in-progress", 78, "cancelled decodes count")
r.expect("claim", "never had to discard a late result" in text, "no late result discarded (Ch5 sec:latency-experiment)")
r.expect("claim", "neither class triggered on the other's" in text, "zero cross-triggers stated")

# -- Number inheritance: no new measurement introduced in Ch6 ---------------------------------
earlier = {round(n.value, n.places) for c in INGENIEUR[:6] for n in numbers(Chapter.load("ingenieur", c))}
for p in Path(THESIS / "generated").glob("*.tex"):
    raw = p.read_text(encoding="utf-8")
    c_dummy = Chapter("ingenieur", p, raw, raw.splitlines())
    for n in numbers(c_dummy):
        earlier.add(round(n.value, n.places))

for n in numbers(r.ch):
    if significant(n) and round(n.value, n.places) not in earlier:
        r.add("FAIL", "new-number", f"{n.text} appears in no earlier chapter -- Chapter 6 may not "
                                    "introduce a figure; report it in Ch5 first", n.line)

# -- Register: unhedged in Conclusion, no banned phrasing --------------------------------------
sec_conc_match = re.search(r"\\section\{Conclusion\}", text)
if sec_conc_match:
    sec_conc_prose = text[sec_conc_match.start():]
    for m in re.finditer(r"\b(?:may|might|could|perhaps|possibly|likely|suggests?|appears?|seems?)\b", sec_conc_prose, flags=re.I):
        r.add("FAIL", "register", f"hedge `{m.group()}` in Conclusion -- Section 6.4 concludes without hedging",
              r.ch.line_of(sec_conc_match.start() + m.start()))

for pat, why in ((r"budget (?:is|was) met|meets the 2\{,\}500|within the 2\{,\}500", "the 2,500 ms budget is missed, never met"),
                 (r"\bguarantee[sd]?\b", "no unearned absolutes")):
    hits = re.findall(pat, prose)
    r.expect("register", not hits, f"`{pat}` absent -- {why}" if not hits else f"`{pat}` found -- {why}")

sys.exit(r.finish())
