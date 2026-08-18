#!/usr/bin/env python3
"""Exp-3 --- acoustic robustness: the golden set's audio through the whole Branch B path.

`prd.md` Table 15, Exp-3: the full pipeline on golden-set audio at five SNR levels
(clean, 20, 15, 10, 5 dB), same items as Exp-1 and the same comparator, "so EM minus
CRR is the ASR cost". One runner serves both halves of A7: the workstation run (A7a)
produces every accuracy column, and the Pi run (A7b) replays the same audio through
the same code for Table 20's latency column and to check that ARM decodes the same
strings x86 does --- expected, not assumed.

The path, per utterance, is the deployed one and nothing else:

    WAV --80 ms chunks--> runtime/vad.py Endpointer --segments--> runtime/stt.py
        --transcript--> runtime/parser.py (llama-server + schema/cmd.gbnf)
        --raw JSON--> schema/validate.py (via eval/metrics.py, fallback on)

**The stream ends in digital silence.** Each file is fed in 80 ms chunks and then
followed by `TAIL_S` of zeros, so a segment still open when the file runs out is
closed by the same silence rule as every other segment rather than by a special
end-of-file path the runtime does not have. No lead-in is added: every golden file
already carries its own (about 0.6 s), and in the noisy conditions that lead-in holds
rotor noise, as a live stream would.

**One utterance can reach the parser as several segments.** At the 450 ms default
the golden set's disfluencies split about one utterance in ten (`runtime/vad.py`).
Each segment is transcribed, parsed and validated separately, as it would be live, and
every command so produced is one the swarm would have received. So an item is
*recognised* only if it produced at least one segment and **every** dispatched command
is canonically equal to the gold one. Scoring only the last segment would credit an
item that first flew a partial, wrong command. That alternative is still computed and
reported beside the rule of record, because it moves the headline.

**Safe failure follows the same logic.** A failed item is safe only if nothing it
dispatched was other than `unknown` or `hover`. An item that produced no segment at
all dispatched nothing; it is counted safe and its count is reported on its own line,
because "the VAD heard nothing" and "the model abstained" are different mechanisms.

**EM comes from the same run.** The reference transcripts go through the same parser
on the same server (`text` condition), so EM and CRR differ in input modality only
(`prd.md` 6.1). That EM is then checked item by item against Surface B's per-item
predictions for the same artefact: Table 17 and Table 20 must be describing one model.

Usage:
    python eval/exp3.py                    # run whatever is missing, then analyse
    python eval/exp3.py --analyse-only     # re-derive results/ from the per-item files
    python eval/exp3.py --fresh            # re-run every condition
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # `python eval/exp3.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import soundfile as sf

from eval.metrics import SAFE_INTENTS, score_predictions
from eval.norm import edits
from eval.stats import BOOTSTRAP_SEED, bootstrap_ratio_ci, bonferroni_alpha, mcnemar

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
PREDS = RESULTS / "exp3_preds"
GOLDEN = REPO / "data" / "test_golden.jsonl"
CLEAN_AUDIO = REPO / "data" / "audio" / "s1_16k"
MIXED_AUDIO = REPO / "data" / "audio" / "mixed"
GGUF = REPO / "gguf" / "qwen2.5-0.5b-instruct-Q4_K_M.gguf"
SURFACE_B_PREDS = RESULTS / "surface_b_preds" / f"{GGUF.stem}_test_golden.jsonl"

#: `text` is the reference-transcript pass that supplies EM; the other five are audio.
AUDIO_CONDITIONS: tuple[str, ...] = ("clean", "20", "15", "10", "5")
TEXT = "text"

CHUNK = 1280        # 80 ms at 16 kHz, the frame size Exp-2's replay uses
TAIL_S = 1.5        # > min_silence + pad + one window: closes any open segment
PORT = 8915         # clear of surface_b.py (8912) and the parser's default (8914)

#: Table 12 budgets this experiment owns.
NFR7_CLEAN_CRR = 0.80
NFR8_10DB_CRR = 0.65
NFR9_SAFE_FAILURE = 0.70


# --- per-item scoring ------------------------------------------------------


@dataclass(frozen=True)
class Outcome:
    """How one item scored, from its per-segment dispatched commands."""

    correct: bool        # rule of record: >= 1 segment and every one correct
    correct_last: bool   # sensitivity: the last segment alone
    safe: bool           # meaningful only when not correct
    n_segments: int


def outcome(segments: Sequence[dict]) -> Outcome:
    """Score one item. Each segment carries `correct` and `dispatched` (from eval.metrics)."""
    if not segments:
        return Outcome(correct=False, correct_last=False, safe=True, n_segments=0)
    return Outcome(
        correct=all(s["correct"] for s in segments),
        correct_last=bool(segments[-1]["correct"]),
        safe=all(s["dispatched"] in SAFE_INTENTS for s in segments),
        n_segments=len(segments),
    )


def score_segment(raw: str, gold: str) -> dict:
    """The single comparator (eval/metrics.py -> schema/canon.py), one segment."""
    (prediction,) = score_predictions([raw], [gold])
    return {"canonical": prediction.predicted, "dispatched": prediction.dispatched,
            "correct": prediction.correct}


# --- the run ---------------------------------------------------------------


def audio_dir(condition: str) -> Path:
    return CLEAN_AUDIO if condition == "clean" else MIXED_AUDIO / f"snr{int(condition):02d}"


def _load_golden() -> list[dict]:
    return [json.loads(l) for l in GOLDEN.read_text(encoding="utf-8").splitlines() if l.strip()]


def endpoint(audio: np.ndarray, endpointer) -> list:
    """Replay one file through the Endpointer, then close the stream with silence."""
    endpointer.reset()
    stream = np.concatenate([audio, np.zeros(int(TAIL_S * 16_000), dtype=np.int16)])
    segments = []
    for start in range(0, stream.size, CHUNK):
        segments += endpointer.feed(stream[start : start + CHUNK])
    return segments


def run_text(items: Sequence[dict], parser) -> list[dict]:
    rows = []
    for item in items:
        result = parser.parse(item["transcript"])
        rows.append({"id": item["id"], "condition": TEXT, "reference": item["transcript"],
                     "gold": item["target"],
                     "segments": [{"transcript": item["transcript"], "raw": result.raw,
                                   **score_segment(result.raw, item["target"])}]})
    return rows


def run_audio(condition: str, items: Sequence[dict], parser, endpointer) -> list[dict]:
    from runtime.stt import transcribe_utterance

    rows = []
    source = audio_dir(condition)
    with tempfile.TemporaryDirectory(prefix="exp3_") as scratch:
        for item in items:
            audio, rate = sf.read(str(source / f"{item['id']}.wav"), dtype="int16")
            if rate != 16_000 or audio.ndim != 1:
                raise ValueError(f"{source / item['id']}.wav: expected 16 kHz mono, got {rate} Hz")
            segments = []
            for k, utt in enumerate(endpoint(audio, endpointer)):
                wav = utt.to_wav(Path(scratch) / f"{item['id']}_{k}.wav")
                started = time.perf_counter()
                transcript = transcribe_utterance(wav)
                stt_ms = (time.perf_counter() - started) * 1000.0
                result = parser.parse(transcript)
                started = time.perf_counter()
                scored = score_segment(result.raw, item["target"])
                validate_ms = (time.perf_counter() - started) * 1000.0
                segments.append({
                    "start_s": round(utt.start_s, 4), "end_s": round(utt.end_s, 4),
                    "t0_s": round(utt.t0_s, 4), "forced": utt.forced,
                    "transcript": transcript, "raw": result.raw, **scored,
                    # Host timings. Not of record on the workstation; A7b reads them on the Pi.
                    "stt_ms": round(stt_ms, 2), "prefill_ms": round(result.prefill_ms, 2),
                    "decode_ms": round(result.decode_ms, 2), "validate_ms": round(validate_ms, 3),
                })
            rows.append({"id": item["id"], "condition": condition,
                         "reference": item["transcript"], "gold": item["target"],
                         "segments": segments})
    return rows


def _write_rows(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def run_missing(conditions: Sequence[str], preds: Path, fresh: bool, limit: int | None) -> None:
    items = _load_golden()[:limit]
    pending = [c for c in conditions
               if fresh or not (preds / f"{c}.jsonl").is_file()
               or len(_read_rows(preds / f"{c}.jsonl")) != len(items)]
    if not pending:
        print("every condition already on disk; analysing")
        return

    from runtime.parser import CommandParser
    from runtime.vad import Endpointer

    parser, server = CommandParser.for_gguf(GGUF, port=PORT)
    endpointer = Endpointer()
    host = platform.node()
    try:
        for condition in pending:
            started = time.monotonic()
            rows = (run_text(items, parser) if condition == TEXT
                    else run_audio(condition, items, parser, endpointer))
            for row in rows:
                row["host"] = host
            _write_rows(preds / f"{condition}.jsonl", rows)
            print(f"  {condition:>5s}: {len(rows)} items in {time.monotonic() - started:.0f} s",
                  flush=True)
    finally:
        server.stop()


# --- analysis --------------------------------------------------------------


def _seed(label: str) -> int:
    """Per-condition bootstrap seed, stable across processes (never `hash()`, ADR-0004)."""
    digest = hashlib.sha256(f"exp3:{label}".encode("utf-8")).hexdigest()[:8]
    return (BOOTSTRAP_SEED + int(digest, 16)) % (2**32)


def surface_b_mismatches(text_rows: Sequence[dict]) -> list[str]:
    """Items whose runtime-path raw output differs from Surface B's for the same artefact."""
    if not SURFACE_B_PREDS.is_file():
        return ["surface_b_preds file missing"]
    reference = {r["id"]: r["raw"] for r in _read_rows(SURFACE_B_PREDS)}
    return [r["id"] for r in text_rows if reference.get(r["id"]) != r["segments"][0]["raw"]]


