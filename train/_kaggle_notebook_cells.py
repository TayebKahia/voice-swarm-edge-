MERGE_MD = r"""
## Merge the adapters and convert to GGUF f16

This has to happen here, not on the workstation. Merging a LoRA adapter into its base
weights needs `torch` and `peft`, and neither is installed locally --- deliberately
(`IMPLEMENTATION_ROADMAP.md` 0.5, and 2.8a trap 3). Converting to GGUF needs the
converter from the `llama.cpp` tree, which reads the merged safetensors with torch.

What stays local is `llama-quantize`: pure C++, reads the f16 GGUF produced here, emits
Q8_0 and Q4_K_M. So the split is

    Kaggle       adapter -> merged fp16 -> GGUF f16
    workstation  GGUF f16 -> Q8_0, Q4_K_M       (the six artefacts of Session 05A)

**Download the .gguf files separately.** They are far too large for the outputs zip.
"""

MERGE_SETUP = r"""
!git clone --depth 1 --quiet https://github.com/ggml-org/llama.cpp /kaggle/tmp/llama.cpp
# --no-deps for the same reason as the first cell: this runs AFTER training, and a
# dependency resolution that moved numpy here would lose the GGUF conversion at the
# very end of an overnight run. `gguf` needs numpy/tqdm/pyyaml, all already present.
!pip install -q --no-deps gguf sentencepiece 2>&1 | tail -1
!ls -l /kaggle/tmp/llama.cpp/convert_hf_to_gguf.py
"""

MERGE_RUN = r"""
import subprocess
from peft import PeftModel

GGUF = WORK / "gguf"; GGUF.mkdir(exist_ok=True)
MERGED = Path("/kaggle/tmp/merged"); MERGED.mkdir(parents=True, exist_ok=True)
CONVERTER = "/kaggle/tmp/llama.cpp/convert_hf_to_gguf.py"

for entry in trained:
    name = entry["name"]
    print(f"\n--- {name}")

    # Reload the BASE and apply the adapter saved on disk, rather than merging the
    # in-memory model. The in-memory one is whatever the final epoch left behind;
    # the checkpoint that matters is the best-val-exact-match one (Table 14).
    base = AutoModelForCausalLM.from_pretrained(
        entry["hf_id"], torch_dtype=torch.float16, token=entry.get("token"))
    merged = PeftModel.from_pretrained(base, str(ADAPTERS / name)).merge_and_unload()

    target = MERGED / name
    merged.save_pretrained(target, safe_serialization=True)
    entry["tokenizer"].save_pretrained(target)
    del base, merged
    torch.cuda.empty_cache()

    out = GGUF / f"{name}-f16.gguf"
    done = subprocess.run(
        ["python", CONVERTER, str(target), "--outfile", str(out), "--outtype", "f16"],
        capture_output=True, text=True)
    if out.is_file():
        print(f"  {out.name}  {out.stat().st_size / 1e9:.2f} GB")
        shutil.rmtree(target)          # /kaggle/tmp is small; the GGUF is the artefact
    else:
        print(f"  CONVERSION FAILED (exit {done.returncode})")
        print(done.stdout[-2000:]); print(done.stderr[-2000:])

print()
for path in sorted(GGUF.glob("*.gguf")):
    print(f"{path.stat().st_size / 1e9:6.2f} GB  {path.name}")
print("\nDownload each .gguf individually from the Output panel -- they are NOT in the zip.")
"""
