#!/usr/bin/env python3
"""Pre-review checks for Master Ch3 (Method). See tools/review/lib.py.

Method is where reproducibility lives, so the checks here compare the chapter against the
artefacts it describes rather than against results: the grammar listing against schema/cmd.gbnf,
the LoRA table against train/configs/*.yaml, the dataset table against data/*.jsonl, and both
requirement tables against prd.md.
"""

import json
from collections import Counter
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (MASTER, REPO, RESULTS, Review, acronyms, md_table, outline_check, prd,  # noqa: E402
                 requirement_table_check)

r = Review("master_ch3", "master", MASTER[2], [*MASTER[:2], *MASTER[3:]])
r.common()
text = r.ch.text

outline_check(r, 2, {"command schema and grammar design": r"schema", "label-first dataset construction": r"dataset",
                     "the LoRA recipe": r"lora", "quantisation procedure": r"quantisation",
                     "evaluation protocol and the definitions of record": r"evaluation protocol"})

# -- Layer 1: the listing IS the frozen grammar -------------------------------------------------
listing = re.findall(r"\\begin\{lstlisting\}[^\n]*\n(.*?)\\end\{lstlisting\}", r.ch.raw, flags=re.S)
gbnf = [l.rstrip() for l in (REPO / "schema/cmd.gbnf").read_text().splitlines() if l.strip() and not l.startswith("#")]
shown = [l.rstrip() for l in (listing[1] if len(listing) > 1 else "").splitlines() if l.strip()]
r.expect("grammar", shown == gbnf, "grammar listing is schema/cmd.gbnf verbatim (comments aside)" if shown == gbnf
         else f"grammar listing differs from schema/cmd.gbnf: {sorted(set(shown) ^ set(gbnf))[:4]}",
         r.ch.find("root      ::= cmd")[0] if r.ch.find("root      ::= cmd") else None)
intents = re.findall(r'\\"intent\\":\\"(\w+)\\"', "\n".join(gbnf))
listed = re.findall(r"\\texttt\{([a-z\\_]+)\}", text[text.find("Ten intents"): text.find("The wire format")])
listed = [i.replace("\\_", "_") for i in listed]
r.text_claim("grammar", "Ten intents cover the vocabulary", sorted(listed) == sorted(intents) and len(intents) == 10,
             f"the ten intents named = the grammar's {len(intents)} intents")
r.text_claim("grammar", "caps the list at five entries", "[0-4] ( \",\" [0-4] ){0,4}" in "\n".join(gbnf),
             "idlist [0-4] with {0,4} repeats = at most five ids in 0..4, N = 5")


def longest(rules: dict[str, str], expr: str) -> int:
    """Length in characters of the longest string `expr` can produce (every rule here is bounded)."""
    toks = re.findall(r'"(?:\\.|[^"\\])*"|\[[^\]]*\]|\{\d+,\d+\}|[()|?]|[\w-]+', expr)
    pos = 0

    def alt() -> int:
        nonlocal pos
        best = seq()
        while pos < len(toks) and toks[pos] == "|":
            pos += 1
            best = max(best, seq())
        return best

    def seq() -> int:
        nonlocal pos
        total = 0
        while pos < len(toks) and toks[pos] not in ("|", ")"):
            t = toks[pos]
            pos += 1
            if t == "(":
                n = alt()
                pos += 1                                   # the closing ")"
            elif t.startswith('"'):
                n = len(re.sub(r"\\(.)", r"\1", t[1:-1]))
            elif t.startswith("["):
                n = 1
            else:
                n = longest(rules, rules[t])
            if pos < len(toks) and toks[pos] == "?":
                pos += 1
            elif pos < len(toks) and toks[pos].startswith("{"):
                n *= int(re.findall(r"\d+", toks[pos])[1])      # {min,max}: at most max repeats
                pos += 1
            total += n
        return total

    return alt()


rules = dict(re.match(r"([\w-]+)\s*::=\s*(.*)", l).groups() for l in gbnf)
cap = int(re.search(r"^MAX_TOKENS = (\d+)", (REPO / "eval/surface_b.py").read_text(), re.M).group(1))
r.number("its longest string is 90 characters", longest(rules, "root"), "longest string of schema/cmd.gbnf")
r.number("so the 96-token cap", cap, "eval/surface_b.py MAX_TOKENS")
r.expect("grammar", longest(rules, "root") < cap, f"longest grammar string {longest(rules, 'root')} chars < "
         f"{cap}-token cap (a token is at least one character)")

