#!/usr/bin/env python3
"""Pre-review checks for Ingénieur Ch3 (Architecture and design). See tools/review/lib.py.

Ch3 is a design chapter: it states targets and rules, never results ("Every figure in this chapter
is a design target"). Its sources are therefore the code and the other tables that fix the same
targets, not results/:
  - the membership table against runtime/branch_a.py (which intents the reflex path carries) and
    schema/schema.py (the ten intents);
  - the validator's envelope against schema/schema.py ENVELOPE, and the legality table against
    swarm/fsm.py TABLE_9_LEGALITY;
  - tab:stage-budget against the generated latency table Ch5 inputs (same stage names, same
    targets), Master tab:latency-budget and Ch1's criteria table;
  - the endpointing derivation against runtime/vad.py, the frame against runtime/stream.py, and
    the core allocation against runtime/parser.py and runtime/pipeline.py.
It also enforces the chapter's own promise: no measured latency from the latency experiment.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import INGENIEUR, REPO, THESIS, Review, numbers, outline_check, prd  # noqa: E402

sys.path.insert(0, str(REPO))
from schema.schema import ENVELOPE, INTENTS, POS_MAX_NORM, SWARM_SIZE  # noqa: E402
from schema.validate import _clamp_pos  # noqa: E402
from swarm.fsm import TABLE_9_LEGALITY, FlightState  # noqa: E402

r = Review("ingenieur_ch3", "ingenieur", INGENIEUR[3], [*INGENIEUR[:3], *INGENIEUR[4:]])  # Architecture, Chapter 4 since 26 Sep
r.common()
text = r.ch.text


def code(path: str, pattern: str) -> str:
    """First group of `pattern` in a source file; the script reads constants rather than importing
    runtime/, whose modules pull in onnxruntime and llama bindings at import time."""
    m = re.search(pattern, (REPO / path).read_text(encoding="utf-8"), flags=re.M)
    if not m:
        r.add("FAIL", "source", f"`{pattern}` not found in {path} -- the code moved; update the script")
        return "0"
    return m.group(1)


def num(s: str) -> float:
    return float(re.sub(r"[^\d.]", "", s.replace("{,}", "")) or "nan")


def table(label: str) -> list[list[str]]:
    """Cells of every data row (after \\midrule) of the tabularx carrying `label`."""
    m = re.search(rf"\\label\{{{label}\}}(.*?)\\end\{{tabularx\}}", text, flags=re.S)
    if not m:
        r.add("FAIL", "table", f"table {label} not found")
        return []
    body = m.group(1)[m.group(1).find("\\midrule"):]
    return [[c.strip() for c in (" " + row).split(" & ")] for row in re.findall(r"^\s*(.*?&.*?)\\\\\s*$", body, flags=re.M)]


def plain(cell: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\\textbf\{(.*)\}", r"\1", cell)).strip()


outline_check(r, 3, {"the dual-path decomposition": r"dual-path", "the Branch A membership rule": r"membership",
                     "the three validation layers": r"validation layers", "the latency budget": r"latency budget",
                     "resource allocation": r"resource allocation", "the speech components": r"speech components"})
extra = [t for lvl, t, _ in r.ch.sections() if lvl == "section" and not re.search(
    r"dual-path|membership|validation layers|latency budget|resource allocation|speech components", t, flags=re.I)]
r.expect("outline", not extra, "no sections beyond prd.md §3.1 item 4" if not extra
         else f"sections beyond prd.md §3.1 item 4: {extra}", warn=True)
r.expect("label", "\\label{chap:architecture}" in text, "carries \\label{chap:architecture}")

# -- Labels: tab:latency-budget belongs to the generated table Ch5 inputs ----------------------------
own = re.findall(r"\\label\{([^}]*)\}", text)
others = {}
for c in r.siblings:
    for src in [c.text, *[p.read_text(encoding="utf-8") for p in c.inputs() if p.is_file()]]:
        for k in re.findall(r"\\label\{([^}]*)\}", src):
            others.setdefault(k, c.path.stem)
gen = (THESIS / "generated/exp2_latency_budget.tex").read_text(encoding="utf-8")
for k in re.findall(r"\\label\{([^}]*)\}", gen):
    others.setdefault(k, "generated/exp2_latency_budget.tex")
clash = [(k, others[k]) for k in own if k in others]
r.expect("label", not clash, f"none of the chapter's {len(own)} labels is defined elsewhere in the document"
         if not clash else f"labels defined twice in the document: {clash}")

# -- Write-once (Table 3): the schema and grammar belong to the Master ---------------------------------
r.expect("table3", "::=" not in text, "no grammar listing (Master Ch3 owns the grammar)" if "::=" not in text
         else "a grammar rule (`::=`) appears -- the Master owns the listing; state what this document needs")
r.expect("table3", bool(re.search(r"specified,\s+with the grammar in full,\s+in the \\emph\{M\\'emoire de Master\}", text)),
         "layer 1 hands the schema and grammar to the \\emph{Mémoire de Master} in one sentence",
         (r.ch.find("Layer 1: the decoding grammar") or [None])[0])
master_only = {"geng2023", "willard2023", "koo2024", "park2024", "tam2024", "gptq", "awq", "spqr",
               "kurtic2025", "kurt2026", "slmquant", "sbc2025", "lora", "qlora"}
used = {k.strip() for m in re.findall(r"\\cite\{([^}]*)\}", text) for k in m.split(",")}
r.expect("table3", not used & master_only, "no Master-owned literature re-surveyed" if not used & master_only
         else f"Master-owned literature cited: {sorted(used & master_only)}")
r.text_claim("table3", "The language model on the parse path is Qwen2.5-0.5B",
             "Q4\\_K\\_M" in text[text.find("Qwen2.5-0.5B"):text.find("Qwen2.5-0.5B") + 200],
             "selected configuration named (Qwen2.5-0.5B, Q4_K_M), not derived (Table 3: Master Ch4 owns it)")

# -- 3.1: the prompt estimate is the design's, and the context window is the parser's -----------------
r.text_claim("design", "roughly 15 tokens per command",
             bool(re.search(r"roughly 15 tokens instead of roughly 290", prd())),
             "15 vs 290 prefill tokens is prd.md §4 decision 3's design estimate (declared, not measured)")
r.number("512-token context window", int(code("runtime/parser.py", r"^DEFAULT_CONTEXT = (\d+)")),
         "runtime/parser.py DEFAULT_CONTEXT")

# -- 3.2: the membership table against the reflex path's code --------------------------------------
reflex_code = set(re.findall(r'"swarm_\w+":\s*"(\w+)"',
                             code("runtime/branch_a.py", r"(KEYWORD_TO_INTENT[^}]*\})")))
rows = table("tab:membership")
intents = {re.sub(r"\\texttt\{(.*)\}", r"\1", row[0]).replace("\\_", "_") for row in rows}
r.expect("membership", intents == set(INTENTS), f"tab:membership lists the schema's {len(INTENTS)} intents"
         if intents == set(INTENTS) else f"tab:membership intents {sorted(intents ^ set(INTENTS))} differ from schema")
reflex_rows = {re.sub(r"\\texttt\{(.*)\}", r"\1", row[0]) for row in rows if row[-1].strip() == "Reflex"}
r.expect("membership", reflex_rows == reflex_code, f"reflex rows {sorted(reflex_rows)} = runtime/branch_a.py "
         f"KEYWORD_TO_INTENT {sorted(reflex_code)}")
bad = [row[0] for row in rows if (row[-1].strip() == "Reflex") != (row[1].startswith("Yes") and row[2].startswith("Yes"))]
r.expect("membership", not bad, "a row is Reflex exactly when both tests say Yes" if not bad
         else f"rows whose Path does not follow from the two tests: {bad}")
dash = [row[0] for row in rows if row[1].strip() == "--" and not row[2].startswith("No")]
r.expect("membership", not dash, "every untested (--) latency cell sits beside a failed fail-safe test" if not dash
         else f"-- in the latency column without a failed fail-safe test: {dash}")
r.number("applies both tests to the ten intents of the schema", len(INTENTS), "schema/schema.py INTENTS")
r.number("of the schema. Exactly two pass", len(reflex_code), "runtime/branch_a.py KEYWORD_TO_INTENT")

# The arithmetic of the latency-decisive test, from the targets and the envelope.
e2e, reflex = 2500, 150
r.number("$2{,}500 - 150 = 2{,}350$", e2e - reflex, "Ch1 end-to-end minus reflex target", nth=2)
r.number("speed ceiling of 2.0~m/s", ENVELOPE["speed"][1], "schema/schema.py ENVELOPE speed")
r.number("that interval is 4.7~m of travel", (e2e - reflex) / 1000 * ENVELOPE["speed"][1],
         "2.35 s x speed ceiling")
r.number("the envelope admits (10~m)", ENVELOPE["radius"][1], "ENVELOPE radius")
r.number("inter-drone spacing (1--5~m)", ENVELOPE["spacing"][0], "ENVELOPE spacing", nth=0)
r.number("inter-drone spacing (1--5~m)", ENVELOPE["spacing"][1], "ENVELOPE spacing", nth=1)
r.number("an altitude envelope of 0.5--15~m", ENVELOPE["z"][0], "ENVELOPE z", nth=0)
r.number("an altitude envelope of 0.5--15~m", ENVELOPE["z"][1], "ENVELOPE z", nth=1)
r.number("where the added 2.35~s costs", (e2e - reflex) / 1000, "end-to-end minus reflex target, in s")

# -- 3.3: layer 1 properties, the validator's envelope, the legality table ---------------------------
gbnf = (REPO / "schema/cmd.gbnf").read_text(encoding="utf-8")
r.text_claim("grammar", "at three integer digits and one decimal place",
             bool(re.search(r'num\s*::= "-"\? \[0-9\] \[0-9\]\? \[0-9\]\? \( "\." \[0-9\] \)\?', gbnf)),
             "schema/cmd.gbnf num rule: at most three integer digits, one decimal")
r.text_claim("grammar", "restricts drone identifiers to the five that exist",
             '[0-4] ( "," [0-4] ){0,4}' in gbnf and SWARM_SIZE == 5, "cmd.gbnf idlist [0-4], N = 5")
r.number("with one of ten intents and a fixed key order", len(re.findall(r'\\"intent\\":\\"(\w+)', gbnf)),
         "intents in schema/cmd.gbnf", nth=1)
for anchor, slot, nth in (("A radius is clamped to 1--10~m", "radius", 0), ("A radius is clamped to 1--10~m", "radius", 1),
                          ("spacing to 1--5~m", "spacing", 0), ("spacing to 1--5~m", "spacing", 1),
                          ("a target height to 0.5--15~m", "z", 0), ("a target height to 0.5--15~m", "z", 1),
                          ("its height clamped to 0.5--15~m", "z", 0), ("its height clamped to 0.5--15~m", "z", 1),
                          ("a speed to 0.2--2.0~m/s", "speed", 0), ("a speed to 0.2--2.0~m/s", "speed", 1)):
    r.number(anchor, ENVELOPE[slot][nth], f"ENVELOPE {slot}[{nth}]", nth=nth)
r.number("a distance to at most 50~m", ENVELOPE["dist"][1], "ENVELOPE dist (ADR-0001)")
r.number("more than 50~m from the origin", POS_MAX_NORM, "schema/schema.py POS_MAX_NORM")
# Height clamped on its own first, then only (x, y) scaled: [30,30,20] loses its bearing to the z
# clamp alone (norm 46.9 < 50); [40,40,5] keeps it. The prose once said the whole vector is scaled.
_hi, _far = _clamp_pos((30.0, 30.0, 20.0)), _clamp_pos((40.0, 40.0, 5.0))
r.text_claim("claim", "its horizontal part alone is scaled down",
             _hi == (30.0, 30.0, 15.0) and _far[2] == 5.0 and abs(_far[0] - _far[1]) < 1e-9
             and abs(sum(v * v for v in _far) ** 0.5 - POS_MAX_NORM) < 0.1,
             "schema/validate.py _clamp_pos: z clamped first, then only x, y scaled to the 50 m norm")
r.number("wrapped into $[-180^\\circ, 180^\\circ]$", ENVELOPE["yaw"][1], "ENVELOPE yaw", nth=1)

STATES = {s.value for s in FlightState}
legal_rows = table("tab:legality")
checked = 0
for row in legal_rows:
    names = [n.replace("\\_", "_") for n in re.findall(r"\\texttt\{([a-z\\_]+)\}", row[0])]
    cell = row[1]
    if "never dispatched" in cell:
        states = set()
    elif re.search(r"every state except", cell):
        states = STATES - {s.replace("\\_", "_") for s in re.findall(r"\\texttt\{([A-Z\\_]+)\}", cell)}
    else:
        states = {s.replace("\\_", "_") for s in re.findall(r"\\texttt\{([A-Z\\_]+)\}", cell)}
    for n in names:
        want = {s.value for s in TABLE_9_LEGALITY.get(n, set())}
        r.expect("legality", states == want, f"`{n}` legal in {sorted(states)} = swarm/fsm.py {sorted(want)}"
                 if states == want else f"`{n}` legal in {sorted(states)} but swarm/fsm.py says {sorted(want)}",
                 (r.ch.find(row[0]) or [None])[0])
        checked += 1
r.expect("legality", checked == len(TABLE_9_LEGALITY), f"tab:legality covers {checked} of "
         f"{len(TABLE_9_LEGALITY)} intents in swarm/fsm.py")
hover = {s.value for s in TABLE_9_LEGALITY["hover"]}
r.text_claim("legality", "in \\texttt{TAKING\\_OFF} and \\texttt{FLYING}, and to a logged no-op",
             hover == {"TAKING_OFF", "FLYING"}, "rejection -> hold exactly where hover is legal (ADR-0002)")

# -- 3.4: tab:stage-budget against the three tables that fix the same targets -------------------------
budget = {plain(row[1]): num(row[2]) for row in table("tab:stage-budget") if len(row) == 3}
r.expect("budget", len(budget) == 10, f"tab:stage-budget: {len(budget)} rows read (10 expected)")
gen_rows = {}
for m in re.finditer(r"^\s*(.+?) & \d[\d,]* & [^&]* & [^&]* & [^&]* & ([^&]+?) & [^&]*\\\\", gen, flags=re.M):
    gen_rows[plain(m.group(1))] = m.group(2).strip()
for name, target in budget.items():
    match = gen_rows.get(name) or gen_rows.get(f"{name}, idle")
    if match is None:
        if name.startswith("End to end, from start of speech"):
            ok = "5,500 ms target is for a 3 s utterance" in gen and target == 5500
            r.expect("budget", ok, f"`{name}` {target:g} ms = the generated table's note (5,500 ms, 3 s utterance)")
        elif name == "Language-model stages combined":
            continue  # checked against the Master below
        else:
            r.add("FAIL", "budget", f"stage `{name}` has no row of the same name in generated/exp2_latency_budget.tex "
                  "-- Ch5 sets the two tables side by side; the names must match")
        continue
    ok = num(match) == target
    r.expect("budget", ok, f"`{name}` {target:g} ms = generated table target {match}" if ok
             else f"`{name}` {target:g} ms but the generated table's target is {match}")
master = (THESIS / "master/ch3_method.tex").read_text(encoding="utf-8")
mb = re.search(r"\\label\{tab:latency-budget\}(.*?)\\end\{tabular\}", master, flags=re.S)
mrows = {plain(a): num(b) for a, b in re.findall(r"^\s*(.+?) & ([\d{},]+)~ms \\\\", mb.group(1) if mb else "", flags=re.M)}
MASTER_NAMES = {"Endpointing wait": "Endpointing (wait to confirm end of speech)",
                "Speech recognition (whisper \\texttt{tiny.en}, 3 threads)": "Speech recognition (\\texttt{whisper.cpp tiny.en})",
                "Language-model prefill": "Language-model prefill (cached prefix)",
                "Language-model decode": "Language-model decode",
                "Validation, state-machine check and dispatch": "Validation, state-machine check and dispatch",
                "Language-model stages combined": "Language-model stages combined",
                "End to end, from end of speech": "End to end, from end of speech"}
for mine, theirs in MASTER_NAMES.items():
    if mine not in budget or theirs not in mrows:
        r.add("FAIL", "budget", f"row `{mine}` / Master `{theirs}` not found -- a name changed; update the script")
        continue
    r.expect("budget", budget[mine] == mrows[theirs], f"`{mine}` {budget[mine]:g} ms = Master tab:latency-budget "
             f"`{theirs}` {mrows[theirs]:g} ms")
ch1 = (THESIS / "ingenieur/ch1_introduction.tex").read_text(encoding="utf-8")
for crit, mine in (("Reflex latency", "Reflex path from keyword offset"),
                   ("End-to-end latency", "End to end, from end of speech")):
    m = re.search(rf"^{crit} & .*?\$\\leq\$ ([\d{{}},]+)~ms", ch1, flags=re.M)
    r.expect("budget", bool(m) and num(m.group(1)) == budget.get(mine), f"`{mine}` {budget.get(mine, 0):g} ms = "
             f"Ch1 `{crit}` {m.group(1) if m else '?'} ms")
m = re.search(r"^Preemption recovery & .*?\$\\leq\$ ([\d{},]+)~ms", ch1, flags=re.M)
r.number("preemption-recovery criterion bounds at 300~ms", num(m.group(1)) if m else -1,
         "Ch1 tab:nonfunctional-requirements Preemption recovery")
parse_after_t0 = ["Speech recognition (whisper \\texttt{tiny.en}, 3 threads)", "Language-model prefill",
                  "Language-model decode", "Validation, state-machine check and dispatch"]
if all(k in budget for k in parse_after_t0):
    r.number("$T_0$ sum to 2{,}600~ms", sum(budget[k] for k in parse_after_t0), "sum of the four stage rows after T0")
    r.number("The two language-model rows together allow 1{,}350~ms",
             budget["Language-model prefill"] + budget["Language-model decode"], "prefill + decode rows", nth=1)
    r.number("& Language-model stages combined & 1{,}350~ms",
             budget["Language-model prefill"] + budget["Language-model decode"], "prefill + decode rows")
rate = int(code("runtime/vad.py", r"^RATE = ([\d_]+)").replace("_", ""))
window_ms = int(code("runtime/vad.py", r"^WINDOW = (\d+)")) / rate * 1000
silence = int(code("runtime/vad.py", r"min_silence_ms: int = (\d+)"))
r.number("whole windows of 32~ms", window_ms, "runtime/vad.py WINDOW / RATE")
r.number("inside the allowance: 450~ms", silence, "runtime/vad.py Endpointer min_silence_ms default")
r.number("for a worst case of 482~ms", silence + window_ms, "min_silence_ms + one window")
r.expect("budget", silence + window_ms <= budget.get("Endpointing wait", 0),
         f"worst-case wait {silence + window_ms:g} ms fits the {budget.get('Endpointing wait', 0):g} ms row")
frame_ms = int(code("runtime/stream.py", r"^FRAME = (\d+)")) / rate * 1000
r.number("quantisation of audio into 80~ms frames", frame_ms, "runtime/stream.py FRAME / RATE")

# -- 3.5: the core allocation against the runtime ------------------------------------------------
r.number("The Raspberry~Pi~5 has four Cortex-A76 cores", 4, "prd.md Table 1 / Ch1", nth=1) if "Cortex-A76" in prd() else None
lm_threads = int(code("runtime/parser.py", r"^DEFAULT_THREADS = (\d+)"))
stt_threads = int(code("runtime/pipeline.py", r"stt_threads: int = (\d+)"))
r.text_claim("cores", "the language model, each on three threads", lm_threads == stt_threads == 3,
             f"parser DEFAULT_THREADS = {lm_threads}, PipelineRuntime stt_threads = {stt_threads}")
r.number("The frame loop takes one 80~ms frame", frame_ms, "runtime/stream.py FRAME / RATE", nth=1)
r.text_claim("cores", "the 2.5~GiB ceiling on the full deployed stack",
             bool(re.search(r"Memory ceiling & .*?full stack.*?\$\\leq\$ 2\.5~GiB", master)),
             "2.5 GiB full-stack ceiling as Master tab:requirements states it")
r.text_claim("cores", "the full stack was not measured for any",
             bool(re.search(r"No full-stack measurement was", (THESIS / "master/ch4_results.tex").read_text())),
             "agrees with Master Ch4: no full-stack memory measurement")

# -- The chapter's promise: design targets only, no measured latency -----------------------------
measured = set()
for m in re.finditer(r"^\s*.+? & (\d[\d,]*) & ([\d,]+) & ([\d,]+) & ([\d,]+) &", gen, flags=re.M):
    measured |= {num(x) for x in m.groups()[1:]}
targets = set(budget.values()) | {300.0, 482.0, 450.0, 32.0, 80.0, 2350.0, 2600.0}
leaks = [(n.text, n.line) for n in numbers(r.ch) if n.unit and n.value in measured - targets]
r.expect("promise", not leaks, "no measured latency from the latency experiment appears (design targets only)"
         if not leaks else f"measured latency values in a design chapter: {leaks} -- Ch5 reports them")

r.manual.append("""### For the argument agent

