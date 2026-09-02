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
r.number("and 0.13~GiB of peak", round(rss[Q], 2) - round(rss[S], 2), "0.68 - 0.55 GiB, as Ch4 rounds them")
r.number("costs 17.5~pp of", 100 * (B[(Q, "Q4_K_M", "test_golden")] - B[(S, "Q4_K_M", "test_golden")]), "qwen - smollm2 EM",
         places=1)
r.number("adds 1{,}210~ms", tot[L] - tot[Q], "llama - qwen total p95")
r.number("and 0.95~GiB", round(rss[L], 2) - round(rss[Q], 2), "1.63 - 0.68 GiB")
r.number("within 4.0\\% of", 100 * (params[D] / params[Q] - 1), "514 / 494 - 1")
fam = 100 * (A[(Q, "test_golden")] - A[(D, "test_golden")])
r.number("scores 6.5~pp lower", fam, "surface_a qwen - danube golden", places=1)
gap_a = 100 * (A[(Q, "test_golden")] - A[(S, "test_golden")])
r.number("16.0~pp apart", gap_a, "surface_a qwen - smollm2 golden, FP16", places=1)
r.number("(0.935 against", A[(Q, "test_golden")], "surface_a qwen golden")
r.number("against 0.775)", A[(S, "test_golden")], "surface_a smollm2 golden")
# Both terms of the ratio on Surface A (FP16): the seeded finding was a Surface-A gap over a Surface-B gap.
r.text_claim("claim", "more than a third of the distance", fam / gap_a > 1 / 3,
             f"6.5 / 16.0 = {fam / gap_a:.3f}, both FP16")
r.number("since 0.935 against 0.760", B[(Q, "Q4_K_M", "test_golden")], "qwen EM")
r.number("since 0.935 against 0.760", B[(S, "Q4_K_M", "test_golden")], "smollm2 EM", nth=1)
r.number("also falls 9~pp short", 100 * (0.85 - B[(S, "Q4_K_M", "test_golden")]), "0.85 - 0.76")
e2e = {x["Stage"]: x for x in md_table(RESULTS / "exp2_latency_budget.md", "Stage")}
e2e_p95 = float(next(v for k, v in e2e.items() if "end of speech" in k)["p95"].replace(",", ""))
r.number("Qwen2.5-0.5B misses by 622~ms", e2e_p95 - 2500, "exp2 E2E p95 - 2500, as Ch4 4.7")
r.number("misses by 622~ms (25\\%)", 100 * (e2e_p95 / 2500 - 1), "exp2 E2E p95 / 2500 - 1", nth=1)
prefill2 = next(v for k, v in e2e.items() if "prefill" in k)
r.number("uncached prefill p95 is 751~ms", float(prefill2["p95"].replace(",", "")), "exp2 uncached prefill p95, as Ch4")
r.number("p95 is 1{,}771.5~ms", tot_hot[Q], "qwen uncooled total p95")
r.number("SmolLM2-360M's 1{,}610.2~ms", tot_hot[S], "smollm2 uncooled total p95")
r.text_claim("claim", "on the uncooled run no configuration fits", all(v > 1350 for v in tot_hot.values()),
             f"uncooled total p95: { {m: round(v, 1) for m, v in tot_hot.items()} } all > 1350")
r.number("The combined stage is 278~ms", 1350 - tot[Q], "1350 - qwen total p95")
dq = p95(cool[Q], "slm_decode_ms")
r.number("decode alone is 1{,}033~ms", dq, "qwen decode p95")
r.number("a margin of 67~ms", 1100 - dq, "1100 - qwen decode p95")
r.number("or 6\\%", 100 * (1100 - dq) / 1100, "67 / 1100")
r.text_claim("claim", "Only three configurations have both an accuracy and a\nlatency coordinate", len(cool) == 3,
             f"{len(cool)} configurations have Pi latency")

# -- §5.2 figures: decompositions of Ch4's aggregates, recomputed from results/limitation_abstention.md's sources --
from eval.abstention import taxonomy  # noqa: E402

ab = csv_rows(RESULTS / "nfr9_nfr18_abstention.csv")
err, safe = sum(int(x["errors"]) for x in ab), sum(int(x["safe_failures"]) for x in ab)
r.number("rate of 0.0530 reported", safe / err, "pooled safe failures / errors, all six artefacts")
r.number("Section~\\ref{sec:benchmark} is 28 errors", safe, "safe failures, pooled")
r.number("28 errors out of 528", err, "errors, pooled", nth=1)
r.text_claim("claim", "Twenty-four\nare the model emitting", sum(int(x["safe_model_hover"]) for x in ab) == 24,
             f"model hover = {sum(int(x['safe_model_hover']) for x in ab)}")
r.text_claim("claim", "Three are the semantic validator", sum(int(x["safe_validator_fallback"]) for x in ab) == 3,
             f"validator fallback = {sum(int(x['safe_validator_fallback']) for x in ab)}")
r.text_claim("claim", "One is the\nmodel emitting", sum(int(x["safe_model_unknown"]) for x in ab) == 1,
             f"model unknown = {sum(int(x['safe_model_unknown']) for x in ab)}")