wire = {row["Model"]: row for row in md_table(RESULTS / "wire_format_tokens.md", "Model")}["qwen2.5-0.5b-instruct"]
r.number("averages 16.0 tokens under the Qwen2.5 tokeniser", float(wire["Wire format"]), "results/wire_format_tokens.md")
r.number("It would average 19.6 tokens", float(wire["Intent nulls"]), "results/wire_format_tokens.md")
r.number("and 53.3 if every slot", float(wire["Schema nulls"]), "results/wire_format_tokens.md")
saved = {row["Counterfactual"]: row for row in md_table(RESULTS / "wire_format_tokens.md", "Counterfactual")}
r.number("those savings are 0.13~s", float(saved["Intent nulls"]["s at measured tok/s"].split()[0]),
         "results/wire_format_tokens.md")
r.number("and 1.33~s of decode time", float(saved["Schema nulls"]["s at measured tok/s"].split()[0]),
         "results/wire_format_tokens.md")
r.number("At the 27.93~tok/s", float(md_table(RESULTS / "thermal_headroom.md", "Config")[2]["tok/s"]),
         "results/thermal_headroom.md qwen cooled")

for line in re.findall(r"^\{.*\}$", listing[0] if listing else "", flags=re.M):
    ok = all(json.loads(line).get("intent") in intents for _ in [0])
    r.expect("grammar", ok, f"wire-format example has a grammar intent: {line}")

# -- Dataset table against the frozen splits ----------------------------------------------------
count = {s: sum(1 for _ in (REPO / f"data/{f}.jsonl").open()) for s, f in
         (("train_synth", "train"), ("val_synth", "val"), ("test_synth", "test_synth"),
          ("test_golden", "test_golden"), ("test_ood", "test_ood"))}
for split, unit in (("train_synth", "pairs"), ("val_synth", "pairs"), ("test_synth", "pairs"), ("test_ood", "transcripts")):
    r.number(f"\\texttt{{{split.replace('_', chr(92) + '_')}}} & 1{{,}}000 {unit}", count[split], f"data/ rows of {split}")
variants = Counter(json.loads(l).get("variant") for l in (REPO / "data/train.jsonl").open())
asr = {k: v for k, v in variants.items() if k.startswith("asr_")}
r.number("872 rows replace the transcript", sum(asr.values()), f"data/train.jsonl asr_* variants {asr}")
r.number("and 88 carry injected text perturbations", variants["perturb"], "data/train.jsonl perturb variant")
r.number("872 transcripts replaced", sum(asr.values()), "data/train.jsonl asr_* variants")
r.text_claim("dataset", "mixed with noise at 20, 10 or 5~dB", sorted(int(k[4:-2]) for k in asr) == [5, 10, 20],
             f"round-trip SNR levels in data/train.jsonl: {sorted(asr)}")
neg = json.loads((REPO / "data/wake/wake_manifest.json").read_text())["summary"]["neg"]["sources"]
r.number("720 near-miss clips", neg["adversarial"], "data/wake/wake_manifest.json neg sources")
r.text_claim("dataset", "LibriSpeech~\\cite{librispeech}, Speech Commands~\\cite{speechcmd}, 720",
             set(neg) == {"adversarial", "speech_commands", "librispeech"}, f"wake_neg sources = manifest {neg}")
r.number("& 200 audio files", count["test_golden"], "data/test_golden.jsonl rows")
cv = md_table(RESULTS / "table16_asr_speaker_sensitivity.md", "Accent")
buckets = [row for row in cv if not row["Accent bucket"].startswith("Author")]
r.number("300 clips, 263 speakers", sum(int(b["n"]) for b in buckets), "sum of n over table16 buckets")
r.number("15 accent buckets", len(buckets), "table16 bucket rows")
state = (REPO / ".scratch/sprint-pfe/STATE.md").read_text(encoding="utf-8")
r.text_claim("dataset", "3{,}000 clips (1{,}500 per class)", "3,000 positives" in state,
             "wake_pos 3,000 = STATE.md wake-corpus record")