def summarise(condition: str, rows: Sequence[dict], em_correct: dict[str, bool]) -> dict:
    outcomes = [outcome(r["segments"]) for r in rows]
    correct = [float(o.correct) for o in outcomes]
    ones = [1.0] * len(rows)
    failed = [o for o in outcomes if not o.correct]
    seed = _seed(condition)

    errors, words = [], []
    for row in rows:
        hypothesis = " ".join(s["transcript"] for s in row["segments"])
        counted = edits(row["reference"], hypothesis)
        errors.append(counted.total)
        words.append(counted.ref_words)

    em = [float(em_correct[r["id"]]) for r in rows]
    gap = [e - c for e, c in zip(em, correct)]  # paired, same items
    crr_lo, crr_hi = bootstrap_ratio_ci(correct, ones, seed=seed)
    wer_lo, wer_hi = bootstrap_ratio_ci(errors, words, seed=seed + 1)
    gap_lo, gap_hi = bootstrap_ratio_ci(gap, ones, seed=seed + 2)
    # Resampling utterances over the whole set: an item that did not fail has
    # denominator 0 and drops out, so each replicate is a rate over failed items.
    safe_lo, safe_hi = bootstrap_ratio_ci(
        [float(not o.correct and o.safe) for o in outcomes],
        [float(not o.correct) for o in outcomes], seed=seed + 3)

    n = len(rows)
    return {
        "condition": condition,
        "snr_db": "" if condition == "clean" else int(condition),
        "n": n,
        "crr": sum(correct) / n, "crr_lo": crr_lo, "crr_hi": crr_hi,
        "crr_last_segment": sum(o.correct_last for o in outcomes) / n,
        "wer": sum(errors) / sum(words), "wer_lo": wer_lo, "wer_hi": wer_hi,
        "em": sum(em) / n,
        "em_minus_crr": sum(gap) / n, "em_minus_crr_lo": gap_lo, "em_minus_crr_hi": gap_hi,
        "n_failed": len(failed),
        "n_safe": sum(o.safe for o in failed),
        "safe_failure_rate": (sum(o.safe for o in failed) / len(failed)) if failed else float("nan"),
        "safe_lo": safe_lo, "safe_hi": safe_hi,
        "n_no_segment": sum(o.n_segments == 0 for o in outcomes),
        "n_split": sum(o.n_segments > 1 for o in outcomes),
        "n_forced": sum(any(s.get("forced") for s in r["segments"]) for r in rows),
        # Latency is A7b's (the Pi). Left empty here rather than filled with workstation time.
        "e2e_n": "", "e2e_p50_ms": "", "e2e_p95_ms": "",
        "host": rows[0].get("host", "") if rows else "",
    }


