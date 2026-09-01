#!/usr/bin/env python3
"""Render Tables 17 and 18 from the measured CSVs. No number is typed by hand.

Table 17 (model comparison, RQ1) and Table 18 (the quantisation delta, contribution C3)
are joins of two files that were produced on two different machines:

  train/kaggle_out/surface_a.csv  -- FP16 under `transformers`, measured on Kaggle
  results/surface_b.csv           -- the quantised GGUF under `llama.cpp` + GBNF

Table 17's latency columns (p50/p95, tok/s, peak RSS) come from a third file, produced on a
third machine:

  results/exp1_cooled.csv         -- per-trial timing/RSS/thermal rows from the Pi (eval/exp1.py),
                                     the cooled run of record; results/exp1.csv is its uncooled
                                     predecessor, reported in results/thermal_headroom.md

Exp-1 covers only the **Q4_K_M** configurations (STATE.md triage: 60 timed runs, not the PRD's
200, Q8_0 dropped from the hardware sweep). A Q8_0 row therefore keeps `--` in those columns
here -- not because the script forgot, but because nothing measured it. Table 19's Decode p95
is pooled over the same three Q4_K_M configs and is explicit that Q8_0 latency was never run.

Usage:
    python eval/tables.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):  # `python eval/tables.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.bench import aggregate, read_trials

REPO = Path(__file__).resolve().parent.parent
SURFACE_A = REPO / "train" / "kaggle_out" / "surface_a.csv"
SURFACE_B = REPO / "results" / "surface_b.csv"
SURFACE_B_NOGRAMMAR = REPO / "results" / "surface_b_nogrammar.csv"
#: Exp-1 of record. The PRD declares the target as a Raspberry Pi 5 with an **active
#: cooler** (PRD.tex:199) and names one as the mitigation for risk R-8, "thermal
#: throttling corrupts latency figures" (PRD.tex:1841). The first Exp-1 ran before the
#: cooler was fitted and throttled on 180/180 scored trials, so it measured a
#: configuration this project never declared. The cooled run is the protocol-compliant
#: measurement and the one these tables report.
EXP1 = REPO / "results" / "exp1_cooled.csv"
#: Kept, not discarded. NFR-10 must "always be reported" (prd.md:538), and the delta
#: between the two runs is itself a result: what sustained throttling costs a
#: sub-billion model on a passively-cooled Pi 5. Rendered by `thermal_headroom()`.
EXP1_THROTTLED = REPO / "results" / "exp1.csv"
RESULTS = REPO / "results"
#: Exp-3's per-SNR summary, written by `eval/exp3.py` from its per-item files. The Pi's
#: run (A7b) is of record once it exists: it carries the latency column, and where its
#: predictions differ from the workstation's (A7a) the target's are the result (the
#: comparison is `results/exp3_pi_parity.csv`). Before A7b, the workstation's is used.
EXP3_PI = REPO / "results" / "exp3_pi.csv"
EXP3 = EXP3_PI if EXP3_PI.is_file() else REPO / "results" / "exp3.csv"
EXP2 = REPO / "results" / "exp2.csv"
EXP2_ANALYSIS = REPO / "results" / "exp2_analysis.md"
EXP4 = REPO / "results" / "exp4.csv"
WAKE_TRAINING = REPO / "results" / "wake_training.json"
WAKE_REAL_VOICE = REPO / "results" / "wake_real_voice.json"

SPLITS = ("test_synth", "test_golden", "test_ood")
#: The headline split for Table 18. The golden set is real recorded speech through the real
#: ASR, so it is the honest place to ask what quantisation costs; test_synth is TTS and
#: flatters every configuration equally.
DELTA_SPLIT = "test_golden"

#: Table 12, NFR-18.
FALSE_COMMAND_BUDGET = 0.05

#: Splits whose gold targets carry no slots at all, so slot-F1 has no dynamic range on them.
#: `test_ood` is the abstention set: 150 out-of-domain utterances whose gold is
#: `{"intent":"unknown"}` and nothing else -- 0 gold slot pairs across all 150 items. With
#: zero gold slots, true positives and false negatives are pinned at 0, so precision is 0
#: whenever the model emits any slot at all and `slot_micro_f1` can only ever return 0.0
#: (it emitted something) or `nan` (it emitted nothing). It cannot tell one spurious slot
#: apart from thirty-one, which is the only question worth asking on this split -- and
#: `false_command_rate` already answers it, on a scale that means something. Printing the
#: arithmetically-correct 0.0 next to 97.5 and 94.5 in the same column reads as a collapse
#: in slot filling that never happened, so Table 17 prints `--` instead.
NO_SLOT_SPLITS = ("test_ood",)


def _rows(path: Path) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"missing {path.relative_to(REPO)} -- run the sweep that writes it")
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _f(value: str) -> float | None:
    return float(value) if value not in ("", None) else None


def _pct(value: float | None, places: int = 1) -> str:
    return "--" if value is None else f"{100 * value:.{places}f}"


def _frac(value: float | None, places: int = 3) -> str:
    """A rate as a fraction, the scale the prose and the 0.85 threshold use.

    Three places resolve one item in 200; the pooled figures of Table 19 (3,540 decodes)
    keep four, because their difference is under a tenth of a point.
    """
    return "--" if value is None else f"{value:.{places}f}"


def _signed(value: float, places: int = 1) -> str:
    """A signed difference with a true minus sign (U+2212, rendered `$-$` in LaTeX)."""
    text = f"{value:+.{places}f}"
    if float(text) == 0:
        return f"{0:.{places}f}"
    return text.replace("-", "\u2212")


def _half_up(value: float, places: int = 3) -> str:
    """Round half up, as the prose does: 0.0375 is 0.038, where float formatting gives 0.037."""
    from decimal import ROUND_HALF_UP, Decimal
    return str(Decimal(repr(round(value, 9))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


MCNEMAR = REPO / "results" / "mcnemar.csv"


def _mcnemar(family: str) -> dict[tuple[str, str], dict]:
    """(system_a, system_b) -> row of `results/mcnemar.csv` for one family, or {}."""
    if not MCNEMAR.is_file():
        return {}
    return {(r["system_a"], r["system_b"]): r for r in _rows(MCNEMAR) if r["family"] == family}


ADAPTERS = REPO / "train" / "kaggle_out" / "adapters"


def _epoch_gains() -> dict[str, float]:
    """Model -> validation EM gained between the last two epochs, from the training logs."""
    import json

    gains = {}
    for path in sorted(ADAPTERS.glob("*/training_history.json")):
        history = json.loads(path.read_text(encoding="utf-8"))["history"]
        if len(history) >= 2:
            gains[path.parent.name] = history[-1]["val_exact_match"] - history[-2]["val_exact_match"]
    return gains


def _exp1_summaries(path: Path = EXP1) -> dict[str, dict]:
    """Exp-1 config (== a Q4_K_M gguf stem, e.g. `qwen2.5-0.5b-instruct-Q4_K_M`) -> summary.

    Warm-up rows are excluded by name (`<stem>-warmup`), never by discarding CSV rows --
    every request the Pi answered is still in the CSV for inspection. The path is a
    parameter so the same aggregation renders both the cooled run of record and the
    throttled one, with no second code path to keep in step.
    """
    if not path.is_file():
        return {}
    rows = [r for r in read_trials(path) if not r["config"].endswith("-warmup")]
    return {s["config"]: s for s in aggregate(rows)}


#: 2.4 GHz pinned by the `performance` governor / 1.5 GHz held under throttle (STATE.md, Exp-1).
CLOCK_UNCAPPED_GHZ = 2.4
CLOCK_RATIO = CLOCK_UNCAPPED_GHZ / 1.5


def _cooled_run_state() -> str:
    """"0 of 180 scored trials throttled, 67.5-74.1 C", computed from the per-trial rows."""
    if not EXP1.is_file():
        return "no timed run on record"
    rows = [r for r in read_trials(EXP1) if not r["config"].endswith("-warmup")]
    temps = [float(r["temperature_c"]) for r in rows if r.get("temperature_c") not in ("", None)]
    throttled = sum(str(r.get("throttled_now")) in ("1", "True") for r in rows)
    return (f"{throttled} of {len(rows)} scored trials throttled, "
            f"{min(temps):.1f}\u2013{max(temps):.1f} \u00b0C")


def table17(surface_b: list[dict]) -> str:
    exp1 = _exp1_summaries()
    lines = [
        "### Table 17: Model comparison on the deployed surface",
        "",
        "The deployed surface: each quantised artefact decoded by `llama.cpp` under the [GBNF](#acr:gbnf)",
        "grammar. Accuracy columns are fractions, scored on the workstation from",
        "`results/surface_b.csv` over 240 (`test_synth`), 200 (`test_golden`) and 150 (`test_ood`)",
        "items; Safe-fail is the share of errors that resolve to `unknown` or `hover`.",
        f"Latency, throughput and memory are from `results/{EXP1.name}`, measured on the Raspberry",
        f"Pi 5 with an active cooler fitted ({_cooled_run_state()};",
        "the uncooled run is in [Table](#tab:thermal-headroom)). p50/p95 is the language-model prefill",
        "and decode stages combined, 60 trials per configuration; Mem. is the peak resident",
        "set of the language-model process, in GiB. Only Q4_K_M was timed on the board, so a Q8_0 row carries `--`",
        "there. Slot-F1 is `--` on `test_ood`, whose 150 references carry no slots; what the models",
        "emit there is reported by the false-command rate, [Table](#tab:false-command).",
        "",
        "| Model | Quant | Split | Intent-F1 | Slot-F1 | [EM](#acr:em) | Safe-fail | Schema-valid | p50/p95 (ms) | tok/s | Mem. (GiB) |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: | :--- |",
    ]
    for row in surface_b:
        summary = exp1.get(f"{row['model']}-{row['quant']}")
        if summary:
            p50 = summary.get("total_p50", "")
            p95 = summary.get("total_p95", "")
            # Whole milliseconds, as the prose quotes them; hundredths of a ms are not resolved by
            # 60 trials, and the two extra digits were what pushed this table past the text block.
            latency = "--" if p50 == "" or p95 == "" else f"{float(p50):,.0f}/{float(p95):,.0f}"
            tok_s = summary.get("tokens_per_second", "--") or "--"
            rss = summary.get("peak_rss_mb", "")
            # `peak_rss_mb` is bytes / 1024**2 (eval/bench.py), so / 1024 is GiB, the header's unit.
            rss_str = "--" if rss == "" else f"{rss / 1024:.2f}"
        else:
            latency, tok_s, rss_str = "--", "--", "--"
        # `--`, not 0.0, where the split has no gold slots to score -- see NO_SLOT_SPLITS.
        slot_f1 = None if row["split"] in NO_SLOT_SPLITS else _f(row["slot_micro_f1"])
        lines.append(
            f"| {row['model']} | {row['quant']} | `{row['split']}` "
            f"| {_frac(_f(row['intent_macro_f1']))} "
            f"| {_frac(slot_f1)} "
            f"| {_frac(_f(row['exact_match']))} "
            f"| {_frac(_f(row['safe_failure_rate']))} "
            f"| {_frac(_f(row['schema_validity']))} | {latency} | {tok_s} | {rss_str} |"
        )
    return "\n".join(lines) + "\n"


def table18(surface_a: list[dict], surface_b: list[dict], split: str) -> str:
    fp16 = {r["model"]: _f(r["exact_match"]) for r in surface_a
            if r["surface"] == "A_fp16_finetuned" and r["split"] == split}
    tests = _mcnemar("deployment")
    n_items = next((int(r["n"]) for r in surface_b if r["split"] == split), 0)
    alpha = next((float(r["alpha"]) for r in tests.values()), None)
    lines = [
        f"### Table 18: Quantisation delta --- exact match on `{split}`",
        "",
        f"Exact match on `{split}` ({n_items} items) of each fine-tuned fp16 model on the reference",
        "surface (base model plus adapter under `transformers` on a Kaggle T4, no grammar)",
        "against its quantised artefacts on the deployed surface (`llama.cpp` under the [GBNF](#acr:gbnf)",
        "grammar, scored on the workstation). Numeric format, runtime, grammar and decoding",
        "settings change together, and for Llama-3.2-1B the checkpoint as well, so the delta",
        "measures the *deployment pipeline*, not weight precision alone. b and c are the items",
        "only the reference and only the deployed artefact get right; p is the exact McNemar",
        f"test, an exploratory family of {len(tests)} corrected to \u03b1 = "
        f"{'--' if alpha is None else f'{alpha:.4f}'}; no pair reaches it. Sources:",
        "`train/kaggle_out/surface_a.csv`, `results/surface_b.csv`, `results/mcnemar.csv`.",
        "",
        "| Model | Quant | Reference [EM](#acr:em) | Deployed [EM](#acr:em) | Delta (pp) | b / c | p |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in surface_b:
        if row["split"] != split:
            continue
        before, after = fp16.get(row["model"]), _f(row["exact_match"])
        delta = "--" if before is None or after is None else _signed(100 * (after - before))
        test = tests.get((f"{row['model']} fp16", f"{row['model']} {row['quant']}"))
        counts = "--" if test is None else f"{test['only_a']} / {test['only_b']}"
        p_value = "--" if test is None else f"{float(test['p_value']):.2f}"
        lines.append(f"| {row['model']} | {row['quant']} | {_frac(before)} | {_frac(after)} "
                     f"| {delta} | {counts} | {p_value} |")
    return "\n".join(lines) + "\n"


def nfr18(surface_b: list[dict]) -> str:
    lines = [
        "### False-command rate on out-of-domain input",
        "",
        "Share of the 150 out-of-domain `test_ood` items whose dispatched action is anything",
        "other than `unknown`, on the deployed surface; an output the validator rejects falls",
        f"back to `hover`, and `hover` counts as a false command. Budget: \u2264 {FALSE_COMMAND_BUDGET:.2f}.",
        "Source: `results/surface_b.csv`.",
        "",
        "| Model | Quant | False-command rate | Verdict |",
        "| :--- | :--- | ---: | :--- |",
    ]
    for row in surface_b:
        rate = _f(row.get("false_command_rate", ""))
        if rate is None:
            continue
        verdict = "MEETS" if rate <= FALSE_COMMAND_BUDGET else "**MISS**"
        lines.append(f"| {row['model']} | {row['quant']} | {rate:.4f} | {verdict} |")
    return "\n".join(lines) + "\n"


def table19(constrained: list[dict], ablated: list[dict]) -> str:
    """Table 19, the grammar ablation --- contribution C1 measured rather than asserted."""

    def totals(rows: list[dict]) -> tuple[int, int, float]:
        items = sum(int(r["n"]) for r in rows)
        valid = sum(_f(r["schema_validity"]) * int(r["n"]) for r in rows)
        matched = sum(_f(r["exact_match"]) * int(r["n"]) for r in rows)
        return items, round(items - valid), matched / items

    on_items, on_invalid, on_em = totals(constrained)
    off_items, off_invalid, off_em = totals(ablated)
    lines = [
        "### Table 19: Grammar ablation",
        "",
        "The six deployed artefacts decode the same 590 items (240 `test_synth`, 200",
        "`test_golden`, 150 `test_ood`) greedily, with and without `schema/cmd.gbnf` given to",
        "`llama.cpp`; nothing else changes. Scored on the workstation. Sources:",
        "`results/surface_b.csv` (grammar on) and `results/surface_b_nogrammar.csv` (grammar off).",
        "",
        "| Condition | Decodes | Schema validity | Malformed | [EM](#acr:em) (pooled) |",
        "| :--- | ---: | ---: | ---: | ---: |",
        f"| Grammar on | {on_items} | {1 - on_invalid / on_items:.4f} | {on_invalid} "
        f"| {on_em:.4f} |",
        f"| Grammar off | {off_items} | {1 - off_invalid / off_items:.4f} | {off_invalid} "
        f"| {off_em:.4f} |",
        "",
        "Pooled over every model, quantisation and split. Exact match is pooled by item, not",
        "averaged over the eighteen rows, so the larger splits carry their real weight.",
    ]
    return "\n".join(lines) + "\n"


#: Table 12 budgets Exp-3 owns.
NFR7_CLEAN_CRR, NFR8_10DB_CRR, NFR9_SAFE_FAILURE = 0.80, 0.65, 0.70


def table20(exp3: list[dict]) -> str:
    """Table 20, end to end on the golden set's audio (Exp-3). EM - CRR is the ASR cost."""

    def ci(row: dict, key: str, scale: float = 1.0, places: int = 3) -> str:
        lo, hi = _f(row[f"{key}_lo"]), _f(row[f"{key}_hi"])
        return "--" if lo is None else f"[{lo * scale:.{places}f}, {hi * scale:.{places}f}]"

    def label(row: dict) -> str:
        return "clean" if row["condition"] == "clean" else f"{row['snr_db']} dB"

    def e2e(row: dict) -> str:
        if not row.get("e2e_p50_ms"):
            return "pending (Pi run)"
        return f"{float(row['e2e_p50_ms']):.0f}/{float(row['e2e_p95_ms']):.0f} (n={row['e2e_n']})"

    lines = [
        "### Table 20: Acoustic robustness on the golden set",
        "",
        "Golden-set audio through Silero endpointing (450 ms), whisper `tiny.en` and",
        "`qwen2.5-0.5b-instruct-Q4_K_M` under the grammar; rotor noise (DREGON, evaluation",
        "partition) mixed digitally on active-speech level. EM is the same items as reference",
        "text through the same parser, so EM - CRR is the cost of the speech stage. Intervals",
        "are 95% bootstrap over utterances; safe-failure is over failed items only.",
        f"Host: `{exp3[0].get('host', '')}`. The last column is per segment, nearest rank:",
        "speech recognition + prefill + decode + validation, replayed faster than real time",
        "(no queue, no HTTP), so it shows how latency moves with noise; end-to-end latency is",
        "judged in the latency experiment ([Table](#tab:latency-budget)).",
        "",
        "| SNR | n | CRR | 95% CI | WER % | 95% CI | EM | EM - CRR | 95% CI | Safe-failure | Stage sum p50/p95 (ms) |",
        "| :--- | ---: | ---: | :--- | ---: | :--- | ---: | ---: | :--- | :--- | :--- |",
    ]
    for row in exp3:
        safe = _f(row["safe_failure_rate"])
        lines.append(
            f"| {label(row)} | {row['n']} | {float(row['crr']):.3f} | {ci(row, 'crr')} "
            f"| {_pct(_f(row['wer']))} | {ci(row, 'wer', 100, 1)} | {float(row['em']):.3f} "
            f"| {float(row['em_minus_crr']):+.3f} | {ci(row, 'em_minus_crr')} "
            f"| {'--' if safe is None else f'{safe:.3f}'} ({row['n_safe']}/{row['n_failed']}) "
            f"| {e2e(row)} |")

    by = {r["condition"]: r for r in exp3}

    def verdict(name: str, value: float | None, budget: float, where: str) -> str:
        if value is None:
            return f"{name} ({where}): not measured."
        return (f"{name} ({where}, >= {budget:.2f}): {value:.3f} -- "
                f"**{'MEETS' if value >= budget else 'MISSES'}**.")

    safe_rates = [(label(r), _f(r["safe_failure_rate"])) for r in exp3]
    worst = min((v for _, v in safe_rates if v is not None), default=None)
    lines += [
        "",
        verdict("Clean-audio recognition, CRR", _f(by["clean"]["crr"]) if "clean" in by else None,
                NFR7_CLEAN_CRR, "clean"),
        verdict("Recognition in noise, CRR", _f(by["10"]["crr"]) if "10" in by else None,
                NFR8_10DB_CRR, "10 dB"),
        verdict("Safe failure, safe-failure rate", worst, NFR9_SAFE_FAILURE, "lowest across SNR"),
        "Tests across SNR, the operational envelope and the segmentation breakdown:",
        f"`results/{EXP3.stem}_analysis.md`.",
    ]
    return "\n".join(lines) + "\n"


