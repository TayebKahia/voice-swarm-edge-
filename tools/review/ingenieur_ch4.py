#!/usr/bin/env python3
"""Pre-review checks for Ingénieur Ch4 (Implementation). See tools/review/lib.py.

Ch4 describes the system as built and promises "every figure in this chapter is a parameter of the
code, not a measurement". Its sources are therefore the modules it describes, not results/:
  - 4.1 audio chain against runtime/stream.py, runtime/vad.py (and the silero-vad default it departs
    from), runtime/branch_a.py, train/train_wake.py, runtime/models/wake/wake_heads.json and the
    wake corpus manifest;
  - 4.2 runtime against runtime/parser.py, runtime/pipeline.py, runtime/stt.py, eval/surface_b.py
    (the accuracy harness whose request the runtime copies) and eval/exp2.py (the only assembler);
  - 4.3 bus against runtime/bus.py and the Dispatcher;
  - 4.4 state machine against swarm/fsm.py (the raw-intent defect is probed, not read);
  - 4.5 controller against swarm/control.py and swarm/simulate.py (the clamp is exercised);
  - 4.6 backends against swarm/env.py, swarm/pyflyt_env.py and swarm/test_pyflyt.py.
The swarm/ and schema/ modules are imported (numpy/scipy only); runtime/ constants are read as text,
because runtime/ imports pull in onnxruntime and the parser reads files at import time.
It also enforces the chapter's own promise: no measured value from results/ or thesis/generated/.
"""

import math
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import INGENIEUR, REPO, RESULTS, THESIS, Review, numbers, outline_check, significant  # noqa: E402

sys.path.insert(0, str(REPO))
import json  # noqa: E402

import numpy as np  # noqa: E402

import schema.schema as schema  # noqa: E402
from schema.schema import INTENTS  # noqa: E402
from schema.validate import validate  # noqa: E402
from swarm import control, env as swarm_env, simulate  # noqa: E402
from swarm.fsm import TABLE_9_LEGALITY, FlightState, FlightStateMachine  # noqa: E402
from swarm.pyflyt_env import PHYSICS_HZ, PyFlytEnv  # noqa: E402

r = Review("ingenieur_ch4", "ingenieur", INGENIEUR[3], [*INGENIEUR[:3], *INGENIEUR[4:]])
r.common()
text = r.ch.text
params: set[float] = set()   # every value a claim recomputed: the promise check exempts them


def code(path: str, pattern: str, group: int = 1) -> str:
    """Group of `pattern` in a source file (read as text, not imported)."""
    m = re.search(pattern, (REPO / path).read_text(encoding="utf-8"), flags=re.M | re.S)
    if not m:
        r.add("FAIL", "source", f"`{pattern}` not found in {path} -- the code moved; update the script")
        return "nan"
    return m.group(group)


