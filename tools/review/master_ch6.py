#!/usr/bin/env python3
"""Pre-review checks for Master Ch6 (Conclusion and future work). See tools/review/lib.py.

The Conclusion states results unhedged, and the risk that register carries is a result stated
more strongly than Ch4 stated it. So this script is stricter than Ch5's on inheritance: a
significant number that appears in no earlier chapter is a FAIL, not a WARN -- Ch6 concludes on
what Ch4 measured and may not extend it. Each figure is also recomputed from the file Ch4 draws it
from, and the register is checked in the opposite direction to Ch5's: hedging words fail.

Needs the pfe_swarm env (eval.stats imports numpy and scipy).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import MASTER, REPO, RESULTS, Chapter, Review, csv_rows, md_table, numbers, outline_check, significant  # noqa: E402
from eval.stats import nearest_rank  # noqa: E402

r = Review("master_ch6", "master", MASTER[6], MASTER[:6])  # Conclusion, Chapter 7 since 25 Sep
r.common()
text, prose = r.ch.text, r.ch.prose()

outline_check(r, 6, {"RQ1 answered directly against the measured results": r"research question",
                     "a summary of what the comparison establishes": r"establishes",
                     "prioritised next steps": r"next steps"})

# -- Sources, as in master_ch4.py ---------------------------------------------------------------
B = {(x["model"], x["quant"], x["split"]): x for x in csv_rows(RESULTS / "surface_b.csv")}
B_off = {(x["model"], x["quant"], x["split"]): x for x in csv_rows(RESULTS / "surface_b_nogrammar.csv")}
A = {(x["model"], x["split"]): float(x["exact_match"]) for x in csv_rows(REPO / "train/kaggle_out/surface_a.csv")
     if x["surface"] == "A_fp16_finetuned"}
A0 = [x for x in csv_rows(REPO / "train/kaggle_out/surface_a.csv") if x["surface"] == "A_fp16_zeroshot"]
Q, L, S, D = "qwen2.5-0.5b-instruct", "llama-3.2-1b-instruct", "smollm2-360m-instruct", "h2o-danube3-500m-chat"
em = lambda m, q="Q4_K_M", s="test_golden": float(B[(m, q, s)]["exact_match"])  # noqa: E731
params = {x["Model"].strip("`"): float(x["Params"].replace(",", "").split()[0])
          for x in md_table(RESULTS / "table33_iso_parameter.md", "Model")}


def trials(path):
    out = {}
    for x in csv_rows(path):
        if not x["config"].endswith("-warmup"):
            out.setdefault(x["config"].removesuffix("-Q4_K_M"), []).append(x)
    return out


cool, hot = trials(RESULTS / "exp1_cooled.csv"), trials(RESULTS / "exp1.csv")
p95 = lambda rows, c: nearest_rank([float(x[c]) for x in rows], 95)  # noqa: E731
tot = {m: p95(v, "total_ms") for m, v in cool.items()}
rss = {m: max(float(x["peak_rss_mb"]) for x in v) / 1024 for m, v in cool.items()}
e2e = {x["Stage"]: x for x in md_table(RESULTS / "exp2_latency_budget.md", "Stage")}
e2e_p95 = float(next(v for k, v in e2e.items() if "end of speech" in k)["p95"].replace(",", ""))
mc = csv_rows(RESULTS / "mcnemar.csv")
ab = csv_rows(RESULTS / "nfr9_nfr18_abstention.csv")

# -- 6.1 the answer -----------------------------------------------------------------------------
r.number("at 0.935 \\gls{em} on the golden split", em(Q), "surface_b qwen Q4_K_M golden")
r.number("p95 of 894~ms against", tot[S], "smollm2 total p95, cooled")
r.number("Qwen2.5-0.5B's 1{,}072~ms", tot[Q], "qwen total p95, cooled")
r.number("scores 0.760, 17.5~pp lower", em(S), "surface_b smollm2 golden")
r.number("scores 0.760, 17.5~pp lower", 100 * (em(Q) - em(S)), "qwen - smollm2 EM", places=1, nth=1)
qs = next(x for x in mc if x["family"] == "model" and {x["system_a"], x["system_b"]} == {Q, S})
r.text_claim("claim", "a gap significant at the corrected", qs["significant"] == "yes",
             f"mcnemar qwen-smollm2: p {qs['p_value']} against alpha {qs['alpha']}")
r.number("at 1.24~B parameters", params[L] / 1000, "table33 llama params", places=2)
r.number("scores 0.910 there", em(L), "surface_b llama golden")
lq = next(x for x in mc if x["family"] == "model" and {x["system_a"], x["system_b"]} == {Q, L})
r.text_claim("claim", "the test does not establish", lq["significant"] == "no",
             f"mcnemar llama-qwen: p {lq['p_value']} against alpha {lq['alpha']}")
r.number("and takes 2{,}282~ms", tot[L], "llama total p95, cooled")
r.number("as specified by 622~ms (25\\%)", e2e_p95 - 2500, "exp2 E2E p95 - 2500, as Ch4 4.7")
r.number("as specified by 622~ms (25\\%)", 100 * (e2e_p95 / 2500 - 1), "exp2 E2E p95 / 2500 - 1", nth=1)
r.number("measured p95 of 3{,}122~ms", e2e_p95, "exp2 E2E p95 from end of speech")
r.number("at 0.68~GiB against", rss[Q], "qwen peak RSS, cooled", places=2)
rate = [int(x["safe_failures"]) / int(x["errors"]) for x in ab if int(x["errors"])]
r.number("rate is 0.0000--0.1579 against", min(rate), "min per-row safe-failure rate")
r.number("rate is 0.0000--0.1579 against", max(rate), "max per-row safe-failure rate", nth=1)
fcr = [float(x["false_command_rate"]) for x in ab if x["split"] == "test_ood"]
r.number("input is 0.1867--0.3933 against", min(fcr), "min false-command rate")
r.number("input is 0.1867--0.3933 against", max(fcr), "max false-command rate", nth=1)
first = text[text.index("\\label{sec:rq1-answer}"):].split("\n\n")[1]
r.expect("rq1", "trade-off" in first and "Qwen2.5-0.5B at Q4\\_K\\_M" in first,
         "the first paragraph of 6.1 answers RQ1: names the trade-off and the selected configuration")

# -- 6.2 what the comparison establishes -------------------------------------------------------
r.text_claim("claim", "is 1.000 on all eighteen rows", len(B) == 18 and all(float(x["schema_validity"]) == 1.0
                                                                          for x in B.values()),
             f"{len(B)} Surface-B rows, all schema_validity 1.0")
n_all = sum(int(x["n"]) for x in B.values())
hits_on = sum(float(x["exact_match"]) * int(x["n"]) for x in B.values())
hits_off = sum(float(x["exact_match"]) * int(x["n"]) for x in B_off.values())
valid_off = sum(float(x["schema_validity"]) * int(x["n"]) for x in B_off.values())
r.number("over 3{,}540 decodes without it", n_all, "sum of n, surface_b")
r.text_claim("claim", "exactly one output is malformed", round(n_all - valid_off) == 1,
             f"{round(n_all - valid_off)} invalid decodes, grammar off")
r.number("falls by 0.17~pp", 100 * (hits_on - hits_off) / n_all, "pooled EM difference, grammar on - off", places=2)
r.text_claim("claim", "difference falling in its favour", hits_on > hits_off, "pooled EM higher with the grammar")
r.number("four models match none of the 590 items", n_all / 6, "3540 / 6 artefacts", nth=1)
r.text_claim("claim", "four models match none of the 590 items",
             len({x["model"] for x in A0}) == 4 and all(float(x["exact_match"]) == 0 for x in A0),
             f"{len(A0)} zero-shot rows over {len({x['model'] for x in A0})} models, all EM 0")
deltas = [100 * (em(m, q) - A[(m, "test_golden")]) for m in (Q, L, S) for q in ("Q4_K_M", "Q8_0")]
r.number("moves by $-$1.5 to $+$1.5~pp", -min(deltas), "min delta, negated", places=1)
r.number("moves by $-$1.5 to $+$1.5~pp", max(deltas), "max delta", places=1, nth=1)
dep = [x for x in mc if x["family"] == "deployment"]
r.number("whose smallest $p$ is 0.25", min(float(x["p_value"]) for x in dep), "min p, deployment family")
r.text_claim("claim", "none is significant in the", all(x["significant"] == "no" for x in dep),
             "every deployment row: significant = no")
dec = {m: 100 * (1 - p95(cool[m], "slm_decode_ms") / p95(hot[m], "slm_decode_ms")) for m in cool}
r.text_claim("claim", "every trial throttled", all(x["throttled_now"] == "1" for v in hot.values() for x in v),
             "every uncooled trial has throttled_now == 1")
r.number("decode p95 by 25.1\\% to", min(dec.values()), "min decode-p95 reduction, uncooled base")
r.number("to\n41.3\\%", max(dec.values()), "max decode-p95 reduction, uncooled base")
r.number("on the reference surface is 6.5~pp", 100 * (A[(Q, "test_golden")] - A[(D, "test_golden")]),
         "surface_a qwen - danube golden", places=1)
r.number("scores 0.935 against\nH2O-Danube3-500M's", A[(Q, "test_golden")], "surface_a qwen golden")
r.number("H2O-Danube3-500M's 0.870", A[(D, "test_golden")], "surface_a danube golden")
fc = next(x for x in mc if x["family"] == "family control")
r.number("on 15 against 2 discordant", int(fc["only_a"]), "mcnemar family control, only qwen")
r.number("on 15 against 2 discordant", int(fc["only_b"]), "mcnemar family control, only danube", nth=1)
r.number("(exact\n$p = 0.0023$", float(fc["p_exact"]), "mcnemar family control p_exact")

# -- 6.3 next steps -----------------------------------------------------------------------------
import json  # noqa: E402

train = [json.loads(x) for x in (REPO / "data/train.jsonl").read_text().splitlines() if x.strip()]
unk = sum('"unknown"' in json.dumps(x) for x in train)
r.number("through 81 pairs", unk, "rows of data/train.jsonl whose target is unknown")

# -- Conclusion may not add a measurement Ch1-Ch5 did not report ---------------------------------
earlier = {round(n.value, n.places) for c in MASTER[:6] for n in numbers(Chapter.load("master", c))}
for n in numbers(r.ch):
    if significant(n) and round(n.value, n.places) not in earlier:
        r.add("FAIL", "new-number", f"{n.text} appears in no earlier chapter -- the Conclusion may not "
                                    "introduce a figure; report it in Ch4 first", n.line)

# -- Register: unhedged, and nothing the author decisions or Table 3 rule out ---------------------
for m in re.finditer(r"\b(?:may|might|could|perhaps|possibly|likely|suggests?|appears?|seems?)\b", prose):
    r.add("FAIL", "register", f"hedge `{m.group()}` -- Ch6 concludes without hedging", prose.count("\n", 0, m.start()) + 1)
for pat, why in ((r"budget (?:is|was) met|meets the 2\{,\}500|within the 2\{,\}500", "the 2,500 ms budget is missed and re-baselined, never met (STATE.md author decision)"),
                 (r"oversampl", "the corpus already teaches unknown through 81 pairs; name their kind, not their number"),
                 (r"only instance", "known false in limitation_abstention.md; handed to Block A"),
                 (r"acoustic-robustness|Exp-\d", "Table 3: the Master references the acoustic-robustness experiment once, in Ch5"),
                 (r"guarantee", "no unearned absolutes")):
    hits = re.findall(pat, prose)
    r.expect("register", not hits, f"`{pat}` absent -- {why}" if not hits else f"`{pat}` found -- {why}")

r.manual.append("### For the argument agent\n\n- Check each sentence against Ch4's *qualifier*, not only its number: "
                "unhedged means no hedging words, not stronger claims (e.g. the family control stays exploratory, the "
                "quantisation delta is 'not separated from zero', never 'no cost').\n- The zero-shot baseline must not "
                "attribute the gain to the fine-tune or the grammar (Ch5 5.3.1).\n- No new caveat: a limitation that "
                "appears here first belongs in Ch5.")
sys.exit(r.finish())