#: Which Table 6 line each Exp-2 measure is judged against, in Table 6's order. Row names
#: follow the thesis naming (issue 00): stages as the Master's tab:latency-budget words them,
#: the reflex/parse path, and no requirement or experiment codes. Bold marks a row that a
#: criterion of the Ingenieur's tab:nonfunctional-requirements is judged on.
_BUDGET_LINES = (
    ("vad_wait", "branch_b", "Endpointing wait"),
    ("stt", "branch_b", "Speech recognition (whisper `tiny.en`, 3 threads)"),
    ("prefill", "branch_b", "Language-model prefill"),
    ("decode", "branch_b", "Language-model decode"),
    ("validate_fsm", "branch_b", "Validation, state-machine check and dispatch"),
    ("e2e_t0", "branch_b", "**End to end, from end of speech**"),
    ("e2e_speech_end", "branch_b", "End to end, including the endpointing wait"),
    ("e2e_speech_start", "branch_b", "End to end, from start of speech"),
    ("a_offset", "idle", "**Reflex path from keyword offset, idle**"),
    ("a_algorithmic", "idle", "of which spotter delay and frame quantisation"),
    ("a_system", "idle", "of which Pi compute and publish"),
    ("a_offset", "loaded", "**Reflex path from keyword offset, loaded**"),
    ("a_algorithmic", "loaded", "of which spotter delay and frame quantisation"),
    ("a_system", "loaded", "of which Pi compute and publish"),
    ("a_onset", "idle", "Reflex path from keyword onset, idle"),
    ("a_onset", "loaded", "Reflex path from keyword onset, loaded"),
    ("recovery", "loaded", "**Preemption recovery**"),
)