- **Promises from Ch1 this chapter must keep** (promise table P1-P31,
  `.scratch/thesis-review/agents/06-ingenieur-ch1/argument.md`): P6, P7, P8, P14-P18, P21, P25, P26,
  P28 point at chap:architecture. P15 and P17 were fixed in Ch1 (a rejection is a hold or a logged no-op;
  the reflex path skips interpretation, not validation): check Ch3 states both exactly as Ch1 now does.
- **Promises this chapter makes to later chapters**: Ch4 sec:runtime owes the reason the deployed parser
  does not cache the prefix (3.1, prompt and prefix); Ch4 realises the separation clamp (lead-in); Ch5
  sec:latency-experiment measures isolation under load (3.5) and every budget row (3.4);
  sec:acoustic-robustness reports the endpointer's split cost (3.4) and the safe-failure rate (3.3).
  List each with the label it points to.
- **Design claims that rest on code, not on prd.md**: layer 2 envelope (schema/schema.py, ADR-0001),
  rejection rule (ADR-0002, swarm/fsm.py), land from TAKING_OFF (fsm.py), the sequence number reserved
  when an utterance is accepted (runtime/pipeline.py), every command validated (Dispatcher ->
  fsm.handle_command -> validate). The script checks the tables; the prose claims are yours.
- **Two points the author decided to keep as written**: the start-of-speech target of 5,500 ms is not
  derived (3,000 + 500 + 2,500 = 6,000 -- known, left as is, 2026-09-24); the four stage ceilings after
  T0 sum to 2,600 ms > 2,500 ms, stated deliberately. Neither is a finding unless the prose around it is
  wrong.
- **End point of the spans**: Ch1 and 3.4 say both spans end at the bus on the device;
  eval/exp2.py:355 stops at the state machine having applied the command. A Ch5 obligation, not a Ch3
  error -- report it only if Ch3's own wording contradicts Ch1.""")
sys.exit(r.finish())