r.text_claim("dataset", "5{,}040 clips, 3.50~h", "5,040 clips = 3.50 h" in state, "wake_neg 5,040 / 3.50 h = STATE.md")
card = (REPO / "data/dataset_card.md").read_text(encoding="utf-8")
r.text_claim("dataset", "39\\% United States English", "39% United States English" in card,
             "39% US English = data/dataset_card.md")

# -- Annotation interval from the seal and the pass-2 timestamps --------------------------------
seal = json.loads((REPO / "data/annot/annot_pass1.seal.json").read_text())
p2 = [json.loads(l)["at"] for l in (REPO / "data/annot/annot_pass2.jsonl").open()]
days = (datetime.fromisoformat(min(p2)) - datetime.fromisoformat(seal["sealed"])).total_seconds() / 86400
r.number("interval of 4.0~days", days, "seal timestamp -> first pass-2 label")
r.number("labelled 50 golden-set utterances", seal["items"], "annot_pass1.seal.json items")
p1 = {json.loads(l)["id"]: json.loads(l)["label"] for l in (REPO / "data/annot/annot_pass1.jsonl").open()}
p2l = {json.loads(l)["id"]: json.loads(l)["label"] for l in (REPO / "data/annot/annot_pass2.jsonl").open()}
r.text_claim("claim", "that count is zero", sum(p1[k] != p2l.get(k) for k in p1) == 0,
             f"disagreements between passes: {sum(p1[k] != p2l.get(k) for k in p1)}")
r.expect("dataset-card", "two-day interval" not in card,
         "data/dataset_card.md still says 'with a two-day interval' next to its own 4.0-day table -- the card "
         "is C2's published artefact, fix it with the chapter", warn=True)

# -- LoRA table against every training config ---------------------------------------------------
cfgs = {p.stem: p.read_text() for p in (REPO / "train/configs").glob("*.yaml")}
for anchor, key, want in (("$r = 16$", "r", "16"), ("$\\alpha = 32$", "alpha", "32"), ("dropout $0.05$", "dropout", "0.05"),
                          ("learning rate $2\\times10^{-4}$", "learning_rate", "2.0e-4"), ("3 epochs", "epochs", "3"),
                          ("per-device 4", "per_device_train_batch_size", "4"),
                          ("gradient accumulation 4", "gradient_accumulation_steps", "4"),
                          ("256 tokens", "max_seq_length", "256"), ("warmup ratio $0.03$", "warmup_ratio", "0.03"),
                          ("42, identical for all four runs", "seed", "42")):
    vals = {n: (re.search(rf"^\s+{key}:\s*([^\s#]+)", c, flags=re.M) or [None, None])[1] for n, c in cfgs.items()}
    r.text_claim("lora", anchor, set(vals.values()) == {want}, f"{key} = {want} in all {len(cfgs)} configs: {vals}")
r.text_claim("lora", "Precision & fp16", all("precision: fp16" in c for c in cfgs.values()), "precision fp16 in every config")
r.text_claim("lora", "\\texttt{q\\_proj}, \\texttt{k\\_proj}",
             all("[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]" in c for c in cfgs.values()),
             "target modules identical in every config")
params = {row["Model"].strip("`"): float(row["Params"].replace(",", "").split()[0])
          for row in md_table(RESULTS / "table33_iso_parameter.md", "Model")}
q, d = params["qwen2.5-0.5b-instruct"], params["h2o-danube3-500m-chat"]
r.number("514~M parameters", d, "table33 danube params (M)")
r.number("against 494~M", q, "table33 qwen params (M)")
r.number("a difference of 4.0\\%", 100 * (d / q - 1), "514 / 494 - 1")

# -- Quantisation procedure and parity gate -----------------------------------------------------
prompts = json.loads((REPO / "eval/fixed_audit_prompts.json").read_text())["prompts"]
r.text_claim("parity", "ten fixed audit prompts", len(prompts) == 10, f"eval/fixed_audit_prompts.json holds {len(prompts)} prompts")
gate = (RESULTS / "gate3_parity.md").read_text(encoding="utf-8")
r.text_claim("parity", "\\texttt{dro}~+~\\texttt{ne}", "' dro' + 'ne'" in gate, "dro+ne segmentation = results/gate3_parity.md")
quantised = sorted(p.name for p in (REPO / "gguf").glob("*-Q[48]_*.gguf"))
r.text_claim("parity", "producing six deployable artefacts", len(quantised) == 6, f"gguf/ holds {len(quantised)}: {quantised}")

