#!/usr/bin/env python3
"""Pre-review checks for Master Ch1 (Introduction). See tools/review/lib.py."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (MASTER, REPO, RESULTS, Review, csv_rows, main_order, md_table, outline_check,  # noqa: E402
                 prd, rq_check)

r = Review("master_ch1", "master", MASTER[0], MASTER[1:])
r.common()

# -- Structure: prd.md §3.1 item 1, and the outline paragraph against main_master.tex ----------
outline_check(r, 0, {"the edge-inference problem": r"edge-inference",
                     "why structured output matters for robot control": r"structured output",
                     "objectives": r"objective", "contributions": r"contribution"})
r.expect("label", "\\label{chap:introduction}" in r.ch.text,
         "Ch1 carries \\label{chap:introduction} (every other Master chapter has its chap: label)", warn=True)
refs = re.findall(r"Chapter~\\ref\{(chap:[^}]*)\}", r.ch.text[r.ch.text.find("Structure of this document"):])
want = ["chap:related-work", "chap:method", "chap:results", "chap:discussion", "chap:conclusion"]
r.expect("outline", list(dict.fromkeys(refs)) == want,
         f"structure paragraph visits chapters in main_master.tex order: {list(dict.fromkeys(refs))}")
r.text_claim("outline", "has five chapters", len(main_order("master")) - 1 == 5,
             f"'five chapters' = {len(main_order('master')) - 1} chapters after this one in main_master.tex")

# -- RQ1 and contributions verbatim against prd.md §2 ------------------------------------------
rq_check(r, 1)
for c in ("C1", "C2", "C3"):
    r.expect("contribution", f"\\textbf{{{c}.}}" in r.ch.text, f"{c} listed")
r.expect("contribution", "\\textbf{C4.}" not in r.ch.text, "C4 not claimed here (owned by the Ingénieur, Table 3)")
cols = set(csv_rows(RESULTS / "surface_b.csv")[0])
for metric, col in (("\\gls{em}", "exact_match"), ("intent and slot F1", "slot_micro_f1"),
                    ("schema validity", "schema_validity"), ("false-command rate", "false_command_rate")):
    r.text_claim("contribution", metric, col in cols,
                 f"C3 metric `{metric}` is a column the harness reports (results/surface_b.csv:{col})")

# -- The throughput paragraph (§1.1): every number against results/thermal_headroom.md ----------
# The table writes "qwen2.5-0.5b-instruct Q4_K_M" since the Ch4 review (it wrote the artefact stem
# "qwen2.5-0.5b-instruct-Q4_K_M"); keyed on the stem either way.
th = {(row["Config"].replace(" ", "-"), row["Run"]): row
      for row in md_table(RESULTS / "thermal_headroom.md", "Config")}
qc = float(th[("qwen2.5-0.5b-instruct-Q4_K_M", "cooled")]["tok/s"])
qu = float(th[("qwen2.5-0.5b-instruct-Q4_K_M", "uncooled")]["tok/s"])
lc = float(th[("llama-3.2-1b-instruct-Q4_K_M", "cooled")]["tok/s"])
budget = re.search(r"Language-model decode & ([\d{},]+)~ms", (r.ch.path.parent / "ch3_method.tex").read_text())
decode_ms = float(budget.group(1).replace("{,}", "")) if budget else 1100.0
r.number("within 1{,}100~ms", decode_ms, "Ch3 tab:latency-budget, decode row")
r.number("at least 20~tokens per second", 22 / (decode_ms / 1000), "22 tokens / 1.100 s")
r.number("at 27.93~tok/s", qc, "results/thermal_headroom.md qwen cooled")
r.number("at 14.53~tok/s", lc, "results/thermal_headroom.md llama cooled")
r.number("decodes at 18.13~tok/s", qu, "results/thermal_headroom.md qwen uncooled")
r.number("clears by 40\\%", 100 * (qc / 20 - 1), "27.93 / 20 - 1")
ch3 = (r.ch.path.parent / "ch3_method.tex").read_text()
cores = re.search(r'^CORES = "([^"]+)"', (REPO / "eval/exp1.py").read_text(), re.M).group(1)
r.text_claim("claim", "the three cores the deployed configuration reserves for speech recognition and language-model "
             "inference", f"three cores reserved for inference (\\texttt{{taskset -c {cores}}}" in ch3,
             f"'three cores reserved for speech recognition and inference' matches Ch3's throughput definition "
             f"(taskset -c {cores} in eval/exp1.py; core 0 carries capture, VAD and the keyword spotter)")
r.number("against the 20~tok/s floor", 22 / (decode_ms / 1000), "22 tokens / 1.100 s (closing paragraph)")
ch2 = (r.ch.path.parent / "ch2_related_work.tex").read_text()
r.text_claim("coherence", "three deployment candidates", "four fine-tuned models" in ch2 and "a fourth" in r.ch.text,
             "Ch1 names three deployment candidates plus a fourth control model; Ch2 says 'four fine-tuned models'")

# -- RQ1's parameter range against the model metadata -------------------------------------------
params = {row["Model"].strip("`"): float(row["Params"].replace(",", "").split()[0])
          for row in md_table(RESULTS / "table33_iso_parameter.md", "Model")}
r.number("0.36--1.2~B", min(params.values()) / 1000, "results/table33_iso_parameter.md smallest model, B")
r.expect("claim", round(max(params.values()) / 1000, 1) == 1.2,
         f"RQ1 upper bound 1.2 B vs largest model {max(params.values()) / 1000:.3f} B (1.24 rounds to 1.2)")

# -- Spike S3 narrative against its report ------------------------------------------------------
s3 = (Path(__file__).resolve().parents[2] / "spikes" / "reports" / "S3_gbnf_smoke.md").read_text(encoding="utf-8").lower()
for anchor, needle in (("swarm takeoff", "takeoff"), ("swarm land", "land"), ("emergency-abort", "abort"),
                       ("truncated", "trunc"), ("48-token cap", "-n 48"), ("Q4\\_K\\_M,", "q4_k_m")):
    r.text_claim("spike-S3", anchor, needle in s3, f"S3 report mentions `{needle}` (the Ch1 story about `{anchor}`)")
gbnf = (Path(__file__).resolve().parents[2] / "schema" / "cmd.gbnf").read_text(encoding="utf-8")
r.text_claim("claim", "bounds\nthe identifier list at five entries", '( "," [0-4] ){0,4}' in gbnf,
             "schema/cmd.gbnf idlist: one id plus at most four more = five entries")
r.manual.append("### For the argument agent\n\n- Ch1 promises (collect every 'Chapter X reports/sets out ...'): "
                "check each against the chapter it names.\n- Preliminary-run story (l.53-71): read "
                "spikes/reports/S3_gbnf_smoke.md in full; the script only confirms the words occur.")
sys.exit(r.finish())
