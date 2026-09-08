#!/usr/bin/env python3
"""Branch A's keyword spotter: two openWakeWord heads, trained on the wake corpus.

`data/wake_corpus.py` built the corpus (3,000 positives, 5,040 negatives, split by
base rendition -- ADR-0005 D3). This script turns it into the two ONNX files that
`openwakeword.Model` loads, one per class, named so the model names it reports are
exactly `runtime/branch_a.py`'s `BRANCH_A_CLASSES`:

    runtime/models/wake/swarm_hold.onnx     runtime/models/wake/swarm_abort.onnx
    runtime/models/wake/wake_heads.json     (threshold, hashes, training record)

**What is trained, and what is not.** openWakeWord is a frozen front end
(melspectrogram -> Google's speech embedding, 96 dims per 80 ms frame) plus a small
per-keyword classifier over the last 16 embeddings. Only that classifier is trained
here. The front end is the release-v0.5.1 ONNX pair, hashed into wake_heads.json.
The upstream trainer does the head in torch; torch is kept off this workstation
(prd.md SS0.5), so the head is a scikit-learn MLP whose weights are written into an
ONNX graph by hand. The architecture is the upstream one in shape (flatten -> two
hidden ReLU layers -> sigmoid); nothing downstream can tell which library fitted it.

**Window labels come from the keyword's measured span, not from the clip label.**
A 2.5 s clip yields 7 head windows of 1.96 s. Only windows that contain the whole
phrase are positives; windows that miss it are negatives; windows that cut it are
dropped, because "swarm ho" is neither. Onset is exact (`keyword_offset_s`). Length
is read off a dry augmentation of the same base where one exists (96 of 120 bases)
and otherwise predicted from a per-voice fit on Piper's length_scale -- the fitted
ones get a wider margin. Training on full-containment windows is also what puts
detection at keyword *offset*, the anchor NFR-1 is defined at.

**Each head sees the other class as a negative.** Cross-triggers are fail-safe
(prd.md SS4.2), so this is not a safety requirement -- it is what makes the 2x2
cross-trigger matrix Exp-2 reports mean something.

**The operating point is chosen on val and declared before test is scored.**
One threshold for both heads (NFR-15 and NFR-16 are one operating point,
prd.md SS8): the highest grid threshold at which *both* classes keep val
false-reject <= VAL_FRR_TARGET. The target is half of NFR-16's 0.10, as margin
for a 150-clip val split. Test and the golden-set stream are scored once, at that
threshold, and reported whatever they say.

Evaluation runs the exported ONNX through `openwakeword.Model` itself, streaming
80 ms frames -- the deployment path, not the batch features the heads were fitted
on -- so the numbers also prove the export.

Usage:
    python train/train_wake.py              # features (cached), fit, export, evaluate
    python train/train_wake.py --refeature  # recompute the cached embeddings
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Sequence

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

MANIFEST = REPO / "data" / "wake" / "wake_manifest.json"
GOLDEN = REPO / "data" / "test_golden.jsonl"
GOLDEN_AUDIO = REPO / "data" / "audio" / "s1_16k"
FEATURE_CACHE = REPO / "train" / "wake_features" / "embeddings.npz"
OUT_DIR = REPO / "runtime" / "models" / "wake"
REPORT_MD = REPO / "results" / "wake_training.md"
REPORT_JSON = REPO / "results" / "wake_training.json"

SEED = 42
RATE = 16_000
FRAME = 1280                 # openWakeWord's 80 ms hop
HEAD_FRAMES = 16             # embeddings per head window
EMB_HOP_S = 0.08
WINDOW_S = 1.975             # 15 hops + the last embedding's 76 mel frames, +filter length
MARGIN_EXACT_S = 0.04
MARGIN_FITTED_S = 0.45       # the length fit misses by up to ~0.4 s; see the report
HIDDEN = (128, 128)
VAL_FRR_TARGET = 0.05
DEBOUNCE_S = 1.0             # one keyword, one trigger: rising edges closer than this merge
#: Adversarial near-misses are 12% of train-split negative clips (468 / 3,930; 14% is the
#: all-splits share) but every val false accept.
#: Upweighted in the loss only -- the corpus itself is frozen (tag dataset-v1.0).
ADVERSARIAL_WEIGHT = 5.0
#: The MLP's scores saturate, so the grid extends past 0.99.
THRESHOLDS = np.concatenate([np.round(np.arange(0.05, 0.991, 0.01), 2), [0.995, 0.998, 0.999]])
#: prd.md NFR-15 is defined on *ambient-speech* negatives. The authored near-misses are
#: a separate, deliberately dense stream; a per-hour rate over them is a stress figure.
AMBIENT_SOURCES = ("librispeech", "speech_commands")

#: Keys match `runtime/branch_a.py`'s BRANCH_A_CLASSES; the corpus labels carry a `pos_` prefix.
CLASSES = {"swarm_hold": "pos_swarm_hold", "swarm_abort": "pos_swarm_abort"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_int16(path: Path) -> np.ndarray:
    audio, rate = sf.read(str(path), dtype="int16")
    if rate != RATE or audio.ndim != 1:
        raise SystemExit(f"{path}: expected 16 kHz mono, got {rate} Hz, shape {audio.shape}")
    return audio


def feature_model_paths() -> dict[str, Path]:
    import openwakeword

    root = Path(openwakeword.__file__).parent / "resources" / "models"
    paths = {"melspectrogram": root / "melspectrogram.onnx", "embedding": root / "embedding_model.onnx"}
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise SystemExit(
            "openWakeWord feature models missing: " + ", ".join(missing) + "\n"
            "fetch melspectrogram.onnx and embedding_model.onnx from "
            "https://github.com/dscripka/openWakeWord/releases/tag/v0.5.1"
        )
    return paths


# --- keyword spans -----------------------------------------------------------


def keyword_spans(clips: list[dict]) -> dict[str, tuple[float, float, bool]]:
    """path -> (onset_s, end_s, exact). See the module docstring for the method."""
    exact_len: dict[str, float] = {}
    for clip in clips:
        if clip["label"] == "neg" or clip["base"] in exact_len:
            continue
        if clip["rir"] is None and clip["noise_key"] is None:
            audio, _ = sf.read(REPO / clip["path"])
            voiced = np.nonzero(np.abs(audio) > 1e-4)[0]
            exact_len[clip["base"]] = (voiced[-1] + 1) / RATE - clip["keyword_offset_s"]

    # Per-(class, voice) proportional fit: length = k * length_scale.
    ratios: dict[tuple[str, str], list[float]] = defaultdict(list)
    for clip in clips:
        if clip["label"] != "neg" and clip["base"] in exact_len:
            ratios[(clip["label"], clip["voice"])].append(exact_len[clip["base"]] / clip["length_scale"])
    k = {key: float(np.median(v)) for key, v in ratios.items()}

    spans = {}
    for clip in clips:
        if clip["label"] == "neg":
            continue
        onset = clip["keyword_offset_s"]
        if clip["base"] in exact_len:
            spans[clip["path"]] = (onset, onset + exact_len[clip["base"]], True)
        else:
            spans[clip["path"]] = (onset, onset + k[(clip["label"], clip["voice"])] * clip["length_scale"], False)
    return spans


def fit_residual(clips: list[dict]) -> float:
    """Worst error of the length fit on the bases whose length is known exactly."""
    spans = keyword_spans(clips)
    exact = {c["base"]: spans[c["path"]] for c in clips if c["label"] != "neg" and spans[c["path"]][2]}
    worst = 0.0
    by_key: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for c in clips:
        if c["label"] != "neg" and c["base"] in exact:
            on, end, _ = exact[c["base"]]
            by_key[(c["label"], c["voice"])].append((end - on, c["length_scale"]))
    for pairs in by_key.values():
        kk = float(np.median([length / scale for length, scale in pairs]))
        worst = max(worst, max(abs(length - kk * scale) for length, scale in pairs))
    return worst


# --- features ----------------------------------------------------------------


def embed_corpus(clips: list[dict], refeature: bool) -> np.ndarray:
    paths = [c["path"] for c in clips]
    if FEATURE_CACHE.exists() and not refeature:
        cached = np.load(FEATURE_CACHE, allow_pickle=False)
        if list(cached["paths"]) == paths:
            return cached["embeddings"]
        print("feature cache does not match the manifest; recomputing")

    from openwakeword.utils import AudioFeatures

    fm = feature_model_paths()
    features = AudioFeatures(
        melspec_model_path=str(fm["melspectrogram"]),
        embedding_model_path=str(fm["embedding"]),
        inference_framework="onnx",
    )
    out = []
    t0 = time.time()
    for start in range(0, len(clips), 256):
        batch = np.stack([_load_int16(REPO / p) for p in paths[start : start + 256]])
        out.append(features.embed_clips(batch, batch_size=256).astype(np.float32))
        print(f"  embedded {min(start + 256, len(clips))}/{len(clips)}  ({time.time() - t0:.0f} s)", end="\r")
    print()
    embeddings = np.concatenate(out)
    FEATURE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez(FEATURE_CACHE, embeddings=embeddings, paths=np.array(paths))
    return embeddings


def window_dataset(
    clips: list[dict], embeddings: np.ndarray, spans: dict, target: str, split: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Head windows and labels for one class head on one split."""
    n_windows = embeddings.shape[1] - HEAD_FRAMES + 1
    xs, ys, ws = [], [], []
    for index, clip in enumerate(clips):
        if clip["split"] != split:
            continue
        for j in range(n_windows):
            start, end = j * EMB_HOP_S, j * EMB_HOP_S + WINDOW_S
            label = 0
            if clip["label"] != "neg":
                onset, kw_end, exact = spans[clip["path"]]
                margin = MARGIN_EXACT_S if exact else MARGIN_FITTED_S
                contains = start <= onset - 0.01 and end >= kw_end + margin
                misses = end <= onset or start >= kw_end + margin
                if clip["label"] == target:
                    if contains:
                        label = 1
                    elif not misses:
                        continue  # cuts the phrase: neither a positive nor a negative
            xs.append(embeddings[index, j : j + HEAD_FRAMES].reshape(-1))
            ys.append(label)
            ws.append(ADVERSARIAL_WEIGHT if clip.get("source") == "adversarial" else 1.0)
    return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.int64), np.asarray(ws)


