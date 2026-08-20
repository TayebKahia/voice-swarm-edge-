#!/usr/bin/env python3
"""Pre-review checks for Master Ch5 (Discussion and limitations). See tools/review/lib.py.

Discussion interprets Ch4; it may not introduce a measurement Ch4 did not report. So besides
recomputing its figures, this script requires every significant number in Ch5 to appear in Ch4's
prose or in a source Ch4 draws on, and it checks the register: hedged, and no verdict on RQ1
(that is Ch6's).

Only §5.1 is written at the time of writing; the script reports the unwritten sections instead of
failing on them, and the claims below cover §5.1. Add claims as §5.2-5.3 are drafted.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import MASTER, REPO, RESULTS, Chapter, Review, csv_rows, md_table, numbers, outline_check, significant  # noqa: E402
from eval.stats import nearest_rank  # noqa: E402

r = Review("master_ch5", "master", MASTER[4], [*MASTER[:4], *MASTER[5:]])
r.common()
text = r.ch.text

outline_check(r, 4, {"the accuracy-efficiency trade-off as a Pareto frontier": r"trade-off",
                     "failure-mode analysis": r"failure-mode", "threats to internal and external validity": r"threats"})
for sub in ("Internal validity", "External validity"):
    r.expect("outline", f"\\subsection{{{sub}}}" in text, f"threats split into `{sub}`")

# -- Sources, as in master_ch4.py ---------------------------------------------------------------
B = {(x["model"], x["quant"], x["split"]): float(x["exact_match"]) for x in csv_rows(RESULTS / "surface_b.csv")}
A = {(x["model"], x["split"]): float(x["exact_match"]) for x in csv_rows(REPO / "train/kaggle_out/surface_a.csv")
     if x["surface"] == "A_fp16_finetuned"}
Q, L, S, D = "qwen2.5-0.5b-instruct", "llama-3.2-1b-instruct", "smollm2-360m-instruct", "h2o-danube3-500m-chat"


def trials(path):
    out = {}
    for x in csv_rows(path):
        if not x["config"].endswith("-warmup"):
            out.setdefault(x["config"].removesuffix("-Q4_K_M"), []).append(x)
    return out


cool, hot = trials(RESULTS / "exp1_cooled.csv"), trials(RESULTS / "exp1.csv")
p95 = lambda rows, c: nearest_rank([float(x[c]) for x in rows], 95)  # noqa: E731
tot = {m: p95(v, "total_ms") for m, v in cool.items()}
tot_hot = {m: p95(v, "total_ms") for m, v in hot.items()}
rss = {m: max(float(x["peak_rss_mb"]) for x in v) / 1024 for m, v in cool.items()}
params = {x["Model"].strip("`"): float(x["Params"].replace(",", "").split()[0])
          for x in md_table(RESULTS / "table33_iso_parameter.md", "Model")}

# -- §5.1 figures ------------------------------------------------------------------------------
r.number("saves 178~ms of combined", tot[Q] - tot[S], "qwen - smollm2 total p95")
r.number("(1{,}072~ms to 894~ms)", tot[Q], "qwen total p95")
r.number("to 894~ms)", tot[S], "smollm2 total p95")
r.number("and 0.13~GB of peak", round(rss[Q], 2) - round(rss[S], 2), "0.68 - 0.55 GiB, as Ch4 rounds them")
r.number("costs 17.5~pp of exact", 100 * (B[(Q, "Q4_K_M", "test_golden")] - B[(S, "Q4_K_M", "test_golden")]), "qwen - smollm2 EM",
         places=1)
r.number("adds 1{,}210~ms", tot[L] - tot[Q], "llama - qwen total p95")
r.number("and 0.95~GB", round(rss[L], 2) - round(rss[Q], 2), "1.63 - 0.68 GiB")
r.number("within 4.0\\% of", 100 * (params[D] / params[Q] - 1), "514 / 494 - 1")
fam = 100 * (A[(Q, "test_golden")] - A[(D, "test_golden")])
r.number("scores 6.5~pp lower", fam, "surface_a qwen - danube golden", places=1)
gap = 100 * (B[(Q, "Q4_K_M", "test_golden")] - B[(S, "Q4_K_M", "test_golden")])
r.text_claim("claim", "more than a third of the distance", fam / gap > 1 / 3, f"6.5 / 17.5 = {fam / gap:.3f}")
r.text_claim("coherence", "more than a third of the distance", False,
             "6.5 pp is a Surface-A (FP16) gap; 17.5 pp is a Surface-B (Q4_K_M) gap -- the ratio mixes surfaces. "
             "Judge whether the sentence needs to say so", warn=True)
r.number("scores 0.760", B[(S, "Q4_K_M", "test_golden")], "smollm2 EM")
r.number("floor of 0.85 by 9~pp", 100 * (0.85 - B[(S, "Q4_K_M", "test_golden")]), "0.85 - 0.76", nth=1)
r.number("p95 is 1{,}771.5~ms", tot_hot[Q], "qwen uncooled total p95")
r.number("SmolLM2-360M's 1{,}610.2~ms", tot_hot[S], "smollm2 uncooled total p95")
r.text_claim("claim", "no\nconfiguration meets the stage allowance", all(v > 1350 for v in tot_hot.values()),
             f"uncooled total p95: { {m: round(v, 1) for m, v in tot_hot.items()} } all > 1350")
r.number("The combined stage is 278~ms", 1350 - tot[Q], "1350 - qwen total p95")
dq = p95(cool[Q], "slm_decode_ms")
r.number("decode alone is 1{,}033~ms", dq, "qwen decode p95")
r.number("a margin of 67~ms", 1100 - dq, "1100 - qwen decode p95")
r.number("or 6\\%", 100 * (1100 - dq) / 1100, "67 / 1100")
r.text_claim("claim", "Only three configurations have both an accuracy and a\nlatency coordinate", len(cool) == 3,
             f"{len(cool)} configurations have Pi latency")

# -- Discussion may not add a measurement Ch4 did not report ------------------------------------
earlier = {round(n.value, n.places) for c in MASTER[:4] for n in numbers(Chapter.load("master", c))}
claimed = {i.line for i in r.items if i.check == "claim" and i.status == "PASS"}
todo = {i for i, l in enumerate(r.ch.lines, 1) if "\\TODO{" in l}
for n in numbers(r.ch):
    if significant(n) and n.line not in todo and round(n.value, n.places) not in earlier:
        r.add("PASS" if n.line in claimed else "WARN", "new-number",
              f"{n.text} does not appear in Ch1-Ch4 -- " + ("recomputed by a claim, so it is a derived figure"
                                                        if n.line in claimed else "a new measurement? Discussion "
                                                        "should interpret Ch4, not extend it"), n.line)

# -- Register ----------------------------------------------------------------------------------
prose = r.ch.prose()
for m in re.finditer(r"answer(?:s|ed)? (?:to )?RQ1|RQ1 is answered|the verdict", prose):
    r.add("WARN", "register", f"`{m.group()}` -- the RQ1 verdict belongs to Ch6", prose.count("\n", 0, m.start()) + 1)
hedges = len(re.findall(r"\b(?:suggests?|appears?|may|might|plausible|reading|should be held)\b", r.ch.prose()))
r.expect("register", hedges >= 3, f"{hedges} hedging markers in the written sections (Discussion is hedged)", warn=True)
r.expect("table3", len(re.findall(r"Exp-3", r.ch.prose())) <= 1,
         f"Exp-3 mentioned {len(re.findall(r'Exp-3', r.ch.prose()))}x (the scaffold allows exactly once, in §5.3.2)")

r.manual.append("### For the argument agent\n\n- §5.1 argues the 'knee' is at Qwen specifically; check it does not "
                "slide back into a size claim anywhere.\n- 'feasible only because the board is cooled' -- the "
                "decode margin is 6%; is 'modest' the right strength, given one board and n = 60?\n"
                "- Check every number here against Ch4's *wording* too: Ch5 must not quote a Ch4 figure with a "
                "stronger qualifier than Ch4 gave it.")
sys.exit(r.finish())
