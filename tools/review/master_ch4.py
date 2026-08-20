#!/usr/bin/env python3
"""Pre-review checks for Master Ch4 (Results). See tools/review/lib.py.

Every number in the prose is recomputed here from the files the chapter says it comes from,
not read back from the generated tables -- the tables are eval/tables.py's output, and a check
that compares prose to a table cannot catch a table that is itself wrong. Latency percentiles are
recomputed from the per-trial rows of results/exp1_cooled.csv with the project's own nearest-rank
definition (eval/stats.py), because the Markdown summaries round to one decimal and a prose
figure of "785 ms" cannot be judged against "785.5".

Needs the pfe_swarm env (eval.stats imports numpy and scipy).
"""

import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (MASTER, REPO, RESULTS, Review, csv_rows, md_table, outline_check)  # noqa: E402
from eval.stats import EXACT_BELOW_DISCORDANT, nearest_rank  # noqa: E402

r = Review("master_ch4", "master", MASTER[3], [*MASTER[:3], *MASTER[4:]])
r.common()
text = r.ch.text


def half_up(x: float, places: int = 0) -> float:
    """Thesis rounding: 785.5 -> 786. Python's round() is half-to-even and would hide a truncation."""
    return float(Decimal(repr(x)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


outline_check(r, 3, {"Exp-0": r"speaker sensitivity|acoustic", "Exp-1": r"multi-model|benchmark",
                     "quantisation delta": r"quantisation delta", "grammar ablation": r"grammar ablation",
                     "statistical analysis": r"statistic", "the selection rule applied": r"selection rule"})
for stem in re.findall(r"\\input\{generated/(\w+)\}", text):
    r.expect("generated", stem in (REPO / "eval/tables.py").read_text() and (REPO / f"thesis/generated/{stem}.tex").is_file(),
             f"generated/{stem}.tex exists and is written by eval/tables.py (l.18 claims no cell is hand-typed)")

# ---------------------------------------------------------------------------------------------
# Sources
B = {(x["model"], x["quant"], x["split"]): x for x in csv_rows(RESULTS / "surface_b.csv")}
B_off = {(x["model"], x["quant"], x["split"]): x for x in csv_rows(RESULTS / "surface_b_nogrammar.csv")}
A = {(x["model"], x["split"]): float(x["exact_match"]) for x in csv_rows(REPO / "train/kaggle_out/surface_a.csv")
     if x["surface"] == "A_fp16_finetuned"}
A0 = [x for x in csv_rows(REPO / "train/kaggle_out/surface_a.csv") if x["surface"] == "A_fp16_zeroshot"]
Q, L, S, D = "qwen2.5-0.5b-instruct", "llama-3.2-1b-instruct", "smollm2-360m-instruct", "h2o-danube3-500m-chat"
em = lambda m, q="Q4_K_M", s="test_golden": float(B[(m, q, s)]["exact_match"])  # noqa: E731
params = {x["Model"].strip("`"): float(x["Params"].replace(",", "").split()[0])
          for x in md_table(RESULTS / "table33_iso_parameter.md", "Model")}


def trials(path: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for x in csv_rows(path):
        if not x["config"].endswith("-warmup"):
            out.setdefault(x["config"].removesuffix("-Q4_K_M"), []).append(x)
    return out


cool, hot = trials(RESULTS / "exp1_cooled.csv"), trials(RESULTS / "exp1.csv")


def p(rows: list[dict], col: str, pct: float = 95) -> float:
    return nearest_rank([float(x[col]) for x in rows if x[col]], pct)


def tps(rows: list[dict]) -> float:
    return sum(int(x["tokens_predicted"]) for x in rows) / sum(float(x["slm_decode_ms"]) / 1000 for x in rows)


rss = {m: max(float(x["peak_rss_mb"]) for x in rows) / 1024 for m, rows in cool.items()}

# ---------------------------------------------------------------------------------------------
# §4.1 Exp-0
cv = md_table(RESULTS / "table16_asr_speaker_sensitivity.md", "Accent")
author = next(x for x in cv if x["Accent bucket"].startswith("Author"))
buckets = {x["Accent bucket"]: x for x in cv if x is not author}
aw = float(author["WER %"])
r.number("300 validated Common Voice", sum(int(b["n"]) for b in buckets.values()), "sum of table16 bucket n")
r.number("author's 200 recorded", int(author["n"]), "table16 author n")
r.number("is 23.1\\% with", aw, "table16 author WER")
r.number("interval of [20.3, 25.9]", float(author["95% CI"].strip("[]").split(",")[0]), "table16 author CI low")
above = sum(float(b["WER %"]) > aw for b in buckets.values())
r.number("below 7 of the 15 accent", above, "buckets with WER above the author's")
r.number("the 53rd percentile", 100 * (len(buckets) - above) / len(buckets), "buckets below the author / 15")
nz, hk = float(buckets["New Zealand English"]["WER %"]), float(buckets["Hong Kong English"]["WER %"])
r.number("transcribed at 6.2\\%", nz, "table16 New Zealand")
r.number("English at 49.5\\%", hk, "table16 Hong Kong")
r.text_claim("claim", "an eightfold range", round(hk / nz) == 8, f"49.5 / 6.2 = {hk / nz:.2f}")
india = next(b for k, b in buckets.items() if k.startswith("India"))
r.number("South Asia, 80 utterances", int(india["n"]), "table16 India n")
r.text_claim("claim", "largest bucket in the sample", int(india["n"]) == max(int(b["n"]) for b in buckets.values()),
             "India and South Asia is the largest bucket")
r.number("sits at 27.9\\%", float(india["WER %"]), "table16 India WER")
r.number("Seven of the fifteen buckets carry fewer than 10", sum(int(b["n"]) < 10 for b in buckets.values()),
         "buckets with n < 10")
t16 = (RESULTS / "table16_asr_speaker_sensitivity.md").read_text()
cvp = re.search(r"Common Voice: ([\d.]+) % -> ([\d.]+) %", t16)
aup = re.search(r"author's commands: ([\d.]+) % -> ([\d.]+) %", t16)
r.number("from 22.4\\% to", float(cvp[1]), "table16 note, Common Voice unprompted")
r.number("to 22.9\\% (+0.5~pp)", float(cvp[2]), "table16 note, Common Voice prompted")
r.number("from 23.1\\% to 23.0\\%", float(aup[1]), "table16 note, author unprompted")
r.number("to 23.0\\% ($-$0.1~pp)", float(aup[2]), "table16 note, author prompted")

# §4.2 Exp-1 accuracy
r.number("reaches\n0.935 exact match", em(Q), "surface_b qwen Q4 golden")
r.number("reaches 0.910, and", em(L), "surface_b llama Q4 golden")
r.number("reaches 0.760. The ordering", em(S), "surface_b smollm2 Q4 golden")
r.number("1.24~B model", params[L] / 1000, "table33 llama params")
r.number("the 0.49~B model", params[Q] / 1000, "table33 qwen params")
r.number("0.49~B model by 2.5~pp", 100 * (em(Q) - em(L)), "qwen - llama, Q4 golden", places=1, nth=1)
golden_f1 = [100 * float(x["intent_macro_f1"]) for k, x in B.items() if k[2] == "test_golden"]
r.text_claim("claim", "above 95 for\nevery configuration", min(golden_f1) > 95, f"min golden intent F1 = {min(golden_f1):.1f}")
r.text_claim("claim", "reaches 100.0 for Qwen2.5-0.5B",
             half_up(100 * float(B[(Q, "Q4_K_M", "test_golden")]["intent_macro_f1"]), 1) == 100.0,
             f"qwen Q4 golden intent F1 = {100 * float(B[(Q, 'Q4_K_M', 'test_golden')]['intent_macro_f1']):.2f} "
             f"(Q8_0: {100 * float(B[(Q, 'Q8_0', 'test_golden')]['intent_macro_f1']):.2f}) -- the sentence names no quant level")
r.text_claim("claim", "eighteen rows reports 100.0\\% schema validity",
             len(B) == 18 and all(float(x["schema_validity"]) == 1.0 for x in B.values()),
             f"{len(B)} Surface-B rows, all schema_validity == 1.0")
r.number("split's 150 references", int(B[(Q, "Q4_K_M", "test_ood")]["n"]), "surface_b test_ood n")

# §4.2 thermal
thr = sum(x["throttled_now"] == "1" for rows in hot.values() for x in rows)
r.number("throttled on all 180", sum(len(v) for v in hot.values()), "scored trials in results/exp1.csv")
r.text_claim("claim", "throttled on all 180", thr == sum(len(v) for v in hot.values()), f"{thr} of them throttled_now == 1")
r.number("moves from 100\\% of trials", 100 * thr / sum(len(v) for v in hot.values()), "uncooled throttled fraction")
r.number("budget, to 0\\%", 100 * sum(x["throttled_now"] == "1" for v in cool.values() for x in v), "cooled throttled trials")
dec = {m: 100 * (1 - p(cool[m], "slm_decode_ms") / p(hot[m], "slm_decode_ms")) for m in cool}
tp = {m: 100 * (tps(cool[m]) / tps(hot[m]) - 1) for m in cool}
r.number("was 25.1\\% to", min(dec.values()), "min decode-p95 reduction")
r.number("to 41.3\\% of decode p95", max(dec.values()), "max decode-p95 reduction")
r.number("35.2\\% to 68.5\\%", min(tp.values()), "min throughput gain")
r.number("to 68.5\\% of throughput", max(tp.values()), "max throughput gain")
r.text_claim("claim", "largest on the\nsmallest model", max(tp, key=tp.get) == S and max(dec, key=dec.get) == S,
             f"largest effect on {max(tp, key=tp.get)}")
r.number("a 1.6$\\times$ clock ratio", 2.4 / 1.5, "2.4 / 1.5 GHz", places=1)
r.number("throughput gain of 1.69$\\times$", tps(cool[S]) / tps(hot[S]), "smollm2 cooled / uncooled tok/s")
r.text_claim("claim", "at a 1.5~GHz cap", "1.5 GHz" in (RESULTS / "thermal_headroom.md").read_text(), "1.5 GHz = thermal_headroom.md")

# §4.2 latency, throughput, memory (cooled)
for m, tok_anchor, tot_anchor in ((Q, "decodes at\n27.93~tok/s", "p95 of 1{,}072~ms"), (S, "at 40.63~tok/s", "40.63~tok/s and\n894~ms"),
                                  (L, "at 14.53~tok/s", "14.53~tok/s and 2{,}282~ms")):
    r.number(tok_anchor, tps(cool[m]), f"{m} tokens / decode-seconds, exp1_cooled")
    r.number(tot_anchor, p(cool[m], "total_ms"), f"{m} total p95", nth=0 if m == Q else 1)
for m, anchor in ((Q, "Qwen2.5-0.5B (1{,}033~ms)"), (S, "SmolLM2-360M (785~ms)"), (L, "Llama-3.2-1B (1{,}842~ms)")):
    v = p(cool[m], "slm_decode_ms")
    r.number(anchor, v, f"{m} decode p95 = {v:.2f}")
r.number("misses it by 67\\%", 100 * (p(cool[L], "slm_decode_ms") / 1100 - 1), "llama decode p95 / 1100 - 1")
for m, anchor in ((Q, "is 0.68~GB"), (S, "0.55~GB and 1.63~GB"), (L, "and 1.63~GB respectively")):
    r.number(anchor if m != S else "0.55~GB and", rss[m], f"{m} peak RSS MiB/1024")
r.add("WARN", "units", f"'GB' is MiB/1024 (GiB): llama peak RSS {max(float(x['peak_rss_mb']) for x in cool[L]):.0f} MB "
      f"= {max(float(x['peak_rss_mb']) for x in cool[L]) / 1000:.2f} GB decimal. State the unit once, or write GiB",
      r.ch.find("is 0.68~GB")[0] if r.ch.find("is 0.68~GB") else None)
r.number("nearest approach being 35\\% clear", 100 * (1 - rss[L] / 2.5), "1 - 1.63 / 2.5")
r.number("prefill p50 of 38.5~ms", p(cool[Q], "slm_prefill_ms", 50), "qwen prefill p50")
r.number("p95 of 328.8~ms", p(cool[Q], "slm_prefill_ms"), "qwen prefill p95")
r.number("only 8 of its 60 trials", sum(float(x["slm_prefill_ms"]) > 250 for x in cool[Q]), "qwen trials > 250 ms")
r.number("a p50 of 267.7~ms", p(cool[L], "slm_prefill_ms", 50), "llama prefill p50")
r.number("and 34 of 60 trials do", sum(float(x["slm_prefill_ms"]) > 250 for x in cool[L]), "llama trials > 250 ms")
r.number("with 278~ms to spare", 1350 - p(cool[Q], "total_ms"), "1350 - qwen total p95")

# §4.2 abstention
ab = csv_rows(RESULTS / "nfr9_nfr18_abstention.csv")
sfr = [float(x["safe_failure_rate"]) for x in ab]
pooled = sum(int(x["safe_failures"]) for x in ab) / sum(int(x["errors"]) for x in ab)
fcr = [float(x["false_command_rate"]) for x in ab if x["false_command_rate"]]
r.number("between 0.0000 and 0.1579", min(sfr), "min safe-failure rate over 18 rows")
r.number("and 0.1579, pooling", max(sfr), "max safe-failure rate")
r.number("pooling to 0.0530", pooled, "sum safe_failures / sum errors")
r.number("over\n528 errors", sum(int(x["errors"]) for x in ab), "sum errors, nfr9_nfr18_abstention.csv")
r.number("between 0.1867 and 0.3933", min(fcr), "min false-command rate (test_ood rows)")
r.number("and 0.3933. Neither", max(fcr), "max false-command rate")
r.text_claim("claim", "roughly a factor of thirteen", round(0.70 / pooled) == 13, f"0.70 / {pooled:.4f} = {0.70 / pooled:.1f}")
r.text_claim("claim", "a factor of four to eight", (round(min(fcr) / 0.05), round(max(fcr) / 0.05)) == (4, 8),
             f"{min(fcr) / 0.05:.2f} to {max(fcr) / 0.05:.2f}")

# §4.3 iso-parameter (Surface A)
r.number("at 514~M parameters", params[D], "table33")
r.number("within 4.0\\% of", 100 * (params[D] / params[Q] - 1), "514 / 494 - 1")
fam, size = 100 * (A[(Q, "test_golden")] - A[(D, "test_golden")]), 100 * (A[(L, "test_golden")] - A[(S, "test_golden")])
r.number("is 6.5~pp, with", fam, "surface_a qwen - danube, golden", places=1)
r.number("Qwen2.5-0.5B at 0.9350", A[(Q, "test_golden")], "surface_a")
r.number("H2O-Danube3-500M at 0.8700", A[(D, "test_golden")], "surface_a")
r.number("is 15.0~pp, from", size, "surface_a llama - smollm2, golden", places=1)
r.number("SmolLM2-360M at 0.7750", A[(S, "test_golden")], "surface_a")
r.number("Llama-3.2-1B at 0.9250", A[(L, "test_golden")], "surface_a")
r.number("full 3.4$\\times$ span", params[L] / params[S], "1236 / 362")
r.text_claim("claim", "two-fifths of what", 0.35 <= fam / size <= 0.45, f"6.5 / 15.0 = {fam / size:.3f}")
r.number("with 40\\% of its parameters", 100 * params[Q] / params[L], "494 / 1236")
r.number("on all ten audit prompts", 10, "eval/fixed_audit_prompts.json (Ch3 script counts it)")
r.text_claim("claim", "score an exact match of 0.000 on every split", all(float(x["exact_match"]) == 0 for x in A0)
             and len({x["model"] for x in A0}) == 4, f"{len(A0)} zero-shot rows, all EM 0, {len({x['model'] for x in A0})} models")
r.number("not one of the\n590 items", sum(int(x["n"]) for x in A0 if x["model"] == Q), "240 + 200 + 150", nth=1)

# §4.4 quantisation delta (table18 from surface A and B)
deltas = {(m, q): 100 * (em(m, q) - A[(m, "test_golden")]) for m in (Q, L, S) for q in ("Q4_K_M", "Q8_0")}
r.number("span $-$1.5~pp", -min(deltas.values()), "min delta, negated", places=1)
r.number("to $+$1.5~pp", max(deltas.values()), "max delta", places=1)
for (m, q), anchor in (((L, "Q4_K_M"), "Llama-3.2-1B loses 1.5~pp"), ((L, "Q8_0"), "and 1.0~pp at Q8\\_0;"),
                       ((Q, "Q8_0"), "and 0.5~pp at Q8\\_0;"), ((S, "Q4_K_M"), "SmolLM2-360M loses 1.5~pp"),
                       ((S, "Q8_0"), "\\emph{gains} 1.5~pp")):
    r.number(anchor, abs(deltas[(m, q)]), f"{m} {q} B - A", places=1)
r.text_claim("claim", "loses nothing at Q4\\_K\\_M", abs(deltas[(Q, "Q4_K_M")]) < 1e-9, f"qwen Q4 delta {deltas[(Q, 'Q4_K_M')]:.2f}")
r.number("1.5~pp difference is\nthree items", 0.015 * 200, "0.015 x 200", nth=1)

# §4.5 grammar ablation
n_all = sum(int(x["n"]) for x in B.values())
hits_on = sum(float(x["exact_match"]) * int(x["n"]) for x in B.values())
hits_off = sum(float(x["exact_match"]) * int(x["n"]) for x in B_off.values())
valid_off = sum(float(x["schema_validity"]) * int(x["n"]) for x in B_off.values())
r.number("Pooled over 3{,}540 decodes", n_all, "sum of n, surface_b")
r.number("to 0.9997 and", valid_off / n_all, "pooled schema validity, grammar off")
r.number("exactly one output", round(n_all - valid_off), "invalid decodes, grammar off")
r.number("moves from 0.8508", hits_on / n_all, "pooled EM grammar on")
r.number("to 0.8492, a difference", hits_off / n_all, "pooled EM grammar off")
r.number("a difference of 0.17~pp", 100 * (hits_on - hits_off) / n_all, "pooled EM difference", places=2)
r.number("or six decodes in 3{,}540", round(hits_on - hits_off), "item-count difference")
r.number("same 590 items", n_all / 6, "3540 / 6 artefacts")

# §4.6 statistics
mc = csv_rows(RESULTS / "mcnemar.csv")
row = lambda fam_, a, b, split="test_golden", role="primary": next(  # noqa: E731
    x for x in mc if x["family"] == fam_ and x["role"] == role and x["split"] == split and a in x["system_a"] and b in x["system_b"])
r.number("gives $\\alpha = 0.0167$", 0.05 / 3, "0.05 / 3")
r.number("below 25 discordant", EXACT_BELOW_DISCORDANT, "eval/stats.py EXACT_BELOW_DISCORDANT")
r.text_claim("claim", "the verdict agrees under either test for every row",
             all((float(x["p_exact"]) < float(x["alpha"])) == (float(x["p_chi2"]) < float(x["alpha"])) for x in mc),
             f"exact and chi-square verdicts agree on all {len(mc)} mcnemar.csv rows")
lq = row("model", L, Q)
r.number("on 5 items out of 200", int(lq["discordant"]), "mcnemar llama-qwen discordant")
r.text_claim("claim", "splitting them 5--0", (int(lq["only_b"]), int(lq["only_a"])) == (5, 0), f"only_qwen {lq['only_b']}, only_llama {lq['only_a']}")
r.number("exact $p = 0.0625$", float(lq["p_exact"]), "mcnemar llama-qwen p_exact")
ls_, qs = row("model", L, S), row("model", Q, S)
r.number("$p = 2.5 \\times 10^{-6}$", float(ls_["p_value"]) * 1e6, "llama-smollm2 p x 1e6")
r.number("$p = 1.1 \\times 10^{-7}$", float(qs["p_value"]) * 1e7, "qwen-smollm2 p x 1e7")
r.number("on 38 and 41 discordant", int(ls_["discordant"]), "llama-smollm2 discordant")
r.number("and 41 discordant", int(qs["discordant"]), "qwen-smollm2 discordant")
r.number("the 17.5~pp gap", 100 * (em(Q) - em(S)), "qwen - smollm2", places=1)
for m in (L, Q):
    x = row("quantisation", m, m)
    r.expect("claim", int(x["discordant"]) == 1 and float(x["p_value"]) == 1.0,
             f"{m} Q4 vs Q8 golden: discordant {x['discordant']}, p {x['p_value']} (text: single item, p = 1)",
             r.ch.find("pairs each disagree on a single item")[0] if r.ch.find("pairs each disagree on a single item") else None)
sq = row("quantisation", S, S)
r.number("on 22 and returns", int(sq["discordant"]), "smollm2 Q4 vs Q8 golden discordant")
r.number("$p = 0.286$", float(sq["p_value"]), "smollm2 Q4 vs Q8 golden p")
r.text_claim("claim", "No quantisation comparison reaches significance",
             all(x["significant"] == "no" for x in mc if x["family"] == "quantisation"), "every quantisation row: significant = no")
ss = row("quantisation", S, S, "test_synth", "secondary")
r.number("scores 0.8125 at both", float(ss["em_a"]), "smollm2 synth Q4 EM")
r.text_claim("claim", "scores 0.8125 at both", ss["em_a"] == ss["em_b"], f"Q4 {ss['em_a']} = Q8 {ss['em_b']}")
r.number("disagree on 24 items", int(ss["discordant"]), "smollm2 synth discordant")
r.text_claim("claim", "split them 12--12", (ss["only_a"], ss["only_b"]) == ("12", "12"), f"{ss['only_a']}--{ss['only_b']}")

# §4.7 selection rule
r.number("0.55~GB to 1.63~GB against", rss[S], "min peak RSS")
r.number("leaves 218~ms", 2500 - p(cool[L], "total_ms"), "2500 - llama total p95")
r.number("misses NFR-4 by 9~pp", 100 * (0.85 - em(S)), "0.85 - smollm2 EM")
meets = {m: em(m) >= 0.85 and p(cool[m], "slm_decode_ms") <= 1100 and p(cool[m], "total_ms") <= 1350
         and tps(cool[m]) >= 20 and rss[m] <= 2.5 and not any(x["throttled_now"] == "1" for x in cool[m]) for m in cool}
r.text_claim("claim", "only one of the\nthree meeting", sum(meets.values()) == 1 and meets[Q], f"configs meeting all six: {meets}")
r.text_claim("claim", "SmolLM2-360M\nis faster on every timing measure",
             all(p(cool[S], c) < p(cool[Q], c) for c in ("slm_decode_ms", "slm_prefill_ms", "total_ms")) and tps(cool[S]) > tps(cool[Q]),
             "smollm2 beats qwen on decode p95, prefill p95, total p95 and tok/s")
r.text_claim("claim", "dominated on both axes", em(L) < em(Q) and p(cool[L], "total_ms") > p(cool[Q], "total_ms"),
             "llama: lower EM and higher total p95 than qwen")
r.text_claim("claim", "$n = 60$ timed runs per", all(len(v) == 60 for v in cool.values()), f"cooled n per config: {[len(v) for v in cool.values()]}")

r.manual.append("### For the argument agent\n\n- l.14: 'every accuracy figure ... is an upper bound' -- judge whether "
                "'upper bound' is earned (reference text vs audio) or should be 'ceiling under reference input'.\n"
                "- l.261 and the two cautions (l.277-286): the register is Results; flag any sentence that "
                "interprets rather than reports (that belongs to Ch5).\n- §4.3's 'two-fifths' and §4.2's "
                "'predominantly parameter errors' are interpretations with no computed figure behind them in the "
                "text -- ask for the number or soften the claim.")
sys.exit(r.finish())
