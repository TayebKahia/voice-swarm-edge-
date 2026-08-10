"""Generate train/kaggle_finetune.ipynb. The notebook is an artefact; this is its source.

Edit this file (or `_kaggle_notebook_cells.py`) and re-run --- never hand-edit the
.ipynb, which is regenerated wholesale.
"""

import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

# The merge/convert cells live beside this file, in the repository. They were briefly
# imported from a session scratchpad under /tmp, which meant the notebook could not be
# regenerated from a clean clone -- and an edit to the in-repo copy silently did
# nothing, because nothing read it.
sys.path.insert(0, str(HERE))
from _kaggle_notebook_cells import MERGE_MD, MERGE_SETUP, MERGE_RUN

MD = []
CODE = []
cells = []
def md(s): cells.append({"cell_type":"markdown","metadata":{},"source":s.strip("\n").splitlines(keepends=True)})
def code(s): cells.append({"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s.strip("\n").splitlines(keepends=True)})

md(r"""
# PFE --- LoRA fine-tuning, Surface-A eval, and the Gate 3 parity dump

Four models spanning 0.36-1.2B, one notebook, one Kaggle session. Everything the rest of the
project needs from a GPU happens here, because there is no usable local GPU
(`IMPLEMENTATION_ROADMAP.md` 0.5) and `torch` is deliberately not installed on the
workstation.

> ## THIS SESSION TRAINS ONE MODEL, NOT FOUR
>
> `ONLY` in the config cell is set to `configs/h2o-danube3-500m.yaml`. Qwen2.5-0.5B,
> SmolLM2-360M and Llama-3.2-1B are **already trained**, and every published result in
> the project --- Surface B, Tables 17/18/19, the McNemar tests, the abstention entry ---
> was measured on those exact adapters. **Do not clear `ONLY`.** Retraining them would
> produce different weights (fp16 GPU training is not bit-reproducible) and the results
> chapters would be describing artefacts that no longer exist.
>
> Expect roughly **40-60 minutes**, not the ~2 hours the three-model run took.
>
> `surface_a.csv` and `parity_hf.json` from this session cover **only** Danube3.
> **Concatenate** them with the existing `train/kaggle_out/` files --- do not overwrite.

## Before you press Run All

1. **Accelerator: GPU T4 x2** (Settings -> Accelerator). P100 also works.
2. **Internet: ON** (Settings -> Internet). Needs a phone-verified Kaggle account.
   Without it `from_pretrained` cannot reach Hugging Face and the session is wasted.
3. **Dataset attached:** `pfe-swarm-data` (the zip from `train/make_kaggle_bundle.py`).
4. **No `HF_TOKEN` needed for this session.** Danube3 is Apache-2.0 and ungated, and
   it is the only model in `ONLY`. The gated model is Llama-3.2-1B, which is not
   being trained here.
   *For a from-scratch run only:* accept the Meta Community Licence at
   huggingface.co/meta-llama/Llama-3.2-1B-Instruct, then Add-ons -> Secrets ->
   `HF_TOKEN`. Qwen, SmolLM2 and Danube3 need no token. If the token is missing the
   notebook trains the rest and says so rather than dying at the end.
5. **Download before the session expires:** `/kaggle/working/pfe_outputs.zip`.
   Nothing outside `/kaggle/working` survives, and nothing at all survives the session.

## The one deviation from the frozen recipe

Table 14 specifies **bf16**. Kaggle's free accelerators are T4 (SM 7.5) and P100
(SM 6.0); hardware bf16 needs Ampere (SM 8.0+). All four runs therefore use **fp16**,
applied identically. RQ1's design is *hold everything constant except the model*, so
the ranking --- which is the claim --- is unaffected; the absolute EM may shift. This
is recorded here, in `train/configs/*.yaml`, in the Table 17 caption, and in the
Limitations table. If loss goes NaN in the first 200 steps, the fallback is fp32, not
QLoRA (Table 14 excludes QLoRA).
""")

code(r"""
# Install as little as possible. Kaggle's image already ships torch, numpy 2.x and
# a modern transformers, and BOTH failures of this notebook came from upgrading
# packages that were already there:
#
#   run 1: pinning transformers==4.44/datasets==2.21 resolved numpy DOWN to 1.26,
#          and the image's TensorFlow/jax are built against numpy 2 ->
#          "numpy.dtype size changed, Expected 96 from C header, got 88"
#   run 2: `pip install -U transformers` overwrote the preinstalled package inside
#          a LIVE kernel, leaving a new top level against a stale generation/
#          subpackage -> "cannot import name GenerationMixin"
#
# So nothing is upgraded. Only genuinely absent packages are installed, and with
# --no-deps so pip cannot touch numpy, torch or transformers as a side effect.
import importlib, subprocess, sys

def present(module):
    try:
        importlib.import_module(module)
        return True
    except Exception:
        return False

REQUIRED = [("peft", "peft"), ("yaml", "pyyaml"), ("accelerate", "accelerate")]
missing = [package for module, package in REQUIRED if not present(module)]

if missing:
    print("installing (no deps):", missing)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", *missing],
                   check=True)
    print("If anything below still fails to import, START A FRESH SESSION rather than "
          "re-running this cell: pip cannot safely replace a package the kernel has "
          "already imported.")
else:
    print("nothing to install -- the image already has everything")
""")

code(r'''
import json, os, random, sys, time, zipfile, shutil
from dataclasses import dataclass, field
from pathlib import Path

# Belt and braces with the pins above. transformers imports its TensorFlow and Flax
# paths lazily, and merely touching `TFPreTrainedModel` is enough to drag the whole
# of TensorFlow -> jax -> numpy into the process. Nothing here trains in TF, so both
# backends are switched off BEFORE transformers is first imported; with them off the
# TF symbols resolve to dummy objects and tensorflow is never loaded at all.
os.environ["USE_TF"] = "0"
os.environ["USE_FLAX"] = "0"
os.environ["USE_JAX"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import numpy as np
import torch

# Fail here, loudly and in two seconds, rather than 40 minutes into a run that was
# launched with Save & Run All and left overnight.
assert int(np.__version__.split(".")[0]) >= 2, (
    f"numpy is {np.__version__}; the Kaggle image needs 2.x. Something installed a "
    "package with dependencies -- start a fresh session.")
import yaml
from torch.utils.data import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                          TrainerCallback, TrainingArguments, set_seed)
from peft import LoraConfig, get_peft_model

# peft's LoRA dispatcher chain has a torchao branch whose availability check RAISES
# when torchao is present but older than it wants -- Kaggle ships 0.10.0, peft wants
# >0.16 -- so get_peft_model dies before reaching the plain nn.Linear branch. This
# recipe is LoRA, not QLoRA, and never touches torchao, so the branch is simply told
# it is unavailable and the chain falls through to the path Table 14 wants.
#
# Patched, NOT uninstalled. `pip uninstall torchao` removes the distribution metadata
# but can leave the package directory importable; transformers' own quantizer_torchao
# then passes its is_torchao_available() check and calls
# importlib.metadata.version("torchao") on it -> PackageNotFoundError, which breaks
# transformers itself and cascades into every later import. Lying to one predicate is
# a far smaller intervention than editing the image.
_patched = []
for _module_name in ("peft.import_utils", "peft.tuners.lora.torchao"):
    try:
        import importlib as _importlib
        _module = _importlib.import_module(_module_name)
        if hasattr(_module, "is_torchao_available"):
            _module.is_torchao_available = lambda: False
            _patched.append(_module_name)
    except Exception:
        pass
print("torchao dispatcher disabled in:", _patched or "(nothing to patch)")

# The image pairs peft 0.19 with torchao 0.10. When peft builds a LoRA layer it walks
# a chain of dispatchers, and `dispatch_torchao` calls `is_torchao_available()` --
# which RAISES on a torchao below 0.16 rather than returning False. Nothing here uses
# torchao: it is a quantisation backend we never ask for, and the exception lands in
# the middle of get_peft_model, so all four models die before a single training step.
#
# Reporting it unavailable is the honest answer -- it genuinely is not usable -- and
# lets the dispatcher fall through to the ordinary Linear -> lora.Linear path. This is
# done in-process rather than by uninstalling or upgrading torchao: the two failures
# before this one both came from mutating the image, and a monkeypatch touches no
# disk, needs no network and cannot resolve some other package underneath us.
def _silence_broken_torchao():
    try:
        import peft.import_utils as peft_imports
    except Exception:
        return
    try:
        peft_imports.is_torchao_available()
        return                                    # a usable torchao; leave it alone
    except Exception as exc:
        print(f"torchao unusable, reporting it as absent: {exc}")

    unavailable = lambda: False
    peft_imports.is_torchao_available = unavailable
    # The dispatcher imported the name into its own module namespace, so patching
    # peft.import_utils alone would not be seen there.
    try:
        import peft.tuners.lora.torchao as lora_torchao
        lora_torchao.is_torchao_available = unavailable
    except Exception:
        pass


_silence_broken_torchao()

WORK = Path("/kaggle/working")

# Find the uploaded bundle rather than hard-coding its path. A Kaggle Dataset's
# directory name is its slug, which is whatever the title was normalised to, and
# whether the zip is auto-extracted or left whole is not under our control. Hunting
# for a landmark file is stable against both, and it fails with a directory listing
# instead of a bare ModuleNotFoundError forty lines later.
LANDMARKS = ("schema/canon.py", "data/train.jsonl")
INPUT = Path("/kaggle/input")


def _is_bundle(candidate):
    return all((candidate / relative).is_file() for relative in LANDMARKS)


def find_data_root():
    """Locate the bundle at whatever depth Kaggle mounted it.

    Kaggle nests a Dataset as /kaggle/input/datasets/<owner>/<slug>/, but has also
    mounted it as /kaggle/input/<slug>/ --- and the slug is the normalised title, not
    anything we choose. Rather than guess a depth, search for one of the landmark
    files and work back up to the directory holding it; that is correct at any depth
    and stays correct if the layout changes again.
    """
    marker = Path(LANDMARKS[0])              # schema/canon.py
    for hit in sorted(INPUT.rglob(marker.name)):
        candidate = hit.parents[len(marker.parts) - 1]
        if _is_bundle(candidate):
            return candidate

    # Not extracted: Kaggle kept the archive whole. /kaggle/input is read-only, so
    # unpack into /kaggle/tmp.
    for archive in sorted(INPUT.rglob("*.zip")):
        destination = Path("/kaggle/tmp/pfe_data")
        destination.mkdir(parents=True, exist_ok=True)
        zipfile.ZipFile(archive).extractall(destination)
        for hit in sorted(destination.rglob(marker.name)):
            candidate = hit.parents[len(marker.parts) - 1]
            if _is_bundle(candidate):
                print(f"extracted {archive.name} -> {candidate}")
                return candidate

    listing = "\n".join(f"  {path}" for path in sorted(INPUT.rglob("*"))[:40])
    raise SystemExit(
        f"could not find the data bundle -- a directory holding both {LANDMARKS[0]} "
        f"and {LANDMARKS[1]}.\n"
        + ("/kaggle/input is empty: the dataset is not attached to this notebook "
           "(Add Data, right-hand panel).\n" if not listing else
           f"Found these, but none is a complete bundle:\n{listing}\n"))


DATA = find_data_root()
print("data root:", DATA)
ADAPTERS = WORK / "adapters"; ADAPTERS.mkdir(parents=True, exist_ok=True)

# The schema package travels with the data so exact match here is the SAME
# comparator as the one in the repo (schema/canon.py). A second JSON comparison
# written inline could disagree with it silently.
sys.path.insert(0, str(DATA))
from schema.canon import canon

SEED = 42
set_seed(SEED); random.seed(SEED); np.random.seed(SEED)

AUDIT = json.loads((DATA / "eval" / "fixed_audit_prompts.json").read_text())
SYSTEM_PROMPT = AUDIT["system_prompt"]

import transformers, peft
print("numpy", np.__version__, "| transformers", transformers.__version__,
      "| peft", peft.__version__)
print("torch", torch.__version__, "| cuda", torch.cuda.is_available())
print("gpu  ", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE")
cap = torch.cuda.get_device_capability(0) if torch.cuda.is_available() else (0, 0)
print(f"sm    {cap[0]}.{cap[1]}  -> bf16 {'available' if cap[0] >= 8 else 'NOT available, using fp16 (Table 14 deviation)'}")
print("system prompt:", repr(SYSTEM_PROMPT))


def _system_role_supported(tokenizer):
    """Does THIS model's own chat template admit a system turn?

    Probed, never hardcoded by model name. h2o-danube3's template raises
    TemplateError("System role not supported"); Qwen2.5, SmolLM2 and Llama-3.2 all
    render one. Probing rather than listing matters because the three
    already-trained models MUST keep taking the system path byte-for-byte -- their
    adapters, Surface B, Tables 17/18/19, McNemar and the abstention entry were all
    produced under that rendering -- and a probe cannot drift from reality the way a
    hand-maintained list can. Cached on the tokenizer: the answer is a property of
    the template and cannot change mid-run.
    """
    cached = getattr(tokenizer, "_pfe_system_ok", None)
    if cached is None:
        try:
            tokenizer.apply_chat_template(
                [{"role": "system", "content": "probe"},
                 {"role": "user", "content": "probe"}],
                tokenize=False, add_generation_prompt=True)
            cached = True
        except Exception:
            cached = False
        tokenizer._pfe_system_ok = cached
    return cached


def build_messages(tokenizer, user_text):
    """The ONE place a prompt's message list is built.

    Training (CommandDataset), Surface-A eval (generate_batch) and the Gate 3
    parity dump all call this. If those three ever construct prompts differently
    the model is trained under one rendering and measured under another, which is
    exactly the silent failure prd.md Sec. 10.1 names as this project's
    highest-cost -- accuracy degrades with no error message. One function, three
    callers, no second place to get it wrong.
    """
    if _system_role_supported(tokenizer):
        return [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}]
    # This model's template refuses a system turn, so fold the instruction into the
    # user turn -- the conventional workaround, and the one that preserves what the
    # model actually reads: the same two strings in the same order, differing only
    # in the role scaffolding the template wraps them in. It is still a deviation
    # from the other three and is declared as one, not smoothed over.
    return [{"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{user_text}"}]
''')

md(r"""
## Data

`transcript` in, canonical JSON out. The target is passed through `canon` rather than
used as written, so the model is trained on byte-identical output to what exact match
compares against --- key order, number formatting and omitted nulls all fixed by
`prd.md` 6.1 rather than by whatever the generator happened to emit.
""")

code(r'''
def load(split):
    rows = [json.loads(l) for l in (DATA / "data" / f"{split}.jsonl").read_text().splitlines() if l.strip()]
    for r in rows:
        r["canonical"] = canon(json.loads(r["target"]))
    return rows

TRAIN, VAL = load("train"), load("val")
TESTS = {name: load(name) for name in ("test_synth", "test_golden", "test_ood")}
print({k: len(v) for k, v in [("train", TRAIN), ("val", VAL)] + list(TESTS.items())})
print("\nexample\n  in :", TRAIN[0]["transcript"], "\n  out:", TRAIN[0]["canonical"])
''')

md(r"""
## Prompt construction and completion-only masking

Two rules from Table 14 that are easy to get silently wrong:

**Each model's own chat template.** Qwen is ChatML, SmolLM2 and Llama-3.2 differ. A
hand-written special token trains fine and emits garbage at inference, so
`tokenizer.apply_chat_template` is the only thing used.

**Prompt tokens contribute no gradient.** Rather than `DataCollatorForCompletionOnlyLM`
with a per-model response-template string --- which fails quietly when the template
does not tokenise the way the string does --- the prompt and the completion are
tokenised *separately* and concatenated. The mask is then exact by construction, not
by string matching. The cell after this one asserts it.

**Packing is off.** Packing concatenates examples across boundaries and would carry
one example's completion into the next example's masked prompt region.
""")

code(r'''
MAX_LEN = 256

class CommandDataset(Dataset):
    """transcript -> canonical JSON, with the prompt masked out of the loss."""

    def __init__(self, rows, tokenizer):
        self.items, self.overflow = [], 0
        for row in rows:
            messages = build_messages(tokenizer, row["transcript"])
            prompt_text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
            prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
            target_ids = tokenizer(row["canonical"], add_special_tokens=False)["input_ids"]
            if tokenizer.eos_token_id is not None:
                target_ids = target_ids + [tokenizer.eos_token_id]

            input_ids = prompt_ids + target_ids
            if len(input_ids) > MAX_LEN:
                # Truncating the completion would teach the model to stop mid-JSON.
                self.overflow += 1
                continue
            labels = [-100] * len(prompt_ids) + list(target_ids)
            self.items.append({"input_ids": input_ids, "labels": labels,
                               "attention_mask": [1] * len(input_ids)})

    def __len__(self): return len(self.items)
    def __getitem__(self, i): return self.items[i]


def collate(batch, pad_id):
    width = max(len(b["input_ids"]) for b in batch)
    out = {"input_ids": [], "labels": [], "attention_mask": []}
    for b in batch:
        gap = width - len(b["input_ids"])
        out["input_ids"].append(b["input_ids"] + [pad_id] * gap)
        out["labels"].append(b["labels"] + [-100] * gap)     # padding never scores
        out["attention_mask"].append(b["attention_mask"] + [0] * gap)
    return {k: torch.tensor(v, dtype=torch.long) for k, v in out.items()}
''')

code(r'''
# --- verify the masking is actually active, before spending a GPU hour on it ---
_tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
_probe = CommandDataset(TRAIN[:8], _tok)
_item = _probe[0]
_supervised = [i for i, l in enumerate(_item["labels"]) if l != -100]

assert _supervised, "no supervised tokens -- the whole sequence is masked"
assert _supervised[0] > 0, "token 0 is supervised -- the prompt is NOT masked"
assert _supervised == list(range(_supervised[0], len(_item["labels"]))), \
    "supervised region is not a contiguous tail -- masking is misaligned"
assert all(a == b for a, b in zip(_item["input_ids"][_supervised[0]:],
                                  [l for l in _item["labels"] if l != -100])), \
    "labels do not match the input ids they supervise"

print("masked prompt tokens :", _supervised[0])
print("supervised tokens    :", len(_supervised))
print("decoded supervision  :", repr(_tok.decode([l for l in _item["labels"] if l != -100])))
print("overflow dropped     :", _probe.overflow)
print("\nCOMPLETION-ONLY MASKING VERIFIED")
del _tok, _probe
''')

md(r"""
## Checkpoint selection: best validation **exact match**, not best validation loss

Table 14 is explicit about this and it is not a formality. Loss is a token-level
surrogate; the metric the thesis reports is `canon(pred) == canon(gold)`, which is
all-or-nothing on a whole JSON object. A checkpoint can improve perplexity while
getting *fewer* commands exactly right --- and a command that is nearly right is not
partially flown.

Generation is greedy, matching the runtime. No grammar is applied here: this is
Surface A (HF FP16, unconstrained), which is exactly the point of comparison for
Table 18's quantisation delta.
""")

code(r'''
@torch.no_grad()
def generate_batch(model, tokenizer, rows, batch_size=32, max_new_tokens=64):
    """Greedy generation over `rows`, returning the raw decoded completions."""
    was_padding_side = tokenizer.padding_side
    tokenizer.padding_side = "left"          # generation needs left padding
    model.eval()
    outputs = []
    for start in range(0, len(rows), batch_size):
        chunk = rows[start:start + batch_size]
        prompts = [tokenizer.apply_chat_template(
            build_messages(tokenizer, r["transcript"]),
            tokenize=False, add_generation_prompt=True) for r in chunk]
        enc = tokenizer(prompts, return_tensors="pt", padding=True,
                        add_special_tokens=False).to(model.device)
        generated = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                                   num_beams=1, pad_token_id=tokenizer.pad_token_id)
        for i in range(len(chunk)):
            new_tokens = generated[i][enc["input_ids"].shape[1]:]
            outputs.append(tokenizer.decode(new_tokens, skip_special_tokens=True).strip())
    tokenizer.padding_side = was_padding_side
    return outputs


def exact_match(model, tokenizer, rows, batch_size=32):
    """Fraction where canon(pred) == canon(gold). Unparseable output scores 0."""
    hypotheses = generate_batch(model, tokenizer, rows, batch_size=batch_size)
    hits = 0
    for row, text in zip(rows, hypotheses):
        try:
            hits += canon(json.loads(text)) == row["canonical"]
        except Exception:
            pass                              # malformed JSON is simply not a match
    return hits / len(rows), hypotheses


class BestExactMatch(TrainerCallback):
    """Keep the epoch with the highest validation EM, not the lowest loss."""

    def __init__(self, model, tokenizer, val_rows, out_dir):
        self.model, self.tokenizer, self.val = model, tokenizer, val_rows
        self.out_dir, self.best, self.history = Path(out_dir), -1.0, []

    def on_epoch_end(self, args, state, control, **kwargs):
        started = time.time()
        score, _ = exact_match(self.model, self.tokenizer, self.val)
        epoch = round(state.epoch or 0, 2)
        self.history.append({"epoch": epoch, "val_exact_match": score})
        flag = ""
        if score > self.best:
            self.best = score
            self.model.save_pretrained(self.out_dir)     # adapter only, ~20 MB
            flag = "  <- best, saved"
        print(f"  [epoch {epoch}] val EM {score:.4f}  ({time.time() - started:.0f}s){flag}")
        self.model.train()
        return control
''')

md("## Train")

code(r'''
def train_one(config_path):
    cfg = yaml.safe_load(Path(config_path).read_text())
    name, hf_id = cfg["name"], cfg["hf_id"]
    print(f"\n{'=' * 70}\n{name}  ({hf_id})\n{'=' * 70}")

    token = None
    if cfg.get("gated"):
        try:
            from kaggle_secrets import UserSecretsClient
            token = UserSecretsClient().get_secret("HF_TOKEN")
        except Exception as exc:
            print(f"  SKIPPED -- gated model and no HF_TOKEN secret ({exc})")
            return None

    tokenizer = AutoTokenizer.from_pretrained(hf_id, token=token)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Say out loud which prompt rendering this model gets. A run left overnight
    # must not silently fold the system prompt into the user turn without leaving
    # a trace in the log -- that is a deviation from the other three and a reader
    # of Table 17 is entitled to know which rows carry it.
    system_ok = _system_role_supported(tokenizer)
    if system_ok:
        print("  prompt rendering : system turn + user turn (standard)")
    else:
        print("  prompt rendering : NO SYSTEM ROLE in this model's chat template --")
        print("                     system prompt folded into the user turn.")
        print("                     DEVIATION from the other three; declare it.")

    model = AutoModelForCausalLM.from_pretrained(
        hf_id, torch_dtype=torch.float16, token=token).cuda()
    # Zero-shot FIRST, before any adapter touches the weights: Table 17's "before"
    # rows, obtained free while the base model is already resident. Same generator,
    # same comparator and same precision as the fine-tuned rows, so the two are
    # directly subtractable. Expect these to be low --- spike S3 showed base models
    # degenerating into unbounded id lists without a grammar to stop them.
    zero_shot = {}
    for split, rows in TESTS.items():
        score, _ = exact_match(model, tokenizer, rows)
        zero_shot[split] = score
        print(f"  zero-shot {split:12s} EM={score:.4f}")

    model.config.use_cache = False               # incompatible with grad checkpointing
    model = get_peft_model(model, LoraConfig(
        r=cfg["lora"]["r"], lora_alpha=cfg["lora"]["alpha"],
        lora_dropout=cfg["lora"]["dropout"],
        target_modules=cfg["lora"]["target_modules"],
        bias="none", task_type="CAUSAL_LM"))
    model.print_trainable_parameters()

    train_ds, val_ds = CommandDataset(TRAIN, tokenizer), CommandDataset(VAL, tokenizer)
    print(f"  train {len(train_ds)} (dropped {train_ds.overflow} over {MAX_LEN} tokens)"
          f" | val {len(val_ds)} (dropped {val_ds.overflow})")

    out_dir = ADAPTERS / name
    callback = BestExactMatch(model, tokenizer, VAL, out_dir)

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=f"/kaggle/tmp/{name}",
            num_train_epochs=cfg["train"]["epochs"],
            per_device_train_batch_size=cfg["train"]["per_device_train_batch_size"],
            gradient_accumulation_steps=cfg["train"]["gradient_accumulation_steps"],
            learning_rate=float(cfg["optim"]["learning_rate"]),
            lr_scheduler_type=cfg["optim"]["lr_scheduler_type"],
            warmup_ratio=cfg["optim"]["warmup_ratio"],
            optim=cfg["optim"]["optimizer"],
            fp16=True,                            # Table 14 deviation, see the header
            logging_steps=25, save_strategy="no", report_to=[], seed=SEED,
            dataloader_pin_memory=False),
        train_dataset=train_ds,
        data_collator=lambda b: collate(b, tokenizer.pad_token_id),
        callbacks=[callback])

    result = trainer.train()
    print(f"  final train loss {result.training_loss:.4f} | best val EM {callback.best:.4f}")
    (out_dir / "training_history.json").write_text(json.dumps({
        "model": name, "hf_id": hf_id, "precision": "fp16",
        "system_role_supported": system_ok,
        "best_val_exact_match": callback.best, "history": callback.history,
        "final_train_loss": result.training_loss,
        "dropped_over_max_len": train_ds.overflow}, indent=2))
    return {"name": name, "hf_id": hf_id, "tokenizer": tokenizer, "token": token,
            "model": model, "best_val_em": callback.best, "zero_shot": zero_shot}
''')

code(r'''
ALL_CONFIGS = ["configs/qwen2.5-0.5b.yaml", "configs/smollm2-360m.yaml",
               "configs/llama-3.2-1b.yaml", "configs/h2o-danube3-500m.yaml"]

# Train a subset by naming them here; empty list means all four.
#
# Kaggle gives no persistence between sessions, so a rerun retrains everything from
# scratch by default. For a from-scratch reproduction that is the right default --
# all artefacts then come out of one session under one image, which is what RQ1's
# "hold everything constant except the model" asks for, and fp16 training on a GPU
# is not bit-reproducible, so artefacts from two sessions are not quite the same
# experiment.
#
# ####################################################################
# ONLY IS DELIBERATELY NON-EMPTY. DO NOT CLEAR IT ON THIS PROJECT.
#
# The first three models are ALREADY TRAINED and every published result --
# Surface B, Tables 17/18/19, the McNemar tests, the abstention entry -- was
# measured on those exact adapters. Clearing ONLY retrains them, and fp16 GPU
# training is not bit-reproducible, so the new adapters would NOT be the ones
# those numbers came from. The whole results chapter would be describing
# artefacts that no longer exist.
#
# Clear ONLY only when reproducing the entire project from a clean clone with
# no downloaded adapters, and expect every downstream number to move.
# ####################################################################
#
# h2o-danube3-500m is the iso-parameter control added after the other three (see
# its config header). It is the escape hatch's intended case: one model added to
# a finished set. Its adapter, GGUF and per-model prediction files stand alone,
# but surface_a.csv and parity_hf.json will describe ONLY this model and have to
# be CONCATENATED with the earlier download rather than replacing it.
ONLY: list[str] = ["configs/h2o-danube3-500m.yaml"]

CONFIGS = ONLY or ALL_CONFIGS
if ONLY:
    print(f"PARTIAL RUN -- {len(CONFIGS)} of {len(ALL_CONFIGS)} models.")
    print("surface_a.csv and parity_hf.json will cover only these; merge with the "
          "earlier download, do not overwrite it.")

trained, failed, started = [], [], time.time()
for relative in CONFIGS:
    # Each model is isolated. This notebook is meant to be launched with
    # "Save & Run All" and left overnight, so an exception on the third model must
    # not take cells 14-21 with it -- that would discard the Surface-A CSV, the
    # parity dump and the GGUFs for the two models that trained perfectly well,
    # with nobody awake to notice. Failures are collected and reported at the end.
    try:
        entry = train_one(DATA / relative)
    except Exception as exc:
        import traceback
        failed.append((relative, f"{type(exc).__name__}: {exc}"))
        print(f"\n!! {relative} FAILED -- continuing with the rest")
        traceback.print_exc()
        torch.cuda.empty_cache()
        continue
    if entry:
        trained.append(entry)
        # Free the GPU between runs; the models do not fit at once.
        entry["model"].cpu(); torch.cuda.empty_cache()

print(f"\ntrained {len(trained)}/{len(CONFIGS)} in {(time.time() - started) / 60:.1f} min")
for relative, reason in failed:
    print(f"  FAILED {relative}: {reason}")
    if "gated repo" in reason or "403" in reason or "401" in reason:
        print("     -> This is an ACCESS grant, not a token problem. Request access at")
        print("        the model's Hugging Face page and wait for approval, then rerun.")
        print("        The other models are unaffected and their artefacts are below.")
if not trained:
    raise SystemExit("no model trained -- nothing downstream can run")
''')

md(r"""
## Surface-A: FP16 exact match on the held-out sets

This is Session 05A item 1, done here because the weights are already resident and the
GPU is warm. It is the **FP16 column of Table 18**; the quantised column comes from
`llama.cpp` on the workstation, and the difference between them is contribution C3.

Doing it locally would mean CPU inference over four models times ~590 items.
""")

code(r'''
import csv

rows_out = []
for entry in trained:
    # The "before" rows, captured before training in train_one().
    for split, score in entry["zero_shot"].items():
        rows_out.append({"model": entry["name"], "surface": "A_fp16_zeroshot",
                         "split": split, "n": len(TESTS[split]),
                         "exact_match": round(score, 6), "best_val_em": ""})

    entry["model"].cuda()
    for split, rows in TESTS.items():
        score, hypotheses = exact_match(entry["model"], entry["tokenizer"], rows)
        rows_out.append({"model": entry["name"], "surface": "A_fp16_finetuned",
                         "split": split, "n": len(rows), "exact_match": round(score, 6),
                         "best_val_em": round(entry["best_val_em"], 6)})
        print(f"{entry['name']:28s} {split:12s} n={len(rows):4d}  EM={score:.4f}")
        (WORK / f"preds_{entry['name']}_{split}.jsonl").write_text("\n".join(
            json.dumps({"id": r["id"], "transcript": r["transcript"],
                        "gold": r["canonical"], "pred": h}) for r, h in zip(rows, hypotheses)))
    entry["model"].cpu(); torch.cuda.empty_cache()

with (WORK / "surface_a.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["model", "surface", "split", "n",
                                                "exact_match", "best_val_em"])
    writer.writeheader(); writer.writerows(rows_out)
print("\nwrote surface_a.csv")
''')

md(r"""
## Gate 3: dump the HF side of the parity check

The same ten fixed prompts, formatted by each model's own chat template, with their
token IDs. `eval/test_template_parity.py` on the workstation compares this JSON against
live `llama.cpp` output and asserts **token-ID identity**.

A mismatch degrades accuracy with no error message --- it looks like a quantisation bug
or a bad fine-tune. That is why `prd.md` calls it "a mandatory gate after every
conversion, not a diagnostic run when something looks wrong."
""")

code(r'''
parity = {}
for entry in trained:
    tokenizer = entry["tokenizer"]
    records = []
    for prompt in AUDIT["prompts"]:
        text = tokenizer.apply_chat_template(
            build_messages(tokenizer, prompt["user_text"]),
            tokenize=False, add_generation_prompt=True)
        records.append({"id": prompt["id"], "name": prompt["name"],
                        "user_text": prompt["user_text"],
                        "formatted": text,
                        "token_ids": tokenizer(text, add_special_tokens=False)["input_ids"]})
    parity[entry["name"]] = records
    print(f"{entry['name']:28s} {len(records)} prompts, "
          f"{sum(len(r['token_ids']) for r in records)} tokens")

(WORK / "parity_hf.json").write_text(json.dumps(
    {"system_prompt": SYSTEM_PROMPT,
     "system_role_folded": {e["name"]: not _system_role_supported(e["tokenizer"])
                            for e in trained},
     "models": parity}, indent=2))
print("\nwrote parity_hf.json")
''')

md(MERGE_MD)
code(MERGE_SETUP)
code(MERGE_RUN)

md("## Package everything for download")

code(r'''
bundle = WORK / "pfe_outputs.zip"
with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(WORK.rglob("*")):
        # The GGUFs are gigabytes and are downloaded individually from the Output
        # panel. Including them here would double the disk they occupy and turn a
        # ~10 MB download into a ~4 GB one -- and the cell below says they are not
        # in the zip, so it had better be true.
        if path.is_file() and path != bundle and GGUF not in path.parents:
            archive.write(path, path.relative_to(WORK))

print(f"{bundle}  ({bundle.stat().st_size / 1e6:.1f} MB)\n")
for name in sorted(zipfile.ZipFile(bundle).namelist()):
    print(" ", name)

print("""
DOWNLOAD pfe_outputs.zip NOW -- nothing here survives the session.

It must contain, for each model that trained:
  adapters/<model>/adapter_model.safetensors   the LoRA weights
  adapters/<model>/training_history.json       per-epoch val EM
  surface_a.csv                                Table 18's FP16 column
  parity_hf.json                               Gate 3's HF side
  preds_<model>_<split>.jsonl                  per-item predictions

Unzip into the repo:  unzip -o pfe_outputs.zip -d train/kaggle_out/
""")
''')

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.11"},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 5}
out = HERE / "kaggle_finetune.ipynb"
out.write_text(json.dumps(nb, indent=1))
print(f"wrote {out.relative_to(REPO)}  ({len(cells)} cells, {out.stat().st_size/1024:.0f} KB)")