def src(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def number(anchor: str, computed: float, source: str, **kw) -> None:
    params.add(round(float(computed), 6))
    r.number(anchor, computed, source, **kw)


def fact(check: str, anchor: str, ok: bool, message: str, warn: bool = False) -> None:
    r.text_claim(check, anchor, ok, message, warn=warn)


def judge(check: str, anchor: str, evidence: bool, message: str) -> None:
    """A point the script can locate and source but not decide: always a WARN for the agents.
    `evidence` must hold (the source says what the message says), or the script is stale."""
    if not evidence:
        r.add("FAIL", "source", f"evidence for `{anchor}` no longer in the code -- update the script")
    else:
        r.text_claim(check, anchor, False, message, warn=True)


# -- Outline and labels ------------------------------------------------------------------------------
outline_check(r, 3, {"the audio chain": r"audio chain", "the runtime": r"^runtime$", "the command bus": r"command bus",
                     "the flight state machine": r"state machine", "the swarm controller": r"swarm controller",
                     "the simulation backends": r"simulation backends"})
r.expect("label", "\\label{chap:implementation}" in text, "carries \\label{chap:implementation}")
order = [t for lvl, t, _ in r.ch.sections() if lvl == "section"]
want = ["Audio chain", "Runtime", "Command bus", "Flight state machine", "Swarm controller", "Simulation backends"]
r.expect("outline", order == want, f"sections in Ch1's announced order: {order}" if order == want
         else f"section order {order} differs from Ch1's structure paragraph {want}")

# -- "Not built": each absence still true ----------------------------------------------------------
for path, what in (("runtime/audio.py", "live capture"), ("runtime/main.py", "an entry point")):
    r.expect("not-built", not (REPO / path).exists(), f"{path} absent: '{what}' is still correctly 'not built'"
             if not (REPO / path).exists() else f"{path} now exists -- Ch4 says {what} is not built; describe it")
swarm_importers = [p.name for p in (REPO / "swarm").glob("*.py")
                   if not p.name.startswith("test_") and p.name != "fsm.py"
                   and re.search(r"^\s*(?:from|import)\s+\S*fsm\b", p.read_text(), flags=re.M)]
r.expect("not-built", not swarm_importers, "no swarm/ module imports the state machine (the link is not built)"
         if not swarm_importers else f"swarm/ modules now import fsm: {swarm_importers} -- Ch4 4.4 says no link exists")
assemblers = [str(p.relative_to(REPO)) for p in [*(REPO / "eval").glob("*.py"), *(REPO / "runtime").glob("*.py")]
              if "StreamLoop(" in p.read_text(encoding="utf-8") and not p.name.startswith("test_") and p.name != "stream.py"]
r.expect("not-built", assemblers == ["eval/exp2.py"], f"only {assemblers} assembles the runtime (StreamLoop)"
         if assemblers == ["eval/exp2.py"] else f"StreamLoop assembled by {assemblers} -- re-check 'only the harness'")

# -- 4.1 Audio chain -------------------------------------------------------------------------------
rate = int(code("runtime/vad.py", r"^RATE = ([\d_]+)").replace("_", ""))
frame = int(code("runtime/stream.py", r"^FRAME = (\d+)"))
window = int(code("runtime/vad.py", r"^WINDOW = (\d+)"))
context = int(code("runtime/vad.py", r"^CONTEXT = (\d+)"))
number("80~ms frames of 1{,}280 samples at 16~kHz", frame / rate * 1000, "runtime/stream.py FRAME / RATE", nth=0)
number("80~ms frames of 1{,}280 samples at 16~kHz", frame, "runtime/stream.py FRAME", nth=1)
number("80~ms frames of 1{,}280 samples at 16~kHz", rate / 1000, "runtime/vad.py RATE", nth=2)
fact("audio", "The only source built replays a recorded 16~kHz file",
     bool(re.search(r"class WavSource", src("runtime/stream.py"))) and "t_due = self.t_start + (i + 1) * FRAME_S" in src("runtime/stream.py"),
     "WavSource is the only frame source; each frame released at t_start + (i+1)*FRAME_S")
number("the quantisation of audio into 80~ms frames", frame / rate * 1000, "FRAME / RATE")
fact("audio", "pinned to core~0", code("eval/exp2.py", r"^FRONT = (\{[^}]*\})") == "{0}", "eval/exp2.py FRONT = {0}")
fact("audio", "by a worker thread pinned to cores~1--3", code("eval/exp2.py", r"^BACK = (\{[^}]*\})") == "{1, 2, 3}",
     "eval/exp2.py BACK = {1, 2, 3}")
fact("audio", "Each frame is passed to the keyword spotter and then to the endpointer",
     src("runtime/stream.py").find("on_wake_frame(frame)") < src("runtime/stream.py").find("self._endpointer.feed(frame)"),
     "StreamLoop.run: spotter before endpointer, same thread")
fact("audio", "writes it as a 16~kHz mono file", "f.setnchannels(1)" in src("runtime/vad.py"), "Utterance.to_wav: mono, RATE")
fact("audio", "the loop subtracts the remainder",
     "t0_wall = t_due - (delivered / RATE - utterance.t0_s)" in src("runtime/stream.py"), "stream.py t0_wall")
number("windows of 512 samples (32~ms)", window, "runtime/vad.py WINDOW", nth=0)
number("windows of 512 samples (32~ms)", window / rate * 1000, "WINDOW / RATE", nth=1)
number("each preceded by the last 64 samples", context, "runtime/vad.py CONTEXT")
number("A frame of 1{,}280 samples is not a whole number of windows", frame, "FRAME")
r.expect("audio", frame % window != 0, f"{frame} % {window} = {frame % window}: a frame is not a whole number of windows")
fact("audio", "The model runs on a single thread", "intra_op_num_threads = 1" in src("runtime/vad.py"), "SileroVAD intra_op 1")
thr = float(code("runtime/vad.py", r"threshold: float = ([\d.]+)"))
hyst = float(code("runtime/vad.py", r"prob < self\._threshold - ([\d.]+)"))
number("probability reaches 0.5", thr, "runtime/vad.py Endpointer threshold default")
number("stayed below 0.35", thr - hyst, "threshold - hysteresis in Endpointer._step")
number("the gap of 0.15 between", hyst, "runtime/vad.py hysteresis")
silero = next(Path(sys.prefix).glob("lib/python*/site-packages/silero_vad/utils_vad.py"), None)
if silero:
    sil = silero.read_text(encoding="utf-8")
    r.expect("audio", "threshold - 0.15" in sil, "the 0.15 hysteresis is Silero's own (utils_vad.py neg_threshold)")
    number("in place of Silero's default of 30~ms", int(re.search(r"speech_pad_ms: int = (\d+)", sil).group(1)),
           "silero_vad utils_vad.py speech_pad_ms default")
else:
    r.add("WARN", "source", "silero_vad package not found in this env -- Silero's 30 ms default unchecked")
silence = int(code("runtime/vad.py", r"min_silence_ms: int = (\d+)"))
pad = int(code("runtime/vad.py", r"speech_pad_ms: int = (\d+)"))
number("silence threshold of 450~ms derived", silence, "runtime/vad.py min_silence_ms")
number("padded by 200~ms at both ends", pad, "runtime/vad.py speech_pad_ms")
number("lies within the 450~ms of silence", silence, "runtime/vad.py min_silence_ms")
fact("audio", "the endpointer refuses a pad longer than the silence",
     "if speech_pad_ms > min_silence_ms:" in src("runtime/vad.py"), "Endpointer.__init__ raises if pad > silence")
number("An utterance still open after 15~s", float(code("runtime/vad.py", r"max_utterance_s: float = ([\d.]+)")),
       "runtime/vad.py max_utterance_s")
fact("audio", "closed by force and marked", "forced=True" in src("runtime/vad.py"), "Utterance.forced")

tw = src("train/train_wake.py")
head_frames = int(code("train/train_wake.py", r"^HEAD_FRAMES = (\d+)"))
emb_dim = int(code("train/train_wake.py", r"\[batch, 16, (\d+)\]"))
window_s = float(code("train/train_wake.py", r"^WINDOW_S = ([\d.]+)"))
number("one 96-dimensional speech embedding per 80~ms frame", emb_dim, "train/train_wake.py [batch, 16, 96]", nth=1)
number("one 96-dimensional speech embedding per 80~ms frame", float(code("train/train_wake.py", r"^EMB_HOP_S = ([\d.]+)")) * 1000,
       "train_wake.py EMB_HOP_S", nth=2)
number("each head scores the last 16 embeddings", head_frames, "train_wake.py HEAD_FRAMES")
number("which span about two seconds of audio", window_s, "train_wake.py WINDOW_S", tol=0.1)
ba = src("runtime/branch_a.py")
deb_rt = float(code("runtime/branch_a.py", r"debounce_s: float = ([\d.]+)"))
deb_tr = float(code("train/train_wake.py", r"^DEBOUNCE_S = ([\d.]+)"))
number("lies more than 1.0~s earlier", deb_rt, "runtime/branch_a.py BranchA debounce_s default")
number("with the same 1.0~s rule as the runtime's debounce", deb_tr, "train/train_wake.py DEBOUNCE_S")
r.expect("spotter", deb_rt == deb_tr, f"runtime debounce {deb_rt} s = evaluation debounce {deb_tr} s")
# Behaviour: frames at 0.08 s, so "more than 1.0 s" = at least 13 frames; runtime and trainer count alike.
refr = int(round(deb_rt / 0.08))
r.expect("spotter", refr == int(round(deb_tr / (frame / rate))) and 12 * 0.08 < 1.0 < 13 * 0.08,
         f"refractory {refr} frames in both: a re-trigger needs a gap of {refr + 1} frames ({(refr + 1) * 0.08:.2f} s) > 1.0 s")
fact("spotter", "The refractory interval is kept per class",
     "self._last_above: dict[str, int | None] = {c: None for c in BRANCH_A_CLASSES}" in ba, "BranchA._last_above keyed by class")
fact("spotter", "the higher score wins", "if score >= best_score:" in ba, "BranchA.poll keeps the best score above threshold")
fact("spotter", "A trigger cancels the decode in progress, if any, and publishes",
     re.search(r"self\.parser\.abort\(\)\s+return self\.bus\.publish\(\"A\", command\)", src("runtime/pipeline.py")) is not None,
     "PipelineRuntime.on_wake_frame: abort() then publish")
fact("spotter", "checked when the module is loaded", "assert set(KEYWORD_TO_INTENT.values()) == {\"hover\", \"abort\"}" in ba,
     "branch_a.py import-time assert on the mapping")
fact("spotter", "loaded only if their files match the hashes", "hashlib.sha256(path.read_bytes())" in ba, "load_trained hash check")

hidden = tuple(int(x) for x in code("train/train_wake.py", r"^HIDDEN = \(([\d, ]+)\)").split(","))
number("two hidden layers of 128", len(hidden), "train_wake.py HIDDEN", nth=0)
number("two hidden layers of 128", hidden[0], "train_wake.py HIDDEN", nth=1)
r.expect("spotter", len(set(hidden)) == 1, f"both hidden layers are {hidden[0]} units ({hidden})")
fact("spotter", "rectified linear units and a sigmoid output", 'activation="relu"' in tw and "sigmoid" in tw.lower(),
     "MLPClassifier relu; ONNX sigmoid output")
fact("spotter", "fitted with scikit-learn", "from sklearn.neural_network import MLPClassifier" in tw, "train_wake.py fit_head")
manifest = json.loads((REPO / "data/wake/wake_manifest.json").read_text(encoding="utf-8"))
clips = manifest["clips"]
voices = {c["voice"] for c in clips if c.get("source") == "piper"}
number("synthetic positives rendered by three", len(voices), f"data/wake/wake_manifest.json Piper voices {sorted(voices)}")
train_neg = [c for c in clips if c["split"] == "train" and c["label"] == "neg"]
adv = [c for c in train_neg if c.get("source") == "adversarial"]
share = 100 * len(adv) / len(train_neg)
all_neg = [c for c in clips if c["label"] == "neg"]
all_share = 100 * sum(c.get("source") == "adversarial" for c in all_neg) / len(all_neg)
number("the hand-written near-misses, 12\\% of the negative clips of the training split", share,
       f"wake_manifest.json train split: {len(adv)} adversarial / {len(train_neg)} negative clips",
       note=f"the share over ALL splits is {all_share:.1f}%; per head the other class's clips are negatives too")
number("five times more than other negatives", float(code("train/train_wake.py", r"^ADVERSARIAL_WEIGHT = ([\d.]+)")),
       "train_wake.py ADVERSARIAL_WEIGHT")
number("by a margin, 40~ms where the phrase's length", 1000 * float(code("train/train_wake.py", r"^MARGIN_EXACT_S = ([\d.]+)")),
       "train_wake.py MARGIN_EXACT_S")
number("450~ms where it was predicted", 1000 * float(code("train/train_wake.py", r"^MARGIN_FITTED_S = ([\d.]+)")),
       "train_wake.py MARGIN_FITTED_S")
fact("spotter", "a window that cuts the phrase is discarded",
     "contains = start <= onset - 0.01 and end >= kw_end + margin" in tw, "window_dataset: positive only past kw_end + margin")
fit = tw[tw.find("def fit_head"):tw.find("mlp.fit(")]
fact("spotter", "scikit-learn's Adam optimiser", "solver=" not in fit, "MLPClassifier solver left at its default, adam")
# $10^{-3}$ is read by the number tokenizer as 10, so these two are exact-value facts.
fact("spotter", "with L2 regularisation of $10^{-3}$", float(code("train/train_wake.py", r"alpha=([\de.-]+),")) == 1e-3,
     "fit_head alpha=1e-3")
fact("spotter", "a learning rate of $10^{-3}$",
     float(code("train/train_wake.py", r"learning_rate_init=([\de.-]+),")) == 1e-3, "fit_head learning_rate_init=1e-3")
number("batches of 256 and at most 40", float(code("train/train_wake.py", r"batch_size=(\d+),")), "fit_head batch_size", nth=0)
number("batches of 256 and at most 40", float(code("train/train_wake.py", r"max_iter=(\d+),")), "fit_head max_iter", nth=1)
fact("spotter", "on standardised inputs and with seed 42", "StandardScaler().fit(x)" in fit and "random_state=SEED" in fit,
     "fit_head: StandardScaler, random_state=SEED")
number("on standardised inputs and with seed 42", float(code("train/train_wake.py", r"^SEED = (\d+)")), "train_wake.py SEED")
fact("spotter", "feature models of openWakeWord's v0.5.1 release",
     "openWakeWord/releases/tag/v0.5.1" in src("runtime/models/wake/wake_heads.json"), "wake_heads.json feature_models source")
fact("spotter", "Each head treats the other class as a negative",
     re.search(r'if clip\["label"\] == target:', tw) is not None, "window_dataset: only the target class yields positives")
fact("spotter", "a window that cuts the phrase is discarded", "continue  # cuts the phrase" in tw, "window_dataset skip")
wt = (RESULTS / "wake_training.md").read_text(encoding="utf-8")
fact("spotter", "the held-out test split was scored twice", "Test has therefore been seen twice" in wt,
     "results/wake_training.md 'The head was fitted twice ... Test has therefore been seen twice'")
fact("spotter", "false accepts on the validation split were all near-misses",
     "every val false accept was an authored near-miss" in wt, "results/wake_training.md round-one record")

grid = np.concatenate([np.round(np.arange(0.05, 0.991, 0.01), 2), [0.995, 0.998, 0.999]])
r.expect("spotter", "THRESHOLDS = np.concatenate([np.round(np.arange(0.05, 0.991, 0.01), 2), [0.995, 0.998, 0.999]])" in tw,
         "THRESHOLDS literal as reconstructed here")
grid_anchor = "from 0.05 to 0.99 in steps of 0.01 and then 0.995, 0.998 and 0.999"
for i, v in enumerate((grid[0], grid[-4], round(grid[1] - grid[0], 2), grid[-3], grid[-2], grid[-1])):
    number(grid_anchor, float(v), "train_wake.py THRESHOLDS", nth=i)
frr_target = float(code("train/train_wake.py", r"^VAL_FRR_TARGET = ([\d.]+)"))
number("false-reject rate of at most 0.05 on the validation split", frr_target, "train_wake.py VAL_FRR_TARGET")
fact("spotter", "It is the highest value on a grid", "chosen = float(thr)" in tw and "for thr in THRESHOLDS:" in tw,
     "train_wake.py: ascending loop keeps the last passing threshold = the highest")
ch1 = (THESIS / "ingenieur/ch1_introduction.tex").read_text(encoding="utf-8")
m = re.search(r"^Keyword false rejects & .*?\$\\leq\$ ([\d.]+)", ch1, flags=re.M)
number("half the budget of 0.10", float(m.group(1)) if m else -1, "Ch1 tab:nonfunctional-requirements Keyword false rejects")
r.expect("spotter", m is not None and abs(2 * frr_target - float(m.group(1))) < 1e-9,
         f"VAL_FRR_TARGET {frr_target} is half of Ch1's {m.group(1) if m else '?'}")
val_counts = {lab: sum(1 for c in clips if c["split"] == "val" and c["label"] == lab) for lab in ("pos_swarm_hold", "pos_swarm_abort")}
number("as a margin for a split of 150 clips per class", min(val_counts.values()), f"wake_manifest.json val {val_counts}")
r.expect("spotter", len(set(val_counts.values())) == 1, f"both classes have the same val count {val_counts}")
heads = json.loads((REPO / "runtime/models/wake/wake_heads.json").read_text(encoding="utf-8"))
number("The rule selected 0.999, the top of the grid", heads["threshold"], "runtime/models/wake/wake_heads.json threshold")
r.expect("spotter", heads["threshold"] == float(grid[-1]), f"0.999 = THRESHOLDS[-1] = {grid[-1]}: the top of the grid")
fact("spotter", "it was applied before the test split of the second fit was scored",
     "selected on **val** by the rule declared in the script before test was scored" in wt,
     "results/wake_training.md: rule declared before test scored")
fact("spotter", "the exported heads through openWakeWord in 80~ms frames", "streaming, 80 ms frames, `openwakeword.Model`" in wt,
     "results/wake_training.md evaluation runs openwakeword.Model on 80 ms frames")

# -- 4.2 Runtime -----------------------------------------------------------------------------------
pl, pa, sb = src("runtime/pipeline.py"), src("runtime/parser.py"), src("eval/surface_b.py")
proc = pl[pl.find("def process"):]
fact("runtime", "reserves a sequence number from the bus, transcribes the audio",
     0 < proc.find("self.bus.next_seq()") < proc.find("transcribe_utterance(") < proc.find("self.parser.parse(")
     < proc.find("validate(result.raw)") < proc.find('self.bus.publish("B", command, seq=seq)'),
     "PipelineRuntime.process: next_seq -> transcribe -> parse -> validate -> publish(seq)")
fact("runtime", "with the \\texttt{tiny.en} model, three threads",
     "ggml-tiny.en.bin" in src("data/harvest_asr_garbage.py") and int(code("runtime/pipeline.py", r"stt_threads: int = (\d+)")) == 3,
     "find_whisper models/ggml-tiny.en.bin; PipelineRuntime stt_threads = 3")
fact("runtime", "an initial prompt that lists the command vocabulary", "prompt=DOMAIN_PROMPT" in src("runtime/stt.py"),
     "runtime/stt.py passes data/asr.py DOMAIN_PROMPT")
fact("runtime", "The invocation is defined once and shared", "from data.asr import" in src("runtime/stt.py"),
     "runtime/stt.py wraps data/asr.py's transcribe()")
fact("runtime", "A recognition failure returns an empty transcript", 'return result.text if result.ok else ""' in src("runtime/stt.py"),
     "transcribe_utterance returns '' on failure")
number("a single decoding slot, three threads and a context of 512 tokens",
       int(code("runtime/parser.py", r"^DEFAULT_THREADS = (\d+)")), "runtime/parser.py DEFAULT_THREADS", nth=0)
number("a single decoding slot, three threads and a context of 512 tokens",
       int(code("runtime/parser.py", r"^DEFAULT_CONTEXT = (\d+)")), "runtime/parser.py DEFAULT_CONTEXT", nth=1)
fact("runtime", "a single decoding slot", '"--parallel", "1"' in pa, "LlamaServerProcess --parallel 1")
parse_fn = pa[pa.find("def parse"):]
posts = re.findall(r'self\._post\(\s*"(/[\w-]+)"', parse_fn)
number("Each parse makes three requests", len(posts), f"CommandParser.parse posts {posts}")
fact("runtime", "without adding special tokens", '"add_special": False' in parse_fn, "/tokenize add_special False")
number("greedily and with at most 96 tokens", int(code("runtime/parser.py", r"^DEFAULT_MAX_TOKENS = (\d+)")),
       "runtime/parser.py DEFAULT_MAX_TOKENS")
r.expect("runtime", '"temperature": 0.0' in parse_fn, "completion at temperature 0.0 (greedy)")
sb_max = int(code("eval/surface_b.py", r"^MAX_TOKENS = (\d+)"))
sb_order = [p for p in ("/apply-template", "/tokenize", "/completion") if p in sb]
fact("runtime", "This is the request sequence of the harness that measures the parser's accuracy",
     posts == ["/apply-template", "/tokenize", "/completion"] and sb_order == posts and sb_max == 96
     and bool(re.search(r'"cache_prompt": False', sb)),
     "eval/surface_b.py: same three endpoints, MAX_TOKENS 96, cache_prompt False")
fact("runtime", "read from the server's own timing report", '"prompt_ms"' in pa and '"predicted_ms"' in pa,
     "ParseResult prefill_ms/decode_ms from timings.prompt_ms/predicted_ms")
fact("runtime", "the wall-clock time of the whole request is recorded beside them",
     "return (self.t_parsed - self.t_transcribed) * 1000" in pl, "BranchBTrace.parse_wall_ms spans the three requests")
fact("runtime", "each completion request disables the server's prompt cache", '"cache_prompt": False' in parse_fn,
     "runtime/parser.py /completion cache_prompt False")
fact("runtime", "closes the connection of the parser's request in flight, if there is one",
     "conn.sock.shutdown(socket.SHUT_RDWR)" in pa and "if conn is not None and conn.sock is not None" in pa,
     "CommandParser.abort: shutdown of the in-flight socket; no-op otherwise (V3 in Ch3)")
fact("runtime", "The parser treats a failed request as an interrupted decode",
     "except (OSError, ValueError, KeyError) as exc:" in parse_fn,
     "parse raises ParseAborted on OSError (connection, timeout), ValueError (not JSON) and KeyError "
     "(no prompt/tokens in the first two replies)")
fact("runtime", "An error answer to the completion request is not treated so",
     'data.get("content", "")' in parse_fn,
     "a /completion reply without `content` yields '', which validate() resolves to a hold, and it is published")
fact("runtime", "The sequence number is reserved when the worker takes the utterance, before transcription starts",
     "while (item := work.get()) is not None:" in src("runtime/stream.py"),
     "the worker dequeues, then process() reserves: matches Ch3 V2 (number at dequeue)")
ex = src("eval/exp2.py")
fact("runtime", "The language-model server is started from a thread restricted to cores~1--3",
     re.search(r"pin\(BACK\)\s+parser, server = CommandParser\.for_gguf\(GGUF, port=PORT\)\s+pin\(FRONT\)", ex) is not None,
     "eval/exp2.py: pin(BACK), start llama-server, pin(FRONT)")
fact("runtime", "The worker restricts itself to cores~1--3", "def _worker" in src("runtime/stream.py")
     and "pin(self._back)" in src("runtime/stream.py"), "StreamLoop._worker pins itself to back_cores")
# The harness records the server's threads (task_affinity walks /proc/pid/task) and the frame-loop thread,
# and the loader's; the worker thread's own mask is not recorded.
fact("runtime", "the worker's own restriction, and so that of the recogniser processes it starts, is applied by the code but not recorded",
     "Cpus_allowed_list" in ex and "worker_affinity" not in ex and "branch-b" not in ex,
     "eval/exp2.py records llama_server_affinity (every thread, at server start), main_affinity (frame loop) and "
     "loader_affinity; nothing reads the worker thread's mask back")
fact("runtime", "Qwen2.5-0.5B fine-tuned and quantised to Q4\\_K\\_M", "q4_k_m" in src("eval/exp3.py").lower(),
     "eval/exp3.py GGUF is the Q4_K_M artefact")
fact("runtime", "The runtime adds no prompt text and no grammar rule of its own",
     "SYSTEM_PROMPT: str = json.loads(AUDIT_PROMPTS_PATH" in pa and "grammar_path: Path = GRAMMAR_PATH" in pa,
     "parser takes the system prompt from eval/fixed_audit_prompts.json and the grammar from schema")

# -- 4.3 Command bus -------------------------------------------------------------------------------
bus = src("runtime/bus.py")
bus_cls = bus[bus.find("class CommandBus"):]
ops = [n for n in re.findall(r"^    def (\w+)\(", bus_cls, flags=re.M) if not n.startswith("_") and n != "close"]
r.expect("bus", ops == ["next_seq", "publish", "recv"], f"CommandBus public operations {ops} (plus close): three")
r.text_claim("bus", "No separate abstract type is declared", not re.search(r"\(\s*(?:ABC|Protocol)\s*\)", bus),
             "runtime/bus.py declares no ABC/Protocol (its docstring's 'abstract interface' is not in the code)")
number("A message longer than 4{,}096 bytes", int(code("runtime/bus.py", r"^MAX_DATAGRAM_BYTES = (\d+)")),
       "runtime/bus.py MAX_DATAGRAM_BYTES")
fact("bus", "sent as one \\gls{udp} datagram", "socket.SOCK_DGRAM" in bus, "CommandBus SOCK_DGRAM")
fact("bus", "rejects a message whose path tag is neither", 'if branch not in ("A", "B"):' in bus, "BusMessage.from_json")
fact("bus", "read from the publishing machine's monotonic clock", "t_publish=time.monotonic()" in bus, "publish stamps monotonic")
fact("bus", "guarded by a lock", "with self._seq_lock:" in bus, "next_seq under _seq_lock")
fact("bus", "The reflex path lets the publish operation draw the number", 'return self.bus.publish("A", command)' in pl,
     "on_wake_frame publishes without seq=")
fact("bus", "keeps the highest sequence number among the reflex-path messages",
     "elif msg.seq < self._highest_branch_a_seq:" in pl, "Dispatcher.apply: strict '<' against the highest reflex seq")
tp = src("runtime/test_pipeline.py")
fact("bus", "Unit tests exercise the rule in both directions",
     "def test_stale_branch_b_message_is_discarded_after_a_later_branch_a_trigger" in tp and "trigger-happy" in tp,
     "runtime/test_pipeline.py: stale discarded; later one applied")
fact("bus", "it has run only over the loopback", "The bus is loopback on the Pi" in (RESULTS / "exp2_analysis.md").read_text(),
     "results/exp2_analysis.md 'The bus is loopback on the Pi'")
ch3 = (THESIS / "ingenieur/ch3_architecture.tex").read_text(encoding="utf-8")
r.expect("cross-chapter", "The bus sits behind an interface" not in ch3,
         "Ch3 no longer says the bus 'sits behind an interface'" if "The bus sits behind an interface" not in ch3 else
         "Ch3 3.1 says 'The bus sits behind an interface'; Ch4 4.3 says no abstract type exists and the interface "
         "is the class's three operations -- consistent only if Ch3's 'interface' is read that way (judge)", warn=True)

# -- 4.4 Flight state machine ----------------------------------------------------------------------
number("Its five states, its transitions", len(FlightState), "swarm/fsm.py FlightState")
number("The 50 cells, five states by ten intents", len(FlightState) * len(INTENTS), "states x intents", nth=0)
number("The 50 cells, five states by ten intents", len(FlightState), "FlightState", nth=1)
number("The 50 cells, five states by ten intents", len(INTENTS), "schema INTENTS", nth=2)
number("A second test checks that all ten commands", len(INTENTS), "schema INTENTS")
number("all ten intents are sent to a state machine", len(INTENTS), "schema INTENTS")
fsm_src = src("swarm/fsm.py")
fact("fsm", "first run through the semantic validator by the state machine itself", "cmd = validate(cmd_input)" in fsm_src,
     "handle_command calls validate()")
fact("fsm", "applies four rules, in order",
     0 < fsm_src.find('if effective_intent == "unknown"') < fsm_src.find('if effective_intent == "abort"')
     < fsm_src.find("if self.is_legal(effective_intent, self.state)") < fsm_src.find('if self.is_legal("hover", self.state)'),
     "handle_command: unknown, abort, legal, rejection -- in that order")
fact("fsm", "not from a separate list of airborne states", "AIRBORNE_STATES =" not in fsm_src,
     "the rejection reads is_legal('hover'); no AIRBORNE_STATES list")
fact("fsm", "refuses the reset unless both hold", "if all_ground_contact and all_near_zero_velocity:" in fsm_src,
     "manual_reset requires both reports")
mut = subprocess.run(["git", "log", "-1", "--format=%b", "bb151c3"], cwd=REPO, capture_output=True, text=True).stdout
faults = re.findall(r"\((\d+) failed\)", mut)
number("three faults were introduced", len(faults), f"commit bb151c3 (test_fsm Gate 4): mutations {faults} tests failed")
# The defect, probed: legality judged on the pre-validation intent.
probe = FlightStateMachine(FlightState.LANDING).handle_command({"intent": "set_param"})
fact("fsm", "a \\texttt{set\\_param} carrying no value, received during a landing, is replaced by a hold and dispatched",
     getattr(probe, "intent", None) == "hover" and FlightState.LANDING not in TABLE_9_LEGALITY["hover"],
     f"FlightStateMachine(LANDING).handle_command({{'intent':'set_param'}}) -> {probe!r}; hover illegal in LANDING")
reflex_ok = all(validate({"intent": i}).intent == i for i in ("hover", "abort"))
fact("fsm", "the reflex path publishes constants that the validator leaves unchanged", reflex_ok,
     "validate({'intent':'hover'|'abort'}) keeps the intent")
fact("fsm", "the harness itself places each trial's state machine in \\texttt{FLYING}",
     bool(re.search(r"def fly\(self\).*?handle_command\(\{\"intent\": \"takeoff\"\}\)\s+fsm\.on_altitude_reached\(\)", ex, flags=re.S)),
     "eval/exp2.py Subscriber.fly(): takeoff + on_altitude_reached -> FLYING per trial")

# -- 4.5 Swarm controller --------------------------------------------------------------------------
dt, n = swarm_env.DEFAULT_DT, swarm_env.DEFAULT_N
number("every 20~ms (50~Hz)", dt * 1000, "swarm/env.py DEFAULT_DT", nth=0)
number("every 20~ms (50~Hz)", 1 / dt, "1 / DEFAULT_DT", nth=1)
number("receives the positions and velocities of the five vehicles", n, "swarm/env.py DEFAULT_N")
number("It implements three of the six shapes", len(control.SHAPES), "swarm/control.py SHAPES", nth=0)
number("It implements three of the six shapes", len(schema.SHAPES), "schema/schema.py SHAPES", nth=1)
fact("controller", "the circle, the line and the wedge", set(control.SHAPES) == {"circle", "line", "wedge"},
     f"control.SHAPES = {control.SHAPES}")
fact("controller", "Its only command is a formation", [m for m in dir(control.SwarmController)
                                                        if not m.startswith("_") and callable(getattr(control.SwarmController, m))]
     == ["command", "step"], "SwarmController public methods: command (a formation) and step")
fact("controller", "which defaults to the swarm's current centroid", "centre = np.asarray(positions, dtype=float).mean(axis=0)"
     in src("swarm/control.py"), "SwarmController.command centre default")
fact("controller", "The controller applies no envelope of its own", "ENVELOPE" not in src("swarm/control.py")
     and "validate" not in src("swarm/control.py"), "swarm/control.py never reads schema ENVELOPE nor calls the validator")
fact("controller", "the formation-control experiment commands the controller directly",
     "controller.command(" in src("swarm/simulate.py") and "validate" not in src("swarm/simulate.py"),
     "swarm/simulate.py commands SwarmController without the validator")
number("The backends limit speed to 3~m/s, above the validator's ceiling of 2.0~m/s", swarm_env.EnvLimits().max_speed,
       "swarm/env.py EnvLimits.max_speed", nth=0)
number("The backends limit speed to 3~m/s, above the validator's ceiling of 2.0~m/s", schema.ENVELOPE["speed"][1],
       "schema ENVELOPE['speed'] upper bound", nth=1)
number("trailing at $30^\\circ$ either side", float(code("swarm/control.py", r"half_angle = np\.deg2rad\(([\d.]+)\)")),
       "control.py wedge half_angle")
w = control.formation_slots("wedge", n, (0.0, 0.0, 0.0))
r.expect("controller", np.allclose(w.mean(axis=0), 0.0), "the wedge is re-centred on its centroid (mean offset 0)")
fact("controller", "minimising the total squared distance", "linear_sum_assignment" in src("swarm/control.py"),
     "assign_slots: Hungarian on squared distance")
g = control.ControlGains()
number("gains $k_p = 2.0$", g.kp, "ControlGains.kp")
number("$k_i = 0.05$", g.ki, "ControlGains.ki")
number("$k_d = 3.0$", g.kd, "ControlGains.kd")
number("the integral is limited to $\\pm 2.0$~m\\,s", g.integral_limit, "ControlGains.integral_limit")
number("which is $2\\sqrt{k_p} \\approx 2.83$", 2 * math.sqrt(g.kp), "2 sqrt(kp)", nth=1)
r.expect("controller", g.kd > 2 * math.sqrt(g.kp), f"kd {g.kd} > 2 sqrt(kp) {2 * math.sqrt(g.kp):.2f}: above critical")
number("oscillates across the 0.5~m tolerance", simulate.SLOT_TOLERANCE, "swarm/simulate.py SLOT_TOLERANCE")
number("during the final 5~s of a trial", simulate.FINAL_WINDOW_SECONDS, "swarm/simulate.py FINAL_WINDOW_SECONDS")
number("repels each pair of vehicles closer than 1.5~m", g.separation_radius, "ControlGains.separation_radius")
number("$6.0\\,(1/d - 1/d_0)/d^2$", g.separation_gain, "ControlGains.separation_gain", nth=0)
number("an influence distance $d_0 = 1.5$~m", g.separation_radius, "ControlGains.separation_radius")
number("weighted at 0.15 towards the swarm's centroid", g.cohesion_gain, "ControlGains.cohesion_gain")
number("and 0.25 towards its mean velocity", g.alignment_gain, "ControlGains.alignment_gain")
number("the clamp finds every pair closer than 0.80~m", control.CLAMP_DISTANCE, "control.py CLAMP_DISTANCE")
number("so the clamp repeats the pass, up to 64 times",
       int(code("swarm/control.py", r"iterations: int = (\d+)")), "separation_clamp iterations default")
number("The clamp distance of 0.80~m is a choice", control.CLAMP_DISTANCE, "CLAMP_DISTANCE")
number("a pair closer than 0.35~m", control.COLLISION_DISTANCE, "control.py COLLISION_DISTANCE")
r.expect("controller", control.COLLISION_DISTANCE < control.CLAMP_DISTANCE, "collision distance < clamp distance")
# Exercise the clamp: a chain of three converges, the first pass alone is counted, approach speed removed.
chain = np.array([[0.0, 0, 2], [0.5, 0, 2], [1.0, 0, 2]])
vel = np.array([[1.0, 0, 0], [0, 0, 0], [-1.0, 0, 0]])
p2, v2, act = control.separation_clamp(chain, vel)
d = np.linalg.norm(p2[:, None] - p2[None], axis=2)[np.triu_indices(3, 1)]
r.text_claim("controller", "so the clamp repeats the pass", d.min() >= control.CLAMP_DISTANCE - 1e-6,
             f"separation_clamp on a chain of three: closest pair {d.min():.6f} m >= {control.CLAMP_DISTANCE} after the sweeps")
r.text_claim("controller", "counted on its first pass only", act == 2,
             f"chain of three: {act} interventions (the two pairs too close on entry; later sweeps not counted)")
closing = [float(np.dot(v2[i] - v2[j], (p2[i] - p2[j]) / np.linalg.norm(p2[i] - p2[j]))) for i, j in ((0, 1), (1, 2))]
r.text_claim("controller", "removes the approaching component", min(closing) >= -1e-6,
             f"after the clamp the adjacent pairs' closing speeds are {[round(c, 6) for c in closing]} (none approaching)")
same = np.array([[0.0, 0, 2], [0.0, 0, 2], [5.0, 0, 2]])
a1, _, _ = control.separation_clamp(same)
a2, _, _ = control.separation_clamp(same)
r.text_claim("controller", "separated along an axis chosen from their indices", np.array_equal(a1, a2)
             and np.linalg.norm(a1[0] - a1[1]) >= control.CLAMP_DISTANCE - 1e-6, "coincident pair: deterministic separation")
sim = src("swarm/simulate.py")
fact("controller", "The collisions are counted after the clamp",
     sim.find("separation_clamp(positions, velocities)") < sim.find("if closest < COLLISION_DISTANCE:"),
     "run_trial counts collisions after separation_clamp")
fact("controller", "The clamp rewrites the vehicles' state only on the kinematic backend",
     "if activations and isinstance(env, NumpyEnv):" in sim and "separation_clamp" not in src("swarm/test_pyflyt.py"),
     "run_trial writes back only for NumpyEnv; test_pyflyt applies no clamp")
loop = sim[sim.find("for tick in range(spec.ticks):"):]
fact("controller", "The controller then receives the corrected state",
     bool(re.search(r"accel = controller\.step\(positions, velocities\)\s+positions, velocities = env\.step\(accel\)\s+"
                    r"positions, velocities, activations = separation_clamp\(positions, velocities\)", loop)),
     "loop: step, env.step, clamp; the next tick's controller.step sees the clamped state")
m = re.search(r"^Collisions & .*? & (.*?) & ", ch1, flags=re.M)
quoted = "zero collisions observed across all trials, backed by a hard geometric separation clamp at the integrator"
r.expect("cross-chapter", bool(m) and m.group(1).lower() == quoted,
         f"Ch1 collision criterion reads `{m.group(1) if m else '?'}`; Ch4 quotes it as 'zero collisions observed across "
         "all trials, backed by a hard geometric separation clamp at the integrator' (near-verbatim: judge)", warn=True)

# -- 4.6 Simulation backends -----------------------------------------------------------------------
lim = swarm_env.EnvLimits()
number("advances the simulation by one control tick of 20~ms", dt * 1000, "DEFAULT_DT (kinematic backend)", nth=1)
steps = max(1, int(round(PHYSICS_HZ * dt)))
r.expect("backends", abs(steps / PHYSICS_HZ - dt) < 1e-9,
         f"one PyFlyt control tick is {steps}/{PHYSICS_HZ} s = {1000 * steps / PHYSICS_HZ:.2f} ms, not "
         f"{dt * 1000:g} ms: the interface's '20 ms tick' holds on the kinematic backend only", warn=True)
number("It limits the commanded acceleration to 4~m/s$^2$", lim.max_accel, "EnvLimits.max_accel")
number("the speed to 3~m/s", lim.max_speed, "EnvLimits.max_speed")
e = swarm_env.NumpyEnv(n=1)
e.reset(0)
e.set_state(np.zeros((1, 3)) + [0, 0, 2], np.zeros((1, 3)))
p, v = e.step(np.array([[1.0, 0, 0]]))
fact("backends", "the velocity is updated first, and the new velocity moves the position",
     abs(p[0, 0] - 1.0 * dt * dt) < 1e-12, f"NumpyEnv.step from rest with a = 1: x = {p[0, 0]:.6f} = a dt^2 (semi-implicit)")
big = swarm_env._clip_norm(np.array([[3.0, 4.0, 0.0]]), 1.0)
fact("backends", "Both limits scale the whole vector", np.allclose(big, [[0.6, 0.8, 0.0]]), "_clip_norm scales the row")
ne = swarm_env.NumpyEnv()
number("standard deviation 0.5~m about the point", ne.spawn_sigma, "NumpyEnv spawn_sigma")
fact("backends", "about the point $(0, 0, 2)$~m", tuple(ne.centroid) == (0.0, 0.0, 2.0), f"NumpyEnv centroid {tuple(ne.centroid)}")
number("The backend runs a 60~s trial of five", simulate.TrialSpec("circle", 0).duration_seconds, "TrialSpec.duration_seconds", nth=0)
number("The backend runs a 60~s trial of five", simulate.TrialSpec("circle", 0).n, "TrialSpec.n", nth=1)
fact("backends", "point-mass double integration", "NumpyEnv" in sim, "kinematic backend is point-mass double integration")
fact("backends", "five quadrotors in PyFlyt~0.29.0", "PyFlyt==0.29.0" in src("requirements.txt")
     and "pyflyt==0.29.0" in src("environment.yml"), "requirements.txt and environment.yml pin PyFlyt 0.29.0")
params.add(0.29)  # the version string, checked against the pins above
fact("backends", "they place the vehicles with seed 42", "def _fly(env, shape: str, seed: int = 42," in src("swarm/test_pyflyt.py"),
     "test_pyflyt._fly seed default 42, and no test passes another")
number("The physics runs at 240~Hz", PHYSICS_HZ, "swarm/pyflyt_env.py PHYSICS_HZ")
number("a whole number of physics steps, five", steps, "round(PHYSICS_HZ * DEFAULT_DT)")
tpy = src("swarm/test_pyflyt.py")
hover_s = float(code("swarm/test_pyflyt.py", r"^HOVER_SECONDS = ([\d.]+)"))
pe = PyFlytEnv()
pe.reset(0)
t0 = pe._aviary.elapsed_time
pe.step(np.zeros((pe.n, 3)))
tick_s = pe._aviary.elapsed_time - t0
pe.close()
updates_per_step = int(round(tick_s * PHYSICS_HZ / steps))
physics_steps_per_tick = steps * updates_per_step
number("each tick advances 10 physics steps", physics_steps_per_tick, "steps * updates_per_step (QuadX 120 Hz attitude loop)")
number("physics steps (41.67~ms), so the effective", tick_s * 1000, "simulated clock step duration in ms", places=2)
number("effective control rate is 24~Hz", 1 / tick_s, "1 / tick_s (simulated clock rate)")
number("rather than the nominal 48~Hz or 50~Hz", pe.effective_control_hz, "PyFlytEnv.effective_control_hz", nth=0)
number("rather than the nominal 48~Hz or 50~Hz", 1 / dt, "1 / DEFAULT_DT", nth=1)
ticks = round(hover_s / dt)
sim_s = ticks * tick_s
number("the 600 ticks evaluate 25~s", ticks, "ticks = round(HOVER_SECONDS / dt)", nth=0)
number("the 600 ticks evaluate 25~s", sim_s, "simulated seconds = ticks * tick_s", nth=1)
r.expect("backends", abs(tick_s - physics_steps_per_tick / PHYSICS_HZ) < 1e-9,
         f"one PyFlyt control tick advances {tick_s * 1000:.2f} ms of simulated time ({1 / tick_s:g} Hz), matching QuadX's {physics_steps_per_tick} physics steps")
pyf = src("swarm/pyflyt_env.py")
fact("backends", "sent to PyFlyt as a world-frame setpoint", "self._aviary.set_mode(6)" in pyf, "PyFlytEnv mode 6 (velocity)")
fact("backends", "subject to the same two limits as the kinematic backend",
     "_clip_norm(accel, self.limits.max_accel)" in pyf and "self.limits.max_speed)" in pyf, "PyFlytEnv clips accel and speed")
fact("backends", "yaw is not commanded", "0.0, target[index][2]" in pyf, "yaw-rate setpoint 0")
fact("backends", "The commanded velocity is held by the backend", "self._commanded_velocity = _clip_norm(" in pyf,
     "PyFlytEnv integrates its own commanded velocity")
fact("backends", "steady-state altitude droop", "test_pyflyt_does_not_sink_under_a_station_keeping_command" in tpy,
     "test guards against steady-state altitude droop")
number("(12~s at the nominal tick", hover_s, "test_pyflyt.py HOVER_SECONDS")
number("for 600 ticks (12~s", hover_s / 0.02, "HOVER_SECONDS / nominal 20 ms tick")
number("the test's 85\\% threshold with $N=5$", 100 * float(code("swarm/test_pyflyt.py", r">= (0\.\d+), f\"FA")),
       "test_pyflyt.py FA threshold", nth=0)
number("the test's 85\\% threshold with $N=5$", n, "SwarmEnv DEFAULT_N", nth=1)
number("within 0.5~m of their slots", float(code("swarm/test_pyflyt.py", r"^TOLERANCE = ([\d.]+)")), "test_pyflyt.py TOLERANCE")
fact("backends", "all five vehicles", ">= 0.85" in tpy, "85% on 5 vehicles requires all 5")
tests = re.findall(r"^def (test_\w+)", tpy, flags=re.M)
n_tests = sum(len(control.SHAPES) if "@pytest.mark.parametrize(\"shape\", SHAPES)\ndef " + t in tpy else 1 for t in tests)
number("All five tests pass", n_tests, f"test_pyflyt.py {tests} (the first parametrised over SHAPES)")
fact("backends", "one test flies the same line with the default controller on both backends",
     "numpy_positions, numpy_targets = _fly(NumpyEnv(n=5), \"line\")" in tpy and "SwarmController(env.n, env.dt)" in tpy,
     "test_the_same_controller_and_gains_drive_both_backends; _fly builds SwarmController with default gains")
fact("backends", "a line formation must not sink", "positions[:, 2].min() > 1.0" in tpy, "sink test: min z > 1.0 m")
fact("backends", "Its runs apply no separation clamp", "separation_clamp" not in tpy and "separation_clamp" not in pyf,
     "no clamp on the PyFlyt path")
m = re.search(r"simulation of \$N = 5\$ vehicles at 50~Hz", ch1)
r.expect("cross-chapter", not m, "Ch1 does not state one control rate for both backends" if not m else
         f"Ch1 l.{ch1[:m.start()].count(chr(10)) + 1} says the simulation runs 'at 50~Hz'; Ch4 4.6 says PyFlyt's "
         f"control rate is {pe.effective_control_hz:g} Hz (true of the kinematic backend only) -- judge", warn=True)
m = re.search(r"point navigation, for \$N = 5\$ at 50~Hz", ch1)
r.expect("cross-chapter", not m, "Ch1's controller row claims no point navigation" if not m else
         f"Ch1 l.{ch1[:m.start()].count(chr(10)) + 1} controller row: 'PID point navigation ... at 50 Hz'; Ch4 4.5: the "
         "controller's only command is a formation, no intent maps onto it -- judge", warn=True)

# -- The chapter's promise: no measured value -------------------------------------------------------
claimed = {i.line for i in r.items if i.check == "claim"}
measured_files = [*RESULTS.glob("*.md"), *(THESIS / "generated").glob("*.tex")]
measured: dict[float, str] = {}
for p in measured_files:
    for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for mm in re.finditer(r"(?<![\w.])\d[\d,]*\.\d+|(?<![\w.])\d{3,}(?:,\d{3})*", line):
            measured.setdefault(float(mm.group().replace(",", "")), f"{p.relative_to(REPO)}:{i}")
leaks, loose = [], []
for num in numbers(r.ch):
    if not significant(num) or round(num.value, 6) in params:
        continue
    if num.line in claimed:
        continue
    if num.value in measured:
        leaks.append(f"{num.text} (l.{num.line}; also {measured[num.value]})")
    else:
        loose.append(f"{num.text} (l.{num.line})")
r.expect("promise", not leaks, "no number outside the recomputed parameters appears in results/ or generated/"
         if not leaks else f"numbers not recomputed as parameters that also appear in a measured source: {leaks} -- "
         "a measured figure, or a parameter the script does not check yet")
r.expect("promise", not loose, "every significant number is recomputed by a claim" if not loose
         else f"significant numbers no claim recomputes: {loose}", warn=True)

r.manual.append("""### For the argument agent

- **Promises this chapter must keep.** Ch1 structure paragraph: audio chain, runtime and bus, state
  machine, controller, backends, in that order (the script checks the section order). Ch1 safety-problem
  paragraph and Ch3 lead-in: the third mechanism realised in the controller (4.5 separation clamp). Ch3
  3.1 "Prompt and prefix": the reason for cache_prompt=false is given in sec:runtime (4.2 "Prompt cache").
- **Promises this chapter makes** (labels): sec:latency-experiment (per-frame lag and compute, per-stage
  timings, prefill cost of the disabled cache, server stop latency); sec:keyword-spotter-evaluation (the
  spotter's rates); sec:acoustic-robustness (endpointer segments and split cost); sec:formation-control
  (interventions and collisions); sec:limitations (Wi-Fi hop never exercised; the raw-intent defect; and,
  by the STATE record, no clamp on PyFlyt); sec:demonstration-protocol (live capture, entry point,
  FSM->controller link). Check each is kept in Ch5/Ch6 as they stand.
- **Consistency with the Ch3 review (issue 11).** V2: queued utterances number at dequeue -- 4.2 says
  "reserved when the worker takes the utterance", consistent; check nothing else in 4.2/4.3 implies the
  number is reserved at endpointing. V3: the cancellation reaches only a running decode -- 4.2 says
  "closes the connection of the parser's request in flight, if there is one", but also "How quickly the
  server stops decoding ... bounds the preemption-recovery criterion" (a trigger during transcription is
  not bounded by it).
- **Seeded points** are in the issue. Script WARNs to judge: the 14% near-miss share (FAIL), the harness
  not recording the worker thread's affinity, PyFlyt's 20.83 ms tick vs "20 ms" and 12.5 s vs "12 s",
  "at least 85%" of five vehicles = all five, three timing observations in a no-measurement chapter.""")
sys.exit(r.finish())