def cochran_q(matrix: np.ndarray) -> tuple[float, int, float]:
    """Cochran's Q over an items x conditions 0/1 matrix: (Q, df, p)."""
    from scipy.stats import chi2

    x = np.asarray(matrix, dtype=float)
    k = x.shape[1]
    col, row = x.sum(axis=0), x.sum(axis=1)
    total = x.sum()
    denominator = k * total - np.square(row).sum()
    if denominator == 0:
        return 0.0, k - 1, 1.0
    q = (k - 1) * (k * np.square(col).sum() - total**2) / denominator
    return float(q), k - 1, float(chi2.sf(q, k - 1))


def arcsine_anova(matrix: np.ndarray, labels: Sequence[str]) -> dict:
    """The pre-registered analysis, run as specified: arcsine-sqrt, one-way ANOVA, Tukey."""
    from scipy.stats import f_oneway, tukey_hsd

    groups = [np.arcsin(np.sqrt(matrix[:, j].astype(float))) for j in range(matrix.shape[1])]
    anova = f_oneway(*groups)
    tukey = tukey_hsd(*groups)
    n = matrix.shape[0]
    k = matrix.shape[1]
    pairs = []
    for i in range(k):
        for j in range(i + 1, k):
            pairs.append({"a": labels[i], "b": labels[j],
                          "crr_diff": float(matrix[:, i].mean() - matrix[:, j].mean()),
                          "p": float(tukey.pvalue[i, j])})
    return {"F": float(anova.statistic), "p": float(anova.pvalue),
            "df_between": k - 1, "df_within": k * n - k, "pairs": pairs}