# --- the head and its ONNX form ----------------------------------------------


def fit_head(x: np.ndarray, y: np.ndarray, extra: np.ndarray):
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler().fit(x)
    neg = extra * (y == 0)
    weights = np.where(y == 1, 0.5 / (y == 1).sum(), 0.5 * neg / max(neg.sum(), 1e-9)) * len(y)
    mlp = MLPClassifier(
        hidden_layer_sizes=HIDDEN,
        activation="relu",
        alpha=1e-3,
        batch_size=256,
        learning_rate_init=1e-3,
        max_iter=40,
        random_state=SEED,
    )
    mlp.fit(scaler.transform(x), y, sample_weight=weights)
    return scaler, mlp


def export_onnx(scaler, mlp, path: Path) -> None:
    """[batch, 16, 96] -> [batch, 1]. The scaler is folded into the first layer."""
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    ws = [w.astype(np.float32) for w in mlp.coefs_]
    bs = [b.astype(np.float32) for b in mlp.intercepts_]
    scale = scaler.scale_.astype(np.float32)
    mean = scaler.mean_.astype(np.float32)
    ws[0] = ws[0] / scale[:, None]
    bs[0] = bs[0] - (mean / scale) @ (ws[0] * scale[:, None])

    inits = [numpy_helper.from_array(np.array([-1, HEAD_FRAMES * 96], dtype=np.int64), "flat_shape")]
    nodes = [helper.make_node("Reshape", ["x", "flat_shape"], ["h0"])]
    for i, (w, b) in enumerate(zip(ws, bs)):
        inits += [numpy_helper.from_array(w, f"W{i}"), numpy_helper.from_array(b, f"B{i}")]
        out = f"z{i}"
        nodes.append(helper.make_node("Gemm", [f"h{i}", f"W{i}", f"B{i}"], [out]))
        if i < len(ws) - 1:
            nodes.append(helper.make_node("Relu", [out], [f"h{i + 1}"]))
    nodes.append(helper.make_node("Sigmoid", [f"z{len(ws) - 1}"], ["score"]))
    graph = helper.make_graph(
        nodes,
        path.stem,
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, ["batch", HEAD_FRAMES, 96])],
        [helper.make_tensor_value_info("score", TensorProto.FLOAT, ["batch", 1])],
        inits,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)], producer_name="train_wake.py")
    model.ir_version = 8  # onnxruntime 1.29 reads it; newer IR adds nothing this graph uses
    onnx.checker.check_model(model)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def check_export(scaler, mlp, path: Path, x: np.ndarray) -> float:
    import onnxruntime as ort

    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    got = session.run(None, {"x": x.reshape(-1, HEAD_FRAMES, 96)})[0][:, 0]
    want = mlp.predict_proba(scaler.transform(x))[:, 1]
    return float(np.max(np.abs(got - want)))


