#!/usr/bin/env python3
"""Branch A on the author's own voice --- the false-reject rate the synthetic test cannot give.

`results/wake_training.md` states its own gap: every positive in the keyword-spotter
corpus is Piper TTS in three voices, and the test voices are the train voices, so
"FRR on the author's own voice is not measured here". This script measures it on 40
real takes (20 `swarm hold`, 20 `swarm abort`) recorded Wed 23 Sep with the golden
set's microphone (`data/audio/wake_real/`, prompts in `data/wake_real_transcripts.txt`),
resampled by the same tool and rule as the golden set:

    python data/resample.py --session s1 --input data/audio/wake_real \\
        --output data/audio/wake_real_16k --glob "w*.wav"

**Nothing here is new scoring logic.** Each take is scored exactly as `train_wake.py`
scored its test split: 1 s of silence either side, 80 ms frames through
`openwakeword.Model` with the trained heads, one threshold (`wake_heads.json`), a
take counted as detected if its own head ever reaches the threshold, and the 2x2
cross-trigger matrix alongside. The heads are hash-checked against `wake_heads.json`
first, as `runtime.branch_a.load_trained` does: the threshold means nothing for other
weights.

**These takes are a test set and nothing else.** They were never seen in training or
threshold selection, and must not be: fitting to them would spend the only real-voice
evidence Branch A has.

**n = 20 per class bounds what this can say.** The interval is exact (Clopper-Pearson),
because at 0 or 1 misses in 20 the normal approximation returns an interval that
reaches below zero. With no misses at all the 95% upper bound is still ~17%, above
NFR-16's 0.10: this can show the spotter works on the operator's voice, not prove the
budget.

Usage:
    python eval/wake_real.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # `python eval/wake_real.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

REPO = Path(__file__).resolve().parent.parent
TAKES = REPO / "data" / "audio" / "wake_real_16k"
META = REPO / "data" / "audio" / "wake_real" / "session_meta.json"
PROMPTS = REPO / "data" / "wake_real_transcripts.txt"
HEADS = REPO / "runtime" / "models" / "wake" / "wake_heads.json"
OUT_MD = REPO / "results" / "wake_real_voice.md"
OUT_JSON = REPO / "results" / "wake_real_voice.json"

#: Table 12.
NFR16_FRR = 0.10
PAD_S = 1.0  # train_wake.positive_traces' pad, so kw_end is measured the same way


def clopper_pearson(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Exact binomial interval for k events in n trials."""
    from scipy.stats import beta

    tail = (1 - confidence) / 2
    lo = 0.0 if k == 0 else float(beta.ppf(tail, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - tail, k + 1, n - k))
    return lo, hi


def labels() -> dict[str, str]:
    """take id -> class name, from the prompt list the takes were recorded against."""
    out = {}
    for line in PROMPTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        take, phrase = line.split("\t")
        out[take] = phrase.strip().replace(" ", "_")
    return out


def _check_heads() -> float:
    record = json.loads(HEADS.read_text())
    for name, head in record["heads"].items():
        digest = hashlib.sha256((HEADS.parent / head["file"]).read_bytes()).hexdigest()
        if digest != head["sha256"]:
            raise SystemExit(f"{head['file']} does not match wake_heads.json; re-run train/train_wake.py")
    return float(record["threshold"])