fcr = [float(x["false_command_rate"]) for x in ab if x["split"] == "test_ood"]
r.number("abstain on 60.7\\% to", 100 * (1 - max(fcr)), "1 - worst false-command rate", places=1)
r.number("to 81.3\\% of items", 100 * (1 - min(fcr)), "1 - best false-command rate", places=1)
ind = [x for x in ab if x["split"] != "test_ood"]
r.number("configurations make 282 errors", sum(int(x["errors"]) for x in ind), "in-domain errors, pooled")
r.text_claim("claim", "once in 2{,}640 decodes",
             sum(int(x["volunteered_unknown"]) for x in ind) == 1 and sum(int(x["n"]) for x in ind) == 2640,
             f"volunteered unknown {sum(int(x['volunteered_unknown']) for x in ind)} in {sum(int(x['n']) for x in ind)}")
fp16_ood = {m: 100 * A[(m, "test_ood")] for m in (Q, L, S, D)}
r.number("abstain on 62.0\\% to", fp16_ood[S], "surface_a smollm2 test_ood", places=1)
r.number("to 73.3\\% of\nthe out-of-domain", fp16_ood[L], "surface_a llama test_ood", places=1)
r.text_claim("claim", "abstain on 62.0\\% to", min(fp16_ood[m] for m in (Q, L, S)) == fp16_ood[S]
             and max(fp16_ood[m] for m in (Q, L, S)) == fp16_ood[L], "62.0 and 73.3 are the min and max of the three")
r.number("inside that spread at 72.0\\%", fp16_ood[D], "surface_a danube test_ood", places=1)
tax = taxonomy()
r.number("Of the 282, 240", tax["total"], "taxonomy total")
r.number("Of the 282, 240", tax["right intent, wrong parameters"], "right intent, wrong parameters", nth=1)
r.number("240 (85.1\\%)", 100 * tax["right intent, wrong parameters"] / tax["total"], "share", places=1, nth=1)
r.number("39 (13.8\\%)", tax["wrong intent, still actionable"], "wrong intent, actionable")
r.number("39 (13.8\\%)", 100 * tax["wrong intent, still actionable"] / tax["total"], "share", places=1, nth=1)
r.number("3 (1.1\\%) resolve", tax["resolved to a safe action"], "safe")
r.number("3 (1.1\\%) resolve", 100 * tax["resolved to a safe action"] / tax["total"], "share", places=1, nth=1)
r.number("so 98.9\\% dispatch", 100 * (1 - tax["resolved to a safe action"] / tax["total"]), "executable share", places=1)
r.number("yaw angle: 114 of the 282", tax["yaw sign flips"], "yaw sign flips")
r.number("errors (40.4\\%) turn", 100 * tax["yaw sign flips"] / tax["total"], "yaw share", places=1)

import json  # noqa: E402

it = {x["id"]: x for x in map(json.loads, (RESULTS / "surface_b_preds/qwen2.5-0.5b-instruct-Q4_K_M_test_golden.jsonl")
                                  .read_text().splitlines())}["0036"]
r.text_claim("claim", "heading 163.0 clockwise, number 1", it["transcript"] == "heading 163.0 clockwise, number 1",
             "item 0036: quoted transcript")
r.text_claim("claim", "reference yaw is $-163.0$", json.loads(it["gold"])["yaw"] == -163.0
             and json.loads(it["raw"])["yaw"] == 163.0, "item 0036: reference -163.0, Qwen Q4_K_M +163.0")

# -- §5.3.1 --------------------------------------------------------------------------------------
import math  # noqa: E402

r.text_claim("claim", "more than five orders of\nmagnitude below", math.log10(0.05 / 3 / 1.1e-7) > 5,
             f"log10(0.0167 / 1.1e-7) = {math.log10(0.05 / 3 / 1.1e-7):.2f}")
r.text_claim("claim", "Six threats remain", len(re.findall(r"\\paragraph\{", text[text.index("subsection{Internal validity}"):
                                                                          text.index("subsection{External validity}")])) == 6,
             "six \\paragraph lead-ins in the internal-validity subsection")

# -- §5.3.2: the one reference to the acoustic-robustness experiment (Table 3), and parity ---------
pi = {x["condition"]: x for x in csv_rows(RESULTS / "exp3_pi.csv")}
par = {x["condition"]: x for x in csv_rows(RESULTS / "exp3_pi_parity.csv")}
r.text_claim("claim", "identical to the workstation's on all 200 items",
             par["text"]["n"] == "200" and par["text"]["raw_differs"] == "0" and par["text"]["outcome_flips"] == "0",
             f"exp3_pi_parity.csv text: n {par['text']['n']}, raw differs {par['text']['raw_differs']}")
r.number("\\gls{crr} is 0.690 on clean", float(pi["clean"]["crr"]), "exp3_pi.csv clean CRR (Pi, of record)")
r.number("and 0.590 at 10~dB", float(pi["10"]["crr"]), "exp3_pi.csv 10 dB CRR")
r.number("against an \\gls{em} of\n0.935", float(pi["clean"]["em"]), "exp3_pi.csv EM on the same items")
names = len(re.findall(r"acoustic-robustness\s+experiment", r.ch.prose()))
r.expect("table3", names == 1, f"the acoustic-robustness experiment is named {names}x in Ch5 (Table 3: exactly once, in 5.3.2)")

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
