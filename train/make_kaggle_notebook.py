import json, pathlib

import sys; sys.path.insert(0, '/tmp/claude-1000/-home-kahia-tayeb-PFE/e48efa90-3b08-4c92-a78e-16adf1900a9a/scratchpad')
from merge_cells import MERGE_MD, MERGE_SETUP, MERGE_RUN

MD = []
CODE = []
cells = []
def md(s): cells.append({"cell_type":"markdown","metadata":{},"source":s.strip("\n").splitlines(keepends=True)})
def code(s): cells.append({"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s.strip("\n").splitlines(keepends=True)})

md(r"""
# PFE --- LoRA fine-tuning, Surface-A eval, and the Gate 3 parity dump

Three 0.5B-class models, one notebook, one Kaggle session. Everything the rest of the
project needs from a GPU happens here, because there is no usable local GPU
(`IMPLEMENTATION_ROADMAP.md` 0.5) and `torch` is deliberately not installed on the
workstation.

## Before you press Run All

1. **Accelerator: GPU T4 x2** (Settings -> Accelerator). P100 also works.
2. **Internet: ON** (Settings -> Internet). Needs a phone-verified Kaggle account.
   Without it `from_pretrained` cannot reach Hugging Face and the session is wasted.
3. **Dataset attached:** `pfe-swarm-data` (the zip from `train/make_kaggle_bundle.py`).
4. **Llama-3.2-1B is gated.** Accept the Meta Community Licence at
   huggingface.co/meta-llama/Llama-3.2-1B-Instruct, then Add-ons -> Secrets ->
   `HF_TOKEN`. Qwen and SmolLM2 need no token. If the token is missing the notebook
   trains the other two and says so rather than dying at the end.
5. **Download before the session expires:** `/kaggle/working/pfe_outputs.zip`.
   Nothing outside `/kaggle/working` survives, and nothing at all survives the session.

## The one deviation from the frozen recipe

Table 14 specifies **bf16**. Kaggle's free accelerators are T4 (SM 7.5) and P100
(SM 6.0); hardware bf16 needs Ampere (SM 8.0+). All three runs therefore use **fp16**,
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

DATA = Path("/kaggle/input/pfe-swarm-data")
WORK = Path("/kaggle/working")
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
            messages = [{"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": row["transcript"]}]
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
            [{"role": "system", "content": SYSTEM_PROMPT},
             {"role": "user", "content": r["transcript"]}],
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
        "best_val_exact_match": callback.best, "history": callback.history,
        "final_train_loss": result.training_loss,
        "dropped_over_max_len": train_ds.overflow}, indent=2))
    return {"name": name, "hf_id": hf_id, "tokenizer": tokenizer, "token": token,
            "model": model, "best_val_em": callback.best, "zero_shot": zero_shot}
''')

code(r'''
CONFIGS = ["configs/qwen2.5-0.5b.yaml", "configs/smollm2-360m.yaml", "configs/llama-3.2-1b.yaml"]

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
        # Free the GPU between runs; three models do not fit at once.
        entry["model"].cpu(); torch.cuda.empty_cache()

print(f"\ntrained {len(trained)}/{len(CONFIGS)} in {(time.time() - started) / 60:.1f} min")
for relative, reason in failed:
    print(f"  FAILED {relative}: {reason}")
if not trained:
    raise SystemExit("no model trained -- nothing downstream can run")
''')

md(r"""
## Surface-A: FP16 exact match on the held-out sets

This is Session 05A item 1, done here because the weights are already resident and the
GPU is warm. It is the **FP16 column of Table 18**; the quantised column comes from
`llama.cpp` on the workstation, and the difference between them is contribution C3.

Doing it locally would mean CPU inference over three models times ~590 items.
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
            [{"role": "system", "content": SYSTEM_PROMPT},
             {"role": "user", "content": prompt["user_text"]}],
            tokenize=False, add_generation_prompt=True)
        records.append({"id": prompt["id"], "name": prompt["name"],
                        "user_text": prompt["user_text"],
                        "formatted": text,
                        "token_ids": tokenizer(text, add_special_tokens=False)["input_ids"]})
    parity[entry["name"]] = records
    print(f"{entry['name']:28s} {len(records)} prompts, "
          f"{sum(len(r['token_ids']) for r in records)} tokens")

(WORK / "parity_hf.json").write_text(json.dumps(
    {"system_prompt": SYSTEM_PROMPT, "models": parity}, indent=2))
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
out = pathlib.Path("train/kaggle_finetune.ipynb")
out.write_text(json.dumps(nb, indent=1))
print(f"wrote {out}  ({len(cells)} cells, {out.stat().st_size/1024:.0f} KB)")