# --- streaming evaluation ----------------------------------------------------


def _model():
    from openwakeword.model import Model

    fm = feature_model_paths()
    return Model(
        wakeword_models=[str(OUT_DIR / f"{name}.onnx") for name in CLASSES],
        inference_framework="onnx",
        melspec_model_path=str(fm["melspectrogram"]),
        embedding_model_path=str(fm["embedding"]),
    )


def stream_scores(model, audio: np.ndarray) -> dict[str, np.ndarray]:
    """Per-80 ms-frame scores for each head, from a clean model state."""
    # openwakeword's reset() primes the feature buffer with np.random noise; unseeded,
    # the same clip scores differently on every run.
    np.random.seed(SEED)
    model.reset()
    trace: dict[str, list[float]] = {name: [] for name in CLASSES}
    for i in range(0, audio.size - FRAME + 1, FRAME):
        scores = model.predict(audio[i : i + FRAME])
        for name in CLASSES:
            trace[name].append(float(scores[name]))
    return {name: np.asarray(v) for name, v in trace.items()}


def count_events(trace: np.ndarray, threshold: float) -> int:
    above = np.flatnonzero(trace >= threshold)
    if above.size == 0:
        return 0
    debounce = int(round(DEBOUNCE_S / (FRAME / RATE)))
    return 1 + int(np.sum(np.diff(above) > debounce))


