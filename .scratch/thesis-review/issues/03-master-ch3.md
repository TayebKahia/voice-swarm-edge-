# Issue 03: master-ch3

Status: ready-for-agent
Blocked by: 02
Chapter: thesis/master/ch3_method.tex
Script: tools/review/master_ch3.py
Report: .scratch/thesis-review/reports/master_ch3.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch3.py
```

## Agents

- **Reproducibility agent** -- D3 (UNTRACED rows only) and D10a: could an outsider rerun Method from
  this chapter alone? Every named script is checked for existence by the script; this agent checks
  it is the one that actually ran.
- **Argument agent** -- D1, D2, D4, D6. Focus: l.330 calls A - B "Contribution C3" while Ch1 defines
  C3 as the harness; the three-layer "guarantee" (l.40); the Table 3 hand-offs to the Ingénieur.
- **Citation agent** -- D5 (18 citations).
- **Presentation agent** -- D7, D8, D9, D11, D12, including the clean build (tab:metrics is an xltabular:
  grep the PDF for its last row, "Convergence").
- **Verifier.**

## What the script establishes (baseline: 16 FAIL, 43 WARN, 98 PASS; 15 of the FAILs are D11)

- The grammar listing is `schema/cmd.gbnf` verbatim; the ten intents are the grammar's ten.
- Every LoRA setting matches all four `train/configs/*.yaml`.
- Dataset sizes within 5% of `data/*.jsonl`; the 4.0-day interval and zero disagreements
  recomputed from the annotation seal and pass-2 timestamps; 514 / 494 = 4.0%.
- NFR targets in tab:requirements match prd.md Table 12 on numbers and bound direction.

## Seeded findings

- **FAIL**: `FA` = Formation accuracy (l.466) but `\gls{fa}` = False Acceptance in
  `shared/acronyms.tex`. One of them needs a new abbreviation.
- `Table~19` (l.105) and `Table~18` (l.331) hand-typed -- use `\ref{tab:grammar-ablation}`,
  `\ref{tab:quantisation-delta}`.
- NFR-9a "Measured by: Exp-1, Exp-2" vs prd.md "Exp-1" -- the chapter text justifies Exp-2; decide
  whether prd.md or the table changes.
- "close to a full second" (l.36): 22 tokens is 0.79 s at the measured 27.93 tok/s, 1.10 s at the floor.
- **D11**: Exp-0 to Exp-4 used ~50x, never defined; "triaged" x5, "spike-era", "the build
  schedule this project executed against", "the project specification", "escalation rule".
- Outside the chapter: `data/dataset_card.md` says "a two-day interval" beside its own 4.0-day table.

## Comments