def _fmt_p(p: float) -> str:
    return f"{p:.2g}" if p < 0.001 else f"{p:.4f}".rstrip("0").rstrip(".") if p < 1 else "1.0"


def _label(condition: str) -> str:
    return "clean" if condition == "clean" else f"{condition} dB"


def analysis_markdown(summaries: Sequence[dict], by_condition: dict[str, list[dict]],
                      mismatches: list[str]) -> str:
    conditions = [s["condition"] for s in summaries]
    ids = [r["id"] for r in by_condition[conditions[0]]]
    matrix = np.array([[outcome(next(r for r in by_condition[c] if r["id"] == i)["segments"]).correct
                        for c in conditions] for i in ids], dtype=int)
    labels = [_label(c) for c in conditions]
    anova = arcsine_anova(matrix, labels)
    q, df, q_p = cochran_q(matrix)
    alpha = bonferroni_alpha(len(anova["pairs"]))

    lines = [
        "## Exp-3 analysis (generated by `eval/exp3.py` from `results/exp3_preds/`)",
        "",
        f"n = {len(ids)} golden utterances per condition, one speaker, one session, rotor noise "
        "(DREGON, evaluation partition), mixed on active-speech level. Artefact "
        f"`{GGUF.stem}` under `schema/cmd.gbnf`, whisper `tiny.en` with the domain prompt, "
        "Silero endpointing at 450 ms.",
        "",
        "### Provenance",
        "",
        (f"The `text` condition (reference transcripts through the runtime parser) reproduces "
         f"Surface B's per-item raw output on all {len(ids)} items: EM here is Table 17's EM."
         if not mismatches else
         f"**The `text` condition DIFFERS from Surface B on {len(mismatches)} item(s): "
         f"{', '.join(mismatches[:20])}.** EM below is this run's, not Table 17's."),
        "",
        "### Pre-registered: arcsine-transformed CRR, one-way ANOVA + Tukey HSD across SNR",
        "",
        f"F({anova['df_between']}, {anova['df_within']}) = {anova['F']:.2f}, p = {_fmt_p(anova['p'])}.",
        "",
        "| A | B | CRR A - B | Tukey p |",
        "| :--- | :--- | ---: | ---: |",
    ]
    lines += [f"| {p['a']} | {p['b']} | {p['crr_diff']:+.3f} | {_fmt_p(p['p'])} |"
              for p in anova["pairs"]]
    lines += [
        "",
        "Two properties of this test must travel with it. (1) The unit is the utterance, "
        "whose outcome is 0 or 1, and arcsin(sqrt(x)) maps {0, 1} to {0, pi/2}: on binary "
        "data the transform is a rescaling and changes nothing. (2) The same 200 utterances "
        "appear in every condition, so the groups are not independent, which one-way ANOVA "
        "assumes. The paired test below is the one whose assumptions hold; it is reported "
        "beside the pre-registered one, not instead of it.",
        "",
        "### Paired: Cochran's Q across the five conditions, exact McNemar per pair",
        "",
        f"Q = {q:.2f}, df = {df}, p = {_fmt_p(q_p)}. Pairwise McNemar, Bonferroni over "
        f"{len(anova['pairs'])} pairs (alpha = {alpha:.4f}).",
        "",
        "| A | B | b (A only) | c (B only) | test | p | signif. |",
        "| :--- | :--- | ---: | ---: | :--- | ---: | :--- |",
    ]
    for i in range(len(conditions)):
        for j in range(i + 1, len(conditions)):
            m = mcnemar(matrix[:, i].astype(bool), matrix[:, j].astype(bool))
            lines.append(f"| {labels[i]} | {labels[j]} | {m.only_first} | {m.only_second} "
                         f"| {m.test} | {_fmt_p(m.p_value)} | "
                         f"{'yes' if m.significant_at(alpha) else 'no'} |")

    by = {s["condition"]: s for s in summaries}
    lines += ["", "### Operational envelope", "",
              "| Threshold | lowest SNR meeting it (point) | lowest SNR meeting it (95% CI lower bound) |",
              "| :--- | :--- | :--- |"]
    order = [c for c in AUDIO_CONDITIONS if c in by]  # clean, then decreasing SNR
    for name, threshold in (("CRR >= 0.80 (NFR-7's level)", NFR7_CLEAN_CRR),
                            ("CRR >= 0.65 (NFR-8's level)", NFR8_10DB_CRR)):
        cells = []
        for key in ("crr", "crr_lo"):
            met = None
            for c in order:  # walk down in SNR; the envelope ends at the first miss
                if by[c][key] >= threshold:
                    met = c
                else:
                    break
            cells.append("none (clean misses)" if met is None else _label(met))
        lines.append(f"| {name} | {cells[0]} | {cells[1]} |")
    lines += ["", "The envelope is contiguous from clean downward: it ends at the first tested "
              "level that misses, even if a lower level happens to meet the threshold.", ""]

    lines += ["### Segmentation and the scoring rule", "",
              "| Condition | split (>1 segment) | no segment | forced cut | CRR, every segment | CRR, last segment only |",
              "| :--- | ---: | ---: | ---: | ---: | ---: |"]
    for s in summaries:
        lines.append(f"| {_label(s['condition'])} | {s['n_split']} | {s['n_no_segment']} "
                     f"| {s['n_forced']} | {s['crr']:.3f} | {s['crr_last_segment']:.3f} |")
    lines += ["", "Where the failures come from. A failed single-segment item is an ASR or parser "
              "error on a whole utterance; a failed split item may also be the endpointer "
              "handing the parser a fragment.", "",
              "| Condition | failed | of which single-segment | of which split | split items that failed |",
              "| :--- | ---: | ---: | ---: | ---: |"]
    for c in conditions:
        scored = [outcome(r["segments"]) for r in by_condition[c]]
        failed = [o for o in scored if not o.correct]
        split_failed = sum(o.n_segments > 1 for o in failed)
        n_split = sum(o.n_segments > 1 for o in scored)
        lines.append(f"| {_label(c)} | {len(failed)} | {len(failed) - split_failed} "
                     f"| {split_failed} | {split_failed}/{n_split} |")
    lines += ["", "CRR of record is 'every segment': a split utterance is recognised only if "
              "every command it dispatched was correct. Items with no segment dispatched "
              "nothing and are counted as safe failures.", ""]
    return "\n".join(lines)