def latency_budget(exp2: list[dict]) -> str:
    """Table 6 against Exp-2's measured p95s on the Pi (NFR-1, NFR-2, NFR-3, NFR-17)."""
    by = {(r["measure"], r["condition"]): r for r in exp2}

    def ms(value: str) -> str:
        return "--" if value in ("", None) else f"{float(value):,.0f}"

    lines = [
        "### Latency budget versus measured",
        "",
        "Raspberry Pi 5, cooled, governor `performance`, cores pinned (frame loop on core 0;",
        "speech recognition and language model on cores 1-3). Real-time replay of recorded",
        "audio: the parse path on the 200 golden utterances (clean), one sample per endpointed",
        "segment; the reflex path on the author's 40 recorded keyword takes, twice, idle and",
        "while the parse path decodes. Nearest-rank percentiles; the verdict is on the p95.",
        "Rows in bold are judged against a criterion of [Table](#tab:nonfunctional-requirements).",
        "The bus is loopback on the Pi; the Wi-Fi hop is outside the budget.",
        "",
        "| Stage | n | p50 | p95 | p99 | Target p95 | Verdict |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]
    for measure, condition, label in _BUDGET_LINES:
        row = by.get((measure, condition))
        if row is None:
            continue
        target = row["budget_p95_ms"]
        lines.append(f"| {label} | {row['n']} | {ms(row['p50'])} | {ms(row['p95'])} | {ms(row['p99'])} "
                     f"| {ms(target) if target else '--'} | {row['verdict'] or '--'} |")
    lines += [
        "",
        "Prefill is the deployed parser's, with the prompt cache off; the budget's prefill",
        "allowance assumes a cached prefix. Start-of-speech has no verdict: its 5,500 ms target is for a",
        "3 s utterance. Split rate, cross-trigger matrix, pre-emption outcomes and the core-0 frame",
        "budget: `results/exp2_analysis.md`.",
    ]
    return "\n".join(lines) + "\n"


#: Budgets of the Ingenieur's tab:nonfunctional-requirements that no results file carries
#: itself (the latency budgets are in exp2.csv; the CRR budgets are NFR7/NFR8 above).
KEYWORD_FA_PER_HOUR, KEYWORD_FRR, FORMATION_ACCURACY = 1.0, 0.10, 0.85


def _interval_verdict(lo: float, hi: float, budget: float) -> str:
    """The keyword criteria's declared rule (results/wake_real_voice.md, STATE.md): a rate
    from a small event count meets its upper bound only if the whole 95% interval is below
    it, misses only if the whole interval is above it, and is otherwise not demonstrated."""
    if hi <= budget:
        return "Met"
    return "Missed" if lo > budget else "Not demonstrated"


def _preemption_counts(path: Path = EXP2_ANALYSIS) -> tuple[int, int, int]:
    """(decodes in flight at a trigger, triggers, decodes aborted), from the analysis file
    eval/exp2.py writes -- the only record of the preemption outcomes."""
    text = path.read_text(encoding="utf-8")
    in_flight = re.search(r"decode in flight: (\d+)/(\d+)", text)
    aborted = re.search(r"Decode aborted by the trigger: (\d+)", text)
    if not (in_flight and aborted):
        raise ValueError(f"{path.name}: preemption outcomes not found; eval/exp2.py changed?")
    return int(in_flight[1]), int(in_flight[2]), int(aborted[1])


def _cross_triggers(path: Path = EXP2_ANALYSIS) -> int:
    """Takes of one class that fired the other class, summed over the idle and loaded
    matrices of the same analysis file."""
    text = path.read_text(encoding="utf-8")
    hold = re.findall(r"\| `swarm_hold` \| \d+ \| \d+ \| (\d+) \| \d+ \|", text)
    abort = re.findall(r"\| `swarm_abort` \| \d+ \| (\d+) \| \d+ \| \d+ \|", text)
    if len(hold) != 2 or len(abort) != 2:
        raise ValueError(f"{path.name}: expected an idle and a loaded cross-trigger matrix")
    return sum(map(int, hold + abort))


def requirements_summary(exp2: list[dict], exp3: list[dict], exp4: list[dict],
                         wake_training: dict, wake_real: dict) -> str:
    """Every criterion of the Ingenieur's two requirement tables, with the measurement that
    answers it and one verdict. Every number is read from a results file. The only typed
    evidence is for the criteria verified by a test suite (simulation backends, flight state
    machine: swarm/test_pyflyt.py, swarm/test_fsm.py, 105 passed on 24 Sep) or not yet run."""
    by2 = {(r["measure"], r["condition"]): r for r in exp2}
    by3 = {r["condition"]: r for r in exp3}

    def ms(measure: str, condition: str) -> tuple[str, str, str]:
        row = by2[(measure, condition)]
        return (f"{float(row['p95']):,.0f} ms", f"{float(row['budget_p95_ms']):,.0f} ms",
                "Met" if row["verdict"] == "MEETS" else "Missed")

    def crr(condition: str, budget: float) -> tuple[str, str]:
        value = float(by3[condition]["crr"])
        return f"{value:.3f}", "Met" if value >= budget else "Missed"

    def sec(label: str) -> str:
        return f"[ref](#{label})"

    in_flight, triggers, aborted = _preemption_counts()
    crossed = _cross_triggers()
    n = len(exp4)
    converged = sum(int(r["converged"]) for r in exp4)
    collisions = sum(int(r["collisions"]) for r in exp4)
    interventions = sum(int(r["clamp_activations"]) for r in exp4)
    accuracies = [float(r["formation_accuracy"]) for r in exp4]
    ambient = wake_training["test"]["ambient"]
    fa_lo, fa_hi = ambient["per_hour_ci95"]
    frr = {r["class"]: r for r in wake_real["rows"]}
    frr_verdicts = {_interval_verdict(*r["frr_ci95"], KEYWORD_FRR) for r in frr.values()}
    stages = [m for m in ("vad_wait", "stt", "prefill", "decode", "validate_fsm")
              if (m, "branch_b") in by2]
    idle, loaded = ms("a_offset", "idle"), ms("a_offset", "loaded")
    e2e, recovery = ms("e2e_t0", "branch_b"), ms("recovery", "loaded")
    clean, noise = crr("clean", NFR7_CLEAN_CRR), crr("10", NFR8_10DB_CRR)

    rows = [
        # Functional (tab:functional-requirements), in its order.
        ("Offline speech recognition", "On the device, no network",
         "No run with networking disabled", "Not yet run", sec("sec:demonstration-protocol")),
        ("Reflex path", "Preempts the parse path",
         f"{aborted}/{in_flight} decodes cancelled; {crossed} cross-triggers",
         "Met" if aborted == in_flight == triggers and crossed == 0 else "Missed",
         sec("sec:latency-experiment")),
        ("Swarm controller", "Formation control, five drones",
         f"{converged}/{n} trials converged", "Met" if converged == n else "Missed",
         sec("sec:formation-control")),
        ("Simulation backends", "Hover smoke test on both", "Passes on both, same gains", "Met",
         sec("sec:simulation-backends")),
        ("Live demonstration", "Live microphone, end to end", "--", "Planned for the defence",
         sec("sec:demonstration-protocol")),
        ("Flight state machine", "Every legality cell tested", "Every cell passes", "Met",
         sec("sec:state-machine")),
        # Non-functional (tab:nonfunctional-requirements), in its order.
        ("Reflex latency", f"p95 \u2264 {idle[1]}", f"{idle[0]} idle, {loaded[0]} loaded",
         "Met" if idle[2] == loaded[2] == "Met" else "Missed", sec("sec:latency-experiment")),
        ("End-to-end latency", f"p95 \u2264 {e2e[1]}", e2e[0], e2e[2],
         sec("sec:latency-experiment")),
        ("Per-stage attribution", "Every stage, p50/p95/p99", f"All {len(stages)} stages",
         "Met" if len(stages) == 5 else "Missed", sec("sec:latency-experiment")),
        ("Preemption recovery", f"p95 \u2264 {recovery[1]}", recovery[0], recovery[2],
         sec("sec:latency-experiment")),
        ("Keyword false accepts", f"\u2264 {KEYWORD_FA_PER_HOUR:.0f} per hour",
         f"{ambient['per_hour']:.2f}/h [{fa_lo:.2f}, {fa_hi:.2f}]",
         _interval_verdict(fa_lo, fa_hi, KEYWORD_FA_PER_HOUR),
         sec("sec:keyword-spotter-evaluation")),
        ("Keyword false rejects", f"\u2264 {KEYWORD_FRR:.2f} per class",
         "; ".join(f"{c.removeprefix('swarm_')} {r['frr']:.2f} [{r['frr_ci95'][0]:.2f}, "
                   f"{r['frr_ci95'][1]:.2f}]" for c, r in frr.items()),
         frr_verdicts.pop() if len(frr_verdicts) == 1 else "Not demonstrated",
         sec("sec:latency-experiment")),
        ("Clean-audio recognition", f"CRR \u2265 {NFR7_CLEAN_CRR:.2f}", *clean,
         sec("sec:acoustic-robustness")),
        ("Recognition in noise", f"CRR \u2265 {NFR8_10DB_CRR:.2f} at 10 dB", *noise,
         sec("sec:acoustic-robustness")),
        ("Collisions", "Zero observed", f"{collisions} in {n} trials",
         "Met" if collisions == 0 else "Missed", sec("sec:formation-control")),
        ("Formation accuracy", f"\u2265 {FORMATION_ACCURACY:.2f}",
         f"{min(accuracies):.3f} in every trial" if min(accuracies) == max(accuracies)
         else f"{min(accuracies):.3f} lowest trial",
         "Met" if min(accuracies) >= FORMATION_ACCURACY else "Missed",
         sec("sec:formation-control")),
        ("Offline operation", "No network dependency", "No run with networking disabled",
         "Not yet run", sec("sec:demonstration-protocol")),
    ]
    lines = [
        "### Summary against the requirements",
        "",
        "Every criterion of [Table](#tab:functional-requirements) and",
        "[Table](#tab:nonfunctional-requirements), in their order, with the measurement that",
        "answers it and the section that reports it. *Met* and *Missed* are judged on the point",
        "estimate, as in each experiment's own table. The two keyword criteria are rates from",
        "small event counts and follow the rule declared before they were scored: met only if",
        "the whole 95% interval (in brackets) is inside the budget, missed only if it is wholly",
        "outside, and otherwise *not demonstrated*.",
        "",
        "| Criterion | Target | Measured | Verdict | Section |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    lines += [
        "",
        f"Collisions: zero observed across all {n} trials, backed by a hard geometric",
        f"separation clamp at the integrator, which made {interventions:,} interventions (vehicle",
        "pairs, summed over timesteps, that the potential field alone failed to keep apart).",
        "Formation accuracy is saturated by the protocol; convergence time is the measure that",
        "discriminates ([Section](#sec:formation-control)).",
    ]
    return "\n".join(lines) + "\n"


def _model_meta() -> dict[str, dict]:
    """Per-model metadata (parameter count, family) from `train/configs/*.yaml`.

    Read rather than hardcoded, for the same reason every other number here is read:
    a parameter count typed into this file can drift from the config the model was
    actually trained under, and nothing would catch it. Requires PyYAML, which is in
    the project environment.
    """
    import yaml

    meta = {}
    for path in sorted((REPO / "train" / "configs").glob("*.yaml")):
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        if "params" not in cfg:
            raise SystemExit(f"{path.name} has no `params` -- Table 33 needs it")
        meta[cfg["name"]] = {"params": int(cfg["params"]), "family": cfg["family"]}
    return meta


def table33(surface_a: list[dict]) -> str:
    """Table 33 --- the Surface-A comparison across all four models.

    Not in prd.md's frozen table set (1-32), and deliberately separate from Table 17
    rather than folded into it: Table 17 reports Surface B, the quantised artefact
    that ships, and h2o-danube3 has no Surface B (scoped to the reference surface --
    see its config's scope_note). Putting a model with no Surface B into Table 17
    would mean a row of blanks in the table that answers RQ1.

    What this table exists for. The other three models sit at three parameter counts
    in three different families, so size and family are perfectly aliased and no
    pairwise comparison can separate them. h2o-danube3-500m is an iso-parameter
    control against qwen2.5-0.5b (514M vs 494M, different families, identical
    recipe), which splits the two effects apart for the first time.
    """
    meta = _model_meta()
    finetuned = [r for r in surface_a if r["surface"] == "A_fp16_finetuned"]
    by_model: dict[str, dict[str, float | None]] = {}
    for row in finetuned:
        by_model.setdefault(row["model"], {})[row["split"]] = _f(row["exact_match"])

    missing = [m for m in by_model if m not in meta]
    if missing:
        raise SystemExit(f"no config metadata for {missing} -- add params/family")

    order = sorted(by_model, key=lambda m: meta[m]["params"])
    lines = [
        "### Table 33: Exact match of the four fine-tuned models on the reference surface",
        "",
        "Exact match of each fine-tuned fp16 model on the reference surface (base model plus",
        "adapter under `transformers` on a Kaggle T4, greedy, no grammar), by split: 240",
        "(`test_synth`), 200 (`test_golden`) and 150 (`test_ood`) items. Source:",
        "`train/kaggle_out/surface_a.csv`; parameter counts and families from",
        "`train/configs/*.yaml`. Ordered by parameter count.",
        "",
        "| Model | Params | Family | " + " | ".join(SPLITS) + " |",
        "| :--- | ---: | :--- | " + " | ".join("---:" for _ in SPLITS) + " |",
    ]
    for model in order:
        cells = [_frac(by_model[model].get(s)) for s in SPLITS]
        lines.append(f"| {model} | {meta[model]['params'] / 1e6:,.0f} M | "
                     f"{meta[model]['family']} | " + " | ".join(cells) + " |")

    # The contrast the table exists to support, computed rather than asserted. Prose, not
    # a markdown sub-heading and bullets: the note is printed under the LaTeX table as-is.
    lines += [""]
    pairs = []
    ranked = [(m, meta[m]["params"], by_model[m].get(DELTA_SPLIT)) for m in order]
    ranked = [r for r in ranked if r[2] is not None]

    # Iso-parameter: the closest pair by parameter count from different families.
    best = None
    for i, (m_a, p_a, e_a) in enumerate(ranked):
        for m_b, p_b, e_b in ranked[i + 1:]:
            if meta[m_a]["family"] == meta[m_b]["family"]:
                continue
            spread = abs(p_a - p_b) / min(p_a, p_b)
            if best is None or spread < best[0]:
                best = (spread, m_a, p_a, e_a, m_b, p_b, e_b)
    if best:
        _, m_a, p_a, e_a, m_b, p_b, e_b = best
        test = _mcnemar("family control").get((f"{m_a} fp16", f"{m_b} fp16")) \
            or _mcnemar("family control").get((f"{m_b} fp16", f"{m_a} fp16"))
        paired = ("" if test is None else
                  f"; {test['only_a']} against {test['only_b']} discordant items, exact McNemar "
                  f"p = {float(test['p_value']):.4f}")
        pairs.append(
            f"**Family, at matched size** ({m_a}, {p_a/1e6:,.0f} M, against {m_b}, "
            f"{p_b/1e6:,.0f} M, {_pct(abs(p_a - p_b) / min(p_a, p_b))}% apart): "
            f"{abs(e_a - e_b) * 100:.1f} pp on `{DELTA_SPLIT}` ({_frac(e_a)} against {_frac(e_b)}"
            f"{paired}).")

    # The widest parameter spread. Not a size effect: no family appears at two sizes, so
    # the endpoints differ in family as well, and the note says so rather than a ratio.
    lo, hi = ranked[0], ranked[-1]
    pairs.append(
        f"**Full span** ({lo[0]}, {lo[1]/1e6:,.0f} M, to {hi[0]}, {hi[1]/1e6:,.0f} M, "
        f"{hi[1]/lo[1]:.1f}\u00d7): {_signed((hi[2] - lo[2]) * 100)} pp on `{DELTA_SPLIT}` "
        f"({_frac(lo[2])} \u2192 {_frac(hi[2])}); the endpoints are also two different families, so "
        "this is not a size effect.")
    lines.append(" ".join(pairs))

    # Convergence, from the training logs rather than a sentence carried from a config.
    gains = _epoch_gains()
    rising = sorted((g, m) for m, g in gains.items() if m in by_model and g > 0)
    flat = [m for m, g in gains.items() if m in by_model and g <= 0]
    if rising:
        lines += [
            "",
            "The recipe is frozen at three epochs for every model. Validation exact match was "
            + ("unchanged between epochs two and three only for " + ", ".join(flat) + "; " if flat else "")
            + "it was still rising at epoch 3 for "
            + ", ".join(f"{m} (+{_half_up(g)})" for g, m in rising)
            + ", so no model is shown to have converged, and the comparison is one "
            "**under an identical three-epoch budget**, not one of capability.",
        ]
    lines += [""]
    return "\n".join(lines)


def thermal_headroom(cooled: dict[str, dict], throttled: dict[str, dict]) -> str:
    """The cost of running the declared hardware without its declared cooler.

    Reports NFR-10 for both runs, which prd.md:538 requires be "always reported", and
    the per-configuration delta. The two runs are otherwise identical -- same board,
    same 60 scored trials per config after the same ten-minute warm-up, same pinned
    cores, same governor, same artefacts -- so the difference isolates cooling.
    """
    lines = [
        "### Thermal headroom: cooled and uncooled benchmark runs",
        "",
        "The multi-model benchmark's run of record (`results/exp1_cooled.csv`, active cooler",
        "fitted) against an earlier run without active cooling (`results/exp1.csv`). The protocol",
        "is otherwise identical: same board, same three Q4_K_M artefacts, 60 scored trials per",
        "configuration after a ten-minute warm-up, cores 1\u20133 pinned, `performance` governor,",
        "swap disabled. Accuracy is not repeated: it is scored on the workstation and does not",
        "depend on the board's clock.",
        "",
        "| Config | Run | Throttled trials | Max temp. (\u00b0C) | Decode p95 (ms) | [SLM](#acr:slm) total p95 (ms) | tok/s |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | ---: |",
    ]
    for config in sorted(cooled):
        for run, summaries in (("cooled", cooled), ("uncooled", throttled)):
            summary = summaries.get(config)
            if not summary:
                continue
            share = _f(summary.get("throttled_fraction"))
            lines.append(
                f"| {' '.join(config.rsplit('-', 1))} | {run} "
                f"| {'--' if share is None else f'{100 * share:.0f}%'} "
                f"| {_f(summary.get('max_temperature_c')) or float('nan'):.1f} "
                f"| {_f(summary.get('slm_decode_p95')) or float('nan'):.1f} "
                f"| {_f(summary.get('total_p95')) or float('nan'):.1f} "
                f"| {_f(summary.get('tokens_per_second')) or float('nan'):.2f} |")

    verdicts = []
    for run, summaries in (("cooled", cooled), ("uncooled", throttled)):
        shares = [_f(s.get("throttled_fraction")) for s in summaries.values()]
        shares = [v for v in shares if v is not None]
        if not shares:
            continue
        worst = max(shares)
        verdicts.append(f"{run}, worst configuration {100 * worst:.0f}% "
                        f"({'meets' if worst <= 0.05 else 'misses'})")
    notes = []
    if verdicts:
        notes.append("**Throttling** (share of trials with a non-zero throttle flag, budget 5%): "
                     + "; ".join(verdicts) + ".")

    deltas = []
    for config in sorted(cooled):
        hot, cold = throttled.get(config), cooled.get(config)
        if not (hot and cold):
            continue
        hot_p95, cold_p95 = _f(hot.get("slm_decode_p95")), _f(cold.get("slm_decode_p95"))
        hot_tps, cold_tps = _f(hot.get("tokens_per_second")), _f(cold.get("tokens_per_second"))
        if None in (hot_p95, cold_p95, hot_tps, cold_tps) or not (hot_p95 and hot_tps):
            continue
        deltas.append((config, 100 * (cold_p95 - hot_p95) / hot_p95,
                       100 * (cold_tps - hot_tps) / hot_tps))
    if deltas:
        # The base is the uncooled run: "decode p95 -25.1%" is the cooled figure relative to
        # the uncooled one. Said in the note, because read the other way round the same
        # throughput figure overstates what the missing cooler cost by up to 28 points.
        notes.append(
            "**Cooled relative to uncooled**: "
            + "; ".join(f"{' '.join(c.rsplit('-', 1))}, decode p95 {_signed(dp)}% and throughput {_signed(dt)}%"
                        for c, dp, dt in deltas) + ".")
        # Stated from the data, not asserted: the throttled clock was capped, not logged, so
        # the ratio is a lower bound and a gain above it does not by itself rule the clock out.
        largest = max(deltas, key=lambda d: d[2])
        needed = CLOCK_UNCAPPED_GHZ / (1 + largest[2] / 100)
        notes.append(
            f"The uncooled run was capped at 1.5 GHz against the {CLOCK_UNCAPPED_GHZ:.1f} GHz the "
            f"`performance` governor sets, a clock ratio of at least {CLOCK_RATIO:.1f}\u00d7; the "
            f"clock actually held was not logged. The largest throughput gain, "
            f"{1 + largest[2] / 100:.2f}\u00d7 on {largest[0].rsplit('-', 1)[0]}, is accounted for by "
            f"the clock alone only if the throttled clock fell below {needed:.2f} GHz.")
    if notes:
        lines += ["", " ".join(notes)]
    lines += [""]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# LaTeX emission
#
# The thesis may not hand-copy a number out of a CSV into a `tabular` (the
# thesis-writing skill's rule 8, "never hand-type a number that a script could
# produce"). These renderers therefore convert the markdown each table function
# already returns, rather than formatting the numbers a second time: one code
# path decides what a cell says, so the `.md` under results/ and the `.tex` the
# chapter inputs cannot drift apart. A rule added to a table above --
# NO_SLOT_SPLITS, say -- reaches the PDF with no second edit.
# ---------------------------------------------------------------------------

#: Build products of the document, not measurements -- results/ holds what the
#: harness measured, and nothing here is a new number.
GENERATED = REPO / "thesis" / "generated"

_TEX_ESCAPES = (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
                ("}", r"\}"), ("~", r"\textasciitilde{}"),
                ("^", r"\textasciicircum{}"),
                # Typography the markdown writes as Unicode; applied after the escapes
                # above, so the backslashes they introduce are not escaped again. The
                # chapter body is kept ASCII, and these reach it through \input.
                ("\u2013", "--"), ("\u2014", "---"), ("\u2212", "$-$"),
                ("\u00d7", r"$\times$"), ("\u2192", r"$\to$"), ("\u2264", r"$\leq$"), ("\u2265", r"$\geq$"),
                ("\u00b0", r"\textdegree{}"), ("\u03b1", r"$\alpha$"))

#: `[Table](#tab:x)` in the markdown -> `Table~\ref{tab:x}` in the PDF: the one place a
#: caption may name another float, by label and never by a number typed in.
_REF = re.compile(r"\[(Table|Figure|Section|ref)\]\(#([A-Za-z0-9:-]+)\)")
#: `[SLM](#acr:slm)` -> `\acrshort{slm}`: an acronym from shared/acronyms.tex, never typed
#: by hand in the PDF. \acrshort, not \gls, because these land in float captions and table
#: heads, where a first-use expansion would be spent before the prose reaches the term.
_ACR = re.compile(r"\[([A-Za-z0-9]+)\]\(#acr:([a-z0-9]+)\)")


def _tex_escape(text: str) -> str:
    for char, replacement in _TEX_ESCAPES:
        text = text.replace(char, replacement)
    return text


#: Inline markdown emphasis, longest marker first so `**` is not eaten as two `*`.
_EMPHASIS = ((re.compile(r"\*\*(.+?)\*\*"), r"\\textbf{\1}"),
             (re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])"), r"\\emph{\1}"))


def _tex_cell(cell: str) -> str:
    """One markdown cell or caption line -> LaTeX.

    Backticks become \\texttt; `**x**` and `*x*` become \\textbf and \\emph. Emphasis is
    resolved before escaping, on the escaped fragments, so a literal underscore inside an
    emphasised run still reaches the PDF as an underscore.
    """
    out, parts = [], cell.strip().split("`")
    for index, part in enumerate(parts):
        if index % 2:
            out.append(r"\texttt{" + _tex_escape(part) + "}")
            continue
        part = _ACR.sub(lambda m: "\x00acr" + m.group(2) + "\x00", part)
        pieces = _REF.split(part)
        for step in range(0, len(pieces), 3):
            text = _tex_escape(pieces[step])
            for pattern, replacement in _EMPHASIS:
                text = pattern.sub(replacement, text)
            text = re.sub("\x00acr([a-z0-9]+)\x00", r"\\acrshort{\1}", text)
            out.append(text)
            if step + 2 < len(pieces):
                word = pieces[step + 1]  # `[ref](#x)` is a bare number, for a table cell
                out.append(("" if word == "ref" else word + "~") + r"\ref{" + pieces[step + 2] + "}")
    return "".join(out)


def _align(spec: str) -> str:
    spec = spec.strip()
    if spec.startswith(":") and spec.endswith(":"):
        return "c"
    return "r" if spec.endswith(":") else "l"


#: Applied to LaTeX cells only, and only to *labels* -- never to a number. Table 17 carries
#: eleven columns and runs 52pt past the text block at full width; every model in this
#: project is an instruction-tuned checkpoint, so the suffix distinguishes nothing and
#: dropping it is what makes the table fit without shrinking the type further. The markdown
#: under results/ keeps the full artefact stem, because that is the measurement record.
_TEX_ABBREVIATIONS = (("qwen2.5-0.5b-instruct", "Qwen2.5-0.5B"),
                      ("llama-3.2-1b-instruct", "Llama-3.2-1B"),
                      ("smollm2-360m-instruct", "SmolLM2-360M"),
                      ("h2o-danube3-500m-chat", "H2O-Danube3-500M"),
                      ("-instruct", ""))


def markdown_to_latex(markdown: str, label: str, size: str = r"\footnotesize",
                      colsep_pt: int = 4, abbreviate: bool = False,
                      columns: str | None = None) -> str:
    """Render the single pipe-table in `markdown` as a LaTeX table float.

    The prose above the table becomes the caption, because the skill asks captions to be
    self-contained: a reader must be able to read the table without the body text. Prose
    below the table (Table 33's three-epoch caveat, Table 19's pooled note) becomes a
    note under the rule, where it stays attached to the numbers it qualifies.

    `columns` replaces the spec derived from the markdown alignment row, for a table whose
    cells are text and must wrap (p-columns); it must name as many columns as the header.
    """
    lines = markdown.splitlines()
    table = [l for l in lines if l.lstrip().startswith("|")]
    if len(table) < 3:
        raise ValueError(f"{label}: expected a header, a rule and at least one row")
    first, last = lines.index(table[0]), lines.index(table[-1])

    title = next((l.lstrip("# ").strip() for l in lines[:first] if l.startswith("#")), "")
    caption_lines = [l for l in lines[:first] if l.strip() and not l.startswith("#")]
    notes_lines = [l for l in lines[last + 1:] if l.strip()]

    def cell(text: str) -> str:
        if abbreviate:
            for long, short in _TEX_ABBREVIATIONS:
                text = text.replace(long, short)
        return _tex_cell(text)

    header = [cell(c) for c in table[0].strip().strip("|").split("|")]
    column_spec = columns or "".join(_align(c) for c in table[1].strip().strip("|").split("|"))
    body = [[cell(c) for c in row.strip().strip("|").split("|")] for row in table[2:]]
    for index, row in enumerate(body):
        if len(row) != len(header):
            raise ValueError(
                f"{label}: row {index} has {len(row)} cells, header has {len(header)}")

    # Joined *before* conversion, not after: the markdown wraps at 90 columns, so a
    # `*run*` or a `` `path` `` in a caption routinely straddles a line break and a
    # per-line conversion would leave the marker in the PDF as a literal asterisk.
    # "Table 16:" is stripped: LaTeX numbers the float itself, and a heading used as the
    # caption would otherwise print as "Table 4.1: Table 16: ...".
    heading = cell(re.sub(r"^Table \d+:\s*", "", title))
    caption = cell(" ".join(caption_lines)) or heading
    # The List of Tables gets the heading, not the paragraph: a five-sentence entry with
    # an unbreakable \texttt{path} in it runs 60pt into the margin there.
    short = heading or caption
    rule = " " + chr(92) * 2
    out = [
        "% Generated by eval/tables.py -- do not edit; edit the renderer and re-run.",
        r"\begin{table}[htbp]",
        r"  \centering",
        "  " + size,
        r"  \setlength{\tabcolsep}{" + str(colsep_pt) + "pt}",
        r"  \caption[" + short + "]{" + caption + "}",
        r"  \label{" + label + "}",
        r"  \begin{tabular}{" + column_spec + "}",
        r"    \toprule",
        "    " + " & ".join(header) + rule,
        r"    \midrule",
    ]
    out += ["    " + " & ".join(row) + rule for row in body]
    out += [r"    \bottomrule", r"  \end{tabular}"]
    if notes_lines:
        out += [r"  \par\medskip",
                r"  \begin{minipage}{\textwidth}\footnotesize\raggedright "
                + cell(" ".join(notes_lines)) + r"\end{minipage}"]
    out += [r"\end{table}", ""]
    return "\n".join(out)



#: stem -> (LaTeX label, font size, \tabcolsep, abbreviate labels). Table 17 carries eleven
#: columns and needs both tighter settings; so does Table 20, which ran 23.6pt past the text
#: block at 3pt (measured 24 Sep); the rest are comfortable at footnotesize.
_TABLES = (
    ("table17_model_comparison", "tab:model-comparison", r"\scriptsize", 2, True),
    ("table18_quantisation_delta", "tab:quantisation-delta", r"\footnotesize", 5, True),
    ("nfr18_false_command", "tab:false-command", r"\footnotesize", 5, True),
    ("table19_grammar_ablation", "tab:grammar-ablation", r"\scriptsize", 3, True),
    ("table33_iso_parameter", "tab:iso-parameter", r"\footnotesize", 5, True),
    ("thermal_headroom", "tab:thermal-headroom", r"\scriptsize", 3, True),
    ("table20_end_to_end", "tab:end-to-end", r"\scriptsize", 2, False),
    ("exp2_latency_budget", "tab:latency-budget", r"\footnotesize", 4, False),
    ("requirements_summary", "tab:requirements-summary", r"\footnotesize", 4, False),
)

#: Column specs for tables whose cells are text and must wrap. The requirements summary is
#: all words; as plain l-columns it ran 139pt past the text block (measured 24 Sep).
_WRAP = r">{\raggedright\arraybackslash}p"
_COLUMNS = {
    "requirements_summary": "@{}" + _WRAP + "{3.5cm}" + _WRAP + "{3.6cm}" + _WRAP + "{4.6cm}"
                            + _WRAP + "{2.5cm}r@{}",
}

#: Rendered to LaTeX here but computed elsewhere: `eval/exp0.py` owns Table 16 and writes
#: its markdown. Converting it here rather than duplicating the emitter in exp0.py keeps
#: one markdown-to-LaTeX path for the whole document, at the cost of this module reading a
#: file it does not produce -- which is why the read is tolerant of the file's absence.
_FOREIGN_TABLES = (
    ("table16_asr_speaker_sensitivity", "tab:asr-sensitivity", r"\scriptsize", 3, False),
)


def run() -> int:
    surface_a, surface_b = _rows(SURFACE_A), _rows(SURFACE_B)
    rendered = {
        "table17_model_comparison": table17(surface_b),
        "table18_quantisation_delta": table18(surface_a, surface_b, DELTA_SPLIT),
        "nfr18_false_command": nfr18(surface_b),
        "table19_grammar_ablation": table19(surface_b, _rows(SURFACE_B_NOGRAMMAR)),
        "table33_iso_parameter": table33(surface_a),
        "thermal_headroom": thermal_headroom(_exp1_summaries(),
                                             _exp1_summaries(EXP1_THROTTLED)),
    }
    if EXP3.is_file():
        rendered["table20_end_to_end"] = table20(_rows(EXP3))
    else:
        print("  skipped table20_end_to_end: results/exp3.csv not written yet (eval/exp3.py)")
    if EXP2.is_file():
        rendered["exp2_latency_budget"] = latency_budget(_rows(EXP2))
    else:
        print("  skipped exp2_latency_budget: results/exp2.csv not written yet (eval/exp2.py, Pi)")
    summary_inputs = (EXP2, EXP2_ANALYSIS, EXP3, EXP4, WAKE_TRAINING, WAKE_REAL_VOICE)
    if all(path.is_file() for path in summary_inputs):
        rendered["requirements_summary"] = requirements_summary(
            _rows(EXP2), _rows(EXP3), _rows(EXP4),
            json.loads(WAKE_TRAINING.read_text(encoding="utf-8")),
            json.loads(WAKE_REAL_VOICE.read_text(encoding="utf-8")))
    else:
        missing = [path.name for path in summary_inputs if not path.is_file()]
        print(f"  skipped requirements_summary: {', '.join(missing)} not written yet")
    written = []
    for stem, text in rendered.items():
        (RESULTS / f"{stem}.md").write_text(text, encoding="utf-8")
        written.append(f"results/{stem}.md")

    GENERATED.mkdir(parents=True, exist_ok=True)
    for stem, label, size, colsep, abbreviate in _TABLES:
        if stem not in rendered:
            continue
        tex = markdown_to_latex(rendered[stem], label, size=size, colsep_pt=colsep,
                                abbreviate=abbreviate, columns=_COLUMNS.get(stem))
        (GENERATED / f"{stem}.tex").write_text(tex, encoding="utf-8")
        written.append(f"thesis/generated/{stem}.tex")

    for stem, label, size, colsep, abbreviate in _FOREIGN_TABLES:
        source = RESULTS / f"{stem}.md"
        if not source.is_file():
            print(f"  skipped {stem}: results/{stem}.md not written yet "
                  f"(run the experiment that owns it)")
            continue
        tex = markdown_to_latex(source.read_text(encoding="utf-8"), label, size=size,
                                colsep_pt=colsep, abbreviate=abbreviate)
        (GENERATED / f"{stem}.tex").write_text(tex, encoding="utf-8")
        written.append(f"thesis/generated/{stem}.tex")
    print("wrote " + ", ".join(written))
    return 0


if __name__ == "__main__":
    sys.exit(run())