# -- Protocol n's ------------------------------------------------------------------------------
r.text_claim("protocol", "configuration over 60 repetitions on the board and did not time Q8\\_0",
             "Exp-1 executed at 60 reps/Q4_K_M-only" in state, "Exp-1 60 reps = STATE.md")
r.text_claim("protocol", "used 60 trials per path", "Exp-2 200 -> 60 trials/branch" in state, "Exp-2 60/branch = STATE.md")
# The pinning command as the harness launches it: `taskset -c CORES llama-server ... -t THREADS`. The
# `-t` belongs to llama-server, so a \texttt{taskset ...} in the prose may carry only the `-c` list.
harness = (REPO / "eval/exp1.py").read_text()
cores = re.search(r'^CORES = "([^"]+)"', harness, re.M).group(1)
threads = re.search(r"^THREADS = (\d+)", harness, re.M).group(1)
pin = re.search(r"\\texttt\{(taskset[^}]*)\}", text)
cmd = pin.group(1) if pin else ""
r.text_claim("protocol", "\\texttt{taskset", set(re.findall(r"\s(-\w+)", cmd)) == {"-c"} and f"-c {cores}" in cmd,
             f"prose `{cmd}` vs harness `taskset -c {cores}` around llama-server `-t {threads}` (eval/exp1.py)")

# -- The token-count latency claim (§3.1) -------------------------------------------------------

# -- Requirement and budget tables against prd.md ----------------------------------------------
# Issue 00: the Master names its criteria instead of printing requirement IDs; the prd row each
# name stands for, and the experiment codes behind the experiment names, are fixed here.
CRITERIA = {"End-to-end latency": "NFR-2", "Exact-match threshold": "NFR-4", "Intent F1": "NFR-5", "Schema validity": "NFR-6",
            "Clean-audio recognition": "NFR-7", "Recognition in noise": "NFR-8", "Safe failure": "NFR-9",
            "Memory ceiling": "NFR-9a", "Memory per configuration": "NFR-9b", "Throttling": "NFR-10",
            "Speaker sensitivity": "NFR-11", "False commands": "NFR-18"}
EXPERIMENTS = {"speaker-sensitivity experiment": "Exp-0", "multi-model benchmark": "Exp-1",
               "latency experiment": "Exp-2", "acoustic-robustness experiment": "Exp-3",
               "formation-control experiment": "Exp-4"}
requirement_table_check(r, "tab:requirements", target_col=2, source_col=3, row_ids=CRITERIA, source_names=EXPERIMENTS)
t6 = re.search(r"### Table 6:.*?\n\n(.*?)\n\n", prd(), flags=re.S)
if t6:
    for stage, ms in re.findall(r"^(.*?) & ([\d{},]+)~ms \\\\", text[text.find("tab:latency-budget"):], flags=re.M):
        v = ms.replace("{,}", ",")
        r.expect("budget", v in t6.group(1), f"latency budget `{stage.strip()}` {v} ms appears in prd Table 6", warn=True)
lm = [int(x.replace("{,}", "")) for x in re.findall(r"Language-model (?:prefill|decode)[^&]*& ([\d{},]+)~ms", text)]
r.number("Language-model stages combined & 1{,}350~ms", sum(lm), "prefill + decode rows")

acr = acronyms()
fa = acr.get("fa", ("", ""))[1]
r.expect("acronym", not re.search(r"\(FA\)|\bFA\s*\$", text) or not fa.lower().startswith("false"),
         f"`FA` is not used for formation accuracy (shared/acronyms.tex defines \\gls{{fa}} as `{fa}`)")

r.manual.append("### For the reproducibility agent\n\n- Could an outsider rerun Method from this chapter alone? "
                "Check each named script exists and is the one that ran (the path checks above only prove existence).\n"
                "- Two surfaces: the reference-minus-deployed difference is what C3's harness measures (Ch1 defines C3 "
                "as the harness) -- judge whether the chapter conflates the contribution with its measurement.\n"
                "- tab:metrics and tab:requirements are written once here and cited everywhere: every later metric "
                "must appear in them (the Ch4/Ch5 scripts do not check this).")
sys.exit(r.finish())
