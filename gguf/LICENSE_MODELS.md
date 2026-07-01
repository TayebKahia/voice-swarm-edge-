# Model licences

Six quantised artefacts: three base models × two quantisations
(**Q8_0** ≈ 8.5 bits/weight, **Q4_K_M** ≈ 4.85 bits/weight).

**Check this file before publishing any merged weights, and before burning the
DVD for the centre de calcul.** Two of the three licences are permissive; one is
not, and it carries obligations that survive fine-tuning.

---

## Base models

| Model | Params | Licence | Obligation |
|---|---|---|---|
| Qwen2.5-0.5B-Instruct | 0.5 B | Apache-2.0 | Retain notice |
| SmolLM2-360M-Instruct | 360 M | Apache-2.0 | Retain notice |
| Llama-3.2-1B-Instruct | 1 B | **Meta Llama 3.2 Community Licence** | See below |

## Llama-3.2 — the one that constrains you

The Meta Community Licence is **not** Apache-2.0. It requires, at minimum:

- **Attribution.** State that the model is built with Llama.
- **Naming.** A derivative's name must include *Llama*.
- **Licence propagation.** Ship the licence text and the Acceptable Use Policy
  with any redistributed weights.

A LoRA adapter merged into Llama-3.2 weights **is** a derivative. The obligation
follows the artefact, so it applies to the DVD delivered to the centre de calcul
just as it does to a public upload.

If Llama-3.2 turns out not to be the deployed configuration, the artefacts still
exist in the comparison and this section still applies to them.

---

## Artefacts

| File | Base | Quantisation | Size | SHA-256 |
|---|---|---|---|---|
| TBD | Qwen2.5-0.5B | Q8_0 | TBD | TBD |
| TBD | Qwen2.5-0.5B | Q4_K_M | TBD | TBD |
| TBD | SmolLM2-360M | Q8_0 | TBD | TBD |
| TBD | SmolLM2-360M | Q4_K_M | TBD | TBD |
| TBD | Llama-3.2-1B | Q8_0 | TBD | TBD |
| TBD | Llama-3.2-1B | Q4_K_M | TBD | TBD |

Deployed configuration: **TBD** — selected by Exp-1 and Exp-2.

---

## Toolchain

Quantisation is not reproducible without the exact build. Record commit SHAs,
not version numbers.

| Tool | Commit SHA | Recorded at |
|---|---|---|
| `llama.cpp` (`llama-quantize`, `llama-cli`, `llama-bench`) | TBD | spike S1 |
| `whisper.cpp` (`tiny.en`, `base.en` Q5) | TBD | spike S2 |

---

## Other licensed components

| Component | Licence |
|---|---|
| `whisper.cpp` models (tiny.en, base.en) | MIT |
| Silero VAD | TBD |
| openWakeWord | Apache-2.0 |
| Piper TTS + voice models | TBD — voices are licensed separately from the code |

Noise and speech corpora are licensed in [`../data/dataset_card.md`](../data/dataset_card.md).
