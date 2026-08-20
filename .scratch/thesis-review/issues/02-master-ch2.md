# Issue 02: master-ch2

Status: ready-for-agent
Blocked by: 01
Chapter: thesis/master/ch2_related_work.tex
Script: tools/review/master_ch2.py
Report: .scratch/thesis-review/reports/master_ch2.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch2.py
```

## Agents

- **Citation agent** -- D5 only. Worklist: the report's citation sheet (34 citations, 16 keys) and
  "Numbers quoted from papers" (25 models, 3 SBCs, 2 runtimes, 1.5 B ceiling, 4x spread, <1%
  perplexity, >= 7 B, 1 M examples). Open each identifier; verdict per row SUPPORTS / PARTIAL /
  DOES NOT SUPPORT / COULD NOT ACCESS. `.scratch/thesis-bibliography/master-candidates.md` is a
  lead, never evidence.
- **Argument agent** -- D1, D2, D4, D6, D8, D10, D11, D12. Focus: the Gap paragraph claims four literatures
  are *silent*; that holds only for the papers cited. And the Delta credits C1 with isolating the
  grammar's contribution, which is the ablation's (C3's) doing.
- **Verifier.**

## What the script establishes (baseline: 0 FAIL, 13 WARN, 34 PASS)

- Four theme sections plus one closing Positioning with Synthesis / Gap / Delta.
- Positioning cites nothing the theme sections did not review.
- No voice-UAV literature (Table 3 gives it to the Ingénieur); no Outlines; all four models cited.

## Seeded findings

- "guarantee" used twice about the grammar (l.83, l.101) -- earned for a by-construction property?
- Acronyms by hand: LLM, CPU, GPU, GGUF, GGML, BNF, GBNF.
- The master-candidates notes flag a tension with C3's framing -- the argument agent reads it.

## Comments
