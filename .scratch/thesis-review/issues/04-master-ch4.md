# Issue 04: master-ch4

Status: ready-for-agent
Blocked by: 03
Chapter: thesis/master/ch4_results.tex
Script: tools/review/master_ch4.py
Report: .scratch/thesis-review/reports/master_ch4.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch4.py
```

## Agents

- **Argument / statistics agent** -- D2, D4, D6, D10. Focus: register (Results reports, Ch5
  interprets); "upper bound" (l.14); interpretations with no computed figure behind them
  ("predominantly parameter errors", "two-fifths"); the two McNemar cautions.
- **Citation agent** -- D5 (11 citations).
- **Presentation agent** -- D7, D8, D9, D11, D12: the six `\input{generated/...}` tables and Figure 2
  (vector, caption self-contained), clean build.
- **Verifier.**

## What the script establishes (baseline: 7 FAIL, 17 WARN, 155 PASS; all 7 FAILs are D11, every number is right)

155 claims recomputed from `surface_b*.csv`, `surface_a.csv`, the per-trial rows of
`exp1_cooled.csv` / `exp1.csv` (nearest-rank, half-up rounding), `mcnemar.csv`,
`nfr9_nfr18_abstention.csv` and table16/33 -- every one matches. The selection rule was
re-applied: exactly one configuration (Qwen2.5-0.5B Q4_K_M) meets all six constraints.

## Seeded findings

- "GB" is MiB / 1024 (GiB): Llama's peak RSS is 1,670 MB = 1.67 GB decimal, written 1.63 GB.
  State the unit once or write GiB -- the same convention runs through Table 17.
- fig:pareto is first `\ref`'d in this chapter at l.328, after the float (l.310).

- **D11**: Exp-0/1/2/3 undefined; "the hardware specification", "the project specification",
  "the escalation rule" (l.97, l.141).
- **D12**: 9 lead-in headings are sentences or claims ("NFR-2 has not been measured, and cannot be
  decided here.", "Schema validity is 1.0000 everywhere, ...").

## Comments