def run() -> int:
    from train.train_wake import CLASSES, _load_int16, _model, _pct, score_positives, stream_scores

    threshold = _check_heads()
    meta = json.loads(META.read_text())["takes"]
    classes = labels()
    unknown = set(classes.values()) - set(CLASSES)
    if unknown:
        raise SystemExit(f"prompt list names {unknown}, not one of {list(CLASSES)}")

    model = _model()
    pad = np.zeros(int(PAD_S * 16_000), dtype=np.int16)
    traces = []
    for take, name in sorted(classes.items()):
        audio = _load_int16(TAKES / f"{take}.wav")
        # Keyword offset from the capture tool's own measurement of trailing silence.
        kw_end = PAD_S + meta[take]["seconds"] - meta[take]["tail_seconds"]
        traces.append({"take": take, "label": CLASSES[name], "kw_end_s": kw_end,
                       "trace": stream_scores(model, np.concatenate([pad, audio, pad]))})

    scored = score_positives(traces, threshold)
    missed = {name: [t["take"] for t in traces if t["label"] == CLASSES[name]
                     and not (t["trace"][name] >= threshold).any()] for name in CLASSES}
    peaks = {t["take"]: {n: round(float(t["trace"][n].max()), 4) for n in CLASSES} for t in traces}

    rows = []
    for name in CLASSES:
        n = scored["n"][name]
        k = len(missed[name])
        lo, hi = clopper_pearson(k, n)
        delays = scored["delay_s"][name]
        rows.append({"class": name, "n": n, "missed": k, "frr": k / n, "frr_ci95": [lo, hi],
                     "fired_hold": scored["cross_trigger"][name]["swarm_hold"],
                     "fired_abort": scored["cross_trigger"][name]["swarm_abort"],
                     "delay_p50_ms": _pct(delays, 50) * 1000 if delays else None,
                     "delay_p95_ms": _pct(delays, 95) * 1000 if delays else None,
                     "missed_takes": missed[name]})

    OUT_JSON.write_text(json.dumps({"threshold": threshold, "rows": rows, "peaks": peaks},
                                   indent=2) + "\n", encoding="utf-8")

    def ms(value: float | None) -> str:
        return "--" if value is None else f"{value:.0f} ms"

    lines = [
        "# Branch A on the author's voice (real takes)",
        "",
        "Generated by `python eval/wake_real.py`. Do not edit by hand.",
        "",
        f"40 takes, one speaker (the author), one session (Wed 23 Sep), golden-set microphone at "
        f"10 cm, 48 kHz masters resampled by `data/resample.py`. Trained heads at the operating "
        f"point **{threshold}**, scored exactly as `train/train_wake.py` scores its test split. "
        "Never used for training or threshold selection.",
        "",
        "| class | n | missed | FRR | 95% CI (exact) | fired hold | fired abort | delay p50 | delay p95 |",
        "| :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(f"| `{r['class']}` | {r['n']} | {r['missed']} | {r['frr']:.3f} "
                     f"| [{r['frr_ci95'][0]:.3f}, {r['frr_ci95'][1]:.3f}] | {r['fired_hold']} "
                     f"| {r['fired_abort']} | {ms(r['delay_p50_ms'])} | {ms(r['delay_p95_ms'])} |")
    lines += [
        "",
        "## Read before quoting",
        "",
        f"- **NFR-16 is FRR <= {NFR16_FRR:.2f}.** A class meets it on this evidence only if its "
        "whole interval is below the budget; at n = 20 that needs zero misses and still fails "
        "(upper bound ~0.17). Quote the point estimate *with* its interval.",
        "- Missed takes, with the peak score their own head reached: " + "; ".join(
            f"`{r['class']}`: " + (", ".join(f"{t} ({peaks[t][r['class']]:.4f})"
                                             for t in r["missed_takes"]) or "none")
            for r in rows) + f". The threshold is {threshold}, at the top of the grid "
        "(`results/wake_training.md`: the scores saturate), so a miss can sit a hair under it. "
        "Per-take peaks are in `results/wake_real_voice.json`.",
        "- Delay is measured from the end of speech as the capture tool recorded it "
        "(`session_meta.json` tail silence), not from a forced alignment; it is indicative, "
        "and NFR-1's latency is Exp-2's measurement on the Pi.",
        "- One speaker in one quiet room: this closes the *synthetic-voice* caveat, not the "
        "speaker or noise ones.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {OUT_MD.relative_to(REPO)} and {OUT_JSON.relative_to(REPO)}")
    for r in rows:
        print(f"  {r['class']:12s} missed {r['missed']}/{r['n']}  FRR {r['frr']:.3f} "
              f"[{r['frr_ci95'][0]:.3f}, {r['frr_ci95'][1]:.3f}]  cross hold/abort "
              f"{r['fired_hold']}/{r['fired_abort']}  missed {r['missed_takes']}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