def poisson_ci(count: int, hours: float) -> tuple[float, float]:
    from scipy.stats import chi2

    lo = 0.0 if count == 0 else chi2.ppf(0.025, 2 * count) / 2
    hi = chi2.ppf(0.975, 2 * count + 2) / 2
    return lo / hours, hi / hours


def positive_traces(model, clips: list[dict], spans: dict, split: str) -> list[dict]:
    pad = np.zeros(RATE, dtype=np.int16)
    out = []
    for clip in clips:
        if clip["split"] != split or clip["label"] == "neg":
            continue
        audio = np.concatenate([pad, _load_int16(REPO / clip["path"]), pad])
        trace = stream_scores(model, audio)
        out.append({"label": clip["label"], "kw_end_s": 1.0 + spans[clip["path"]][1], "trace": trace})
    return out


def negative_stream(clips: list[dict], split: str, ambient: bool) -> np.ndarray:
    return np.concatenate([_load_int16(REPO / c["path"]) for c in clips
                           if c["split"] == split and c["label"] == "neg"
                           and (c["source"] in AMBIENT_SOURCES) == ambient])


def golden_stream() -> np.ndarray:
    """The author's own 200 golden utterances, 0.5 s apart: real voice, real near-misses."""
    gap = np.zeros(RATE // 2, dtype=np.int16)
    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    parts = []
    for row in rows:
        parts += [_load_int16(GOLDEN_AUDIO / f"{row['id']}.wav"), gap]
    return np.concatenate(parts)


def score_positives(traces: list[dict], threshold: float) -> dict:
    """FRR per class, the 2x2 cross-trigger matrix, and detection delay from keyword offset."""
    names = list(CLASSES)
    matrix = {truth: {fired: 0 for fired in names} for truth in names}
    frr, delays = {}, {name: [] for name in names}
    for name, label in CLASSES.items():
        mine = [t for t in traces if t["label"] == label]
        missed = 0
        for t in mine:
            hit = False
            for other in names:
                above = np.flatnonzero(t["trace"][other] >= threshold)
                if above.size:
                    matrix[name][other] += 1
                    if other == name:
                        hit = True
                        delays[name].append((above[0] + 1) * FRAME / RATE - t["kw_end_s"])
            missed += not hit
        frr[name] = missed / len(mine)
    return {"n": {n: sum(t["label"] == l for t in traces) for n, l in CLASSES.items()},
            "frr": frr, "cross_trigger": matrix, "delay_s": delays}


def score_stream(traces: dict[str, np.ndarray], samples: int, threshold: float) -> dict:
    hours = samples / RATE / 3600
    per_class = {name: count_events(traces[name], threshold) for name in CLASSES}
    total = sum(per_class.values())
    lo, hi = poisson_ci(total, hours)
    return {"hours": hours, "events": per_class, "total": total, "per_hour": total / hours,
            "per_hour_ci95": [lo, hi]}


# --- report --------------------------------------------------------------------


def _pct(delays: list[float], q: float) -> float:
    from eval.stats import nearest_rank

    return nearest_rank(delays, q) if delays else float("nan")


def write_report(record: dict) -> None:
    thr = record["threshold"]
    lines = [
        "# Branch A keyword spotter -- training and held-out evaluation",
        "",
        "Generated by `python train/train_wake.py`. Do not edit by hand.",
        "",
        f"Operating point **{thr:.3f}**, one threshold for both heads, selected on **val** by the rule "
        f"declared in the script before test was scored: the highest threshold at which both classes keep "
        f"val false-reject <= {VAL_FRR_TARGET:.2f}.",
        "",
        "## False reject and cross-trigger (streaming, 80 ms frames, `openwakeword.Model`)",
        "",
        "| split | class | n | FRR | fired hold | fired abort | delay p50 | delay p95 |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split in ("val", "test"):
        pos = record[split]["positives"]
        for name in CLASSES:
            d = pos["delay_s"][name]
            lines.append(
                f"| {split} | `{name}` | {pos['n'][name]} | {pos['frr'][name]:.3f} | "
                f"{pos['cross_trigger'][name]['swarm_hold']} | {pos['cross_trigger'][name]['swarm_abort']} | "
                f"{_pct(d, 50) * 1000:.0f} ms | {_pct(d, 95) * 1000:.0f} ms |"
            )
    lines += [
        "",
        "Delay is the first frame at or above threshold, measured from the keyword's last voiced sample. "
        "It is the *algorithmic* part of NFR-1 (frame quantisation and window position) on the "
        "workstation; the Pi's compute is Exp-2's measurement, not this one.",
        "",
        "## False accepts (continuous stream, debounce "
        f"{DEBOUNCE_S:.1f} s)",
        "",
        "| stream | hours | hold | abort | total | per hour | 95% CI (Poisson) |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]
    for label, key in (("val ambient speech (NFR-15)", ("val", "ambient")),
                       ("val near-misses (authored)", ("val", "near_miss")),
                       ("test ambient speech (NFR-15)", ("test", "ambient")),
                       ("test near-misses (authored)", ("test", "near_miss")),
                       ("golden set (author, 200 utts)", ("golden", None))):
        s = record[key[0]][key[1]] if key[1] else record[key[0]]
        lines.append(
            f"| {label} | {s['hours']:.3f} | {s['events']['swarm_hold']} | {s['events']['swarm_abort']} | "
            f"{s['total']} | {s['per_hour']:.2f} | [{s['per_hour_ci95'][0]:.2f}, {s['per_hour_ci95'][1]:.2f}] |"
        )
    t = record["training"]
    lines += [
        "",
        "## Training record",
        "",
        f"- Head: flatten(16x96) -> {HIDDEN[0]} -> {HIDDEN[1]} -> sigmoid, scikit-learn MLP, seed {SEED}, "
        f"{t['epochs']} epochs, class-balanced weights with adversarial negatives x{ADVERSARIAL_WEIGHT:g}; "
        "scaler folded into the first ONNX layer.",
        f"- Train windows: {json.dumps(t['windows'])}",
        f"- Keyword length known exactly for {t['exact_bases']} / {t['bases']} bases; fit residual on "
        f"those {t['fit_residual_s'] * 1000:.0f} ms (fitted bases use a {MARGIN_FITTED_S * 1000:.0f} ms margin).",
        f"- ONNX vs scikit-learn max |diff| on val windows: {json.dumps(t['export_max_abs_diff'])}",
        "",
        "## Read before quoting",
        "",
        "- **Every positive is Piper TTS, three voices.** Split is by base rendition, so test voices are "
        "the same three voices as train. FRR on the author's own voice is not measured here.",
        "- **NFR-15 is the ambient rows.** The near-miss rows are authored phrases (`abort`, "
        "`hold on`, `is the swarm holding`) packed back to back; their per-hour rate is a stress figure, not "
        "an operating rate. A false `abort` on the word `abort` is also fail-safe by prd.md SS4.2.",
        f"- **The operating point sits at the top of the grid ({THRESHOLDS[-1]:.3f}).** The MLP's scores "
        "saturate, so the threshold does little work and the head's own decision boundary does the rest; "
        "a calibrated head (or a logit-space sweep) is the fix if the operating point has to move.",
        "- **The head was fitted twice.** Round one scored test once and was rejected on its val "
        "diagnostics (every val false accept was an authored near-miss); round two upweighted those "
        "negatives in the loss. Test has therefore been seen twice; no third round was run.",
        "- **The held-out negative stream is short.** NFR-15 is <= 1 per hour; zero events over the test "
        "stream still leaves the upper bound in the CI column, and that bound is the honest statement.",
        "- The golden-set row is the author reading Branch B commands, including `hold position` and "
        "`abort abort`: real voice, real room, and the nearest near-misses this project has.",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines))


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--refeature", action="store_true", help="recompute the cached embeddings")
    parser.add_argument("--report", action="store_true", help="rewrite the .md from the saved .json only")
    args = parser.parse_args(argv)
    if args.report:
        write_report(json.loads(REPORT_JSON.read_text()))
        print(REPORT_MD.read_text())
        return 0

    manifest = json.loads(MANIFEST.read_text())
    clips = manifest["clips"]
    spans = keyword_spans(clips)
    exact_bases = {c["base"] for c in clips if c["label"] != "neg" and spans[c["path"]][2]}

    print("embedding the corpus")
    embeddings = embed_corpus(clips, args.refeature)

    training = {"epochs": 0, "windows": {}, "export_max_abs_diff": {}, "bases": len({c["base"] for c in clips if c["label"] != "neg"}),
                "exact_bases": len(exact_bases), "fit_residual_s": fit_residual(clips)}
    for name, label in CLASSES.items():
        x, y, w = window_dataset(clips, embeddings, spans, label, "train")
        print(f"{name}: {len(y)} train windows, {int(y.sum())} positive")
        scaler, mlp = fit_head(x, y, w)
        path = OUT_DIR / f"{name}.onnx"
        export_onnx(scaler, mlp, path)
        xv, _, _ = window_dataset(clips, embeddings, spans, label, "val")
        training["export_max_abs_diff"][name] = check_export(scaler, mlp, path, xv)
        training["windows"][name] = {"total": int(len(y)), "positive": int(y.sum())}
        training["epochs"] = int(mlp.n_iter_)

    print("streaming evaluation through openwakeword.Model")
    model = _model()
    traces = {split: positive_traces(model, clips, spans, split) for split in ("val", "test")}
    streams = {(split, group): negative_stream(clips, split, group == "ambient")
               for split in ("val", "test") for group in ("ambient", "near_miss")}
    neg_traces = {split: stream_scores(model, audio) for split, audio in streams.items()}

    # Operating point: val only.
    chosen = None
    for thr in THRESHOLDS:
        if all(v <= VAL_FRR_TARGET for v in score_positives(traces["val"], thr)["frr"].values()):
            chosen = float(thr)
    if chosen is None:
        raise SystemExit(f"no threshold keeps val FRR <= {VAL_FRR_TARGET} for both classes")

    golden = golden_stream()
    record = {
        "threshold": chosen,
        "selection_rule": f"highest threshold with val FRR <= {VAL_FRR_TARGET} for both classes",
        "training": training,
        "golden": score_stream(stream_scores(model, golden), golden.size, chosen),
    }
    for split in ("val", "test"):
        record[split] = {"positives": score_positives(traces[split], chosen)}
        for group in ("ambient", "near_miss"):
            record[split][group] = score_stream(neg_traces[(split, group)], streams[(split, group)].size, chosen)
    record["roc"] = {
        split: [{"threshold": float(t),
                 "frr": score_positives(traces[split], t)["frr"],
                 "fa_per_hour_ambient": score_stream(neg_traces[(split, "ambient")],
                                                     streams[(split, "ambient")].size, t)["per_hour"]}
                for t in THRESHOLDS]
        for split in ("val", "test")
    }

    fm = feature_model_paths()
    heads = {
        "threshold": chosen,
        "debounce_s": DEBOUNCE_S,
        "classes": list(CLASSES),
        "heads": {name: {"file": f"{name}.onnx", "sha256": _sha256(OUT_DIR / f"{name}.onnx")} for name in CLASSES},
        "feature_models": {k: {"file": p.name, "sha256": _sha256(p),
                               "source": "https://github.com/dscripka/openWakeWord/releases/tag/v0.5.1"}
                           for k, p in fm.items()},
        "corpus_manifest_sha256": _sha256(MANIFEST),
        "report": str(REPORT_MD.relative_to(REPO)),
    }
    (OUT_DIR / "wake_heads.json").write_text(json.dumps(heads, indent=2) + "\n")
    REPORT_JSON.write_text(json.dumps(record, indent=2, default=float) + "\n")
    write_report(record)
    print(REPORT_MD.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