def _csv_value(value: object) -> object:
    if isinstance(value, float):
        return "" if math.isnan(value) else f"{value:.4f}"
    return value


def outputs(preds: Path) -> tuple[Path, Path]:
    """`results/exp3_preds` -> `results/exp3.csv`; A7b's `exp3_pi_preds` -> `exp3_pi.csv`.

    Derived from the per-item directory so the Pi run can never overwrite the
    workstation's summary, which is the thing it is compared against.
    """
    stem = preds.name.removesuffix("_preds")
    return preds.parent / f"{stem}.csv", preds.parent / f"{stem}_analysis.md"


def analyse(preds: Path) -> int:
    csv_out, analysis_out = outputs(preds)
    text_path = preds / f"{TEXT}.jsonl"
    if not text_path.is_file():
        print(f"[-] {text_path} missing; run without --analyse-only")
        return 1
    text_rows = _read_rows(text_path)
    em_correct = {r["id"]: r["segments"][0]["correct"] for r in text_rows}
    mismatches = surface_b_mismatches(text_rows)

    by_condition = {c: _read_rows(preds / f"{c}.jsonl") for c in AUDIO_CONDITIONS
                    if (preds / f"{c}.jsonl").is_file()}
    if not by_condition:
        print("[-] no audio condition on disk")
        return 1
    summaries = [summarise(c, rows, em_correct) for c, rows in by_condition.items()]

    fields = list(summaries[0].keys())
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for s in summaries:
            writer.writerow({k: _csv_value(v) for k, v in s.items()})
    analysis_out.write_text(analysis_markdown(summaries, by_condition, mismatches), encoding="utf-8")

    print(f"wrote {csv_out} and {analysis_out}")
    print(f"provenance: {'text condition == Surface B on every item' if not mismatches else f'{len(mismatches)} MISMATCH(ES) vs Surface B'}")
    for s in summaries:
        print(f"  {_label(s['condition']):>6s}  CRR {s['crr']:.3f} [{s['crr_lo']:.3f}, {s['crr_hi']:.3f}]"
              f"  WER {s['wer']*100:5.1f}%  EM {s['em']:.3f}  EM-CRR {s['em_minus_crr']:+.3f}"
              f"  safe {s['n_safe']}/{s['n_failed']}  split {s['n_split']}  none {s['n_no_segment']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--conditions", nargs="+", default=[TEXT, *AUDIO_CONDITIONS],
                        choices=[TEXT, *AUDIO_CONDITIONS])
    parser.add_argument("--preds", type=Path, default=PREDS, help="per-item output directory")
    parser.add_argument("--fresh", action="store_true", help="re-run conditions already on disk")
    parser.add_argument("--analyse-only", action="store_true")
    parser.add_argument("--limit", type=int, help="first N items only (debugging; use a scratch --preds)")
    args = parser.parse_args(argv)

    if not args.analyse_only:
        run_missing(args.conditions, args.preds, args.fresh, args.limit)
    return analyse(args.preds)


if __name__ == "__main__":
    sys.exit(main())
