# Issue 06: ingenieur-ch1

Status: ready-for-agent
Blocked by: 05
Chapter: thesis/ingenieur/ch1_introduction.tex
Script: tools/review/ingenieur_ch1.py
Report: .scratch/thesis-review/reports/ingenieur_ch1.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/ingenieur_ch1.py
```

## Agents

- **Argument agent** -- D1, D2, D4, D6, D10. Focus: every design promise the safety argument makes
  (membership rule, clamp placement, three layers) listed with the chapter that must deliver it,
  for the Ch3-Ch6 reviews; the locked NFR-12 phrasing at each occurrence; requirement paraphrases
  that narrow or widen scope (report's wording table).
- **Citation / presentation agent** -- D5 (12 citations: stpa, avizienis2004, koren1991, relays2s,
  mira, ...), D7, D8, D9, D11, D12.
- **Verifier.**

## What the script establishes (baseline: 5 FAIL, 29 WARN, 52 PASS; the 5 FAILs are D11)

- RQ2, RQ3 and C4 are prd.md §2 verbatim; C1-C3 not claimed.
- Every NFR target matches prd.md Table 12; counts (12 FR, 21 NFR rows, 6 remaining, "more than
  sixteenfold") are right; no measured result is quoted, as the chapter promises.

## Seeded findings

- Both requirement tables are first `\ref`'d after the float (l.87 vs l.72; l.126 vs l.106).
- FR-11 verification reworded ("every state x command cell" vs prd's "`test_fsm.py` covering every
  cell of Table 9") -- equivalent?
- Labels the unwritten chapters must carry: chap:architecture, chap:implementation,
  chap:validation, chap:demonstration.

- **D11**: Exp-2/3/4 and Branch A/B used in Ch1 but defined nowhere yet -- define them here,
  at first use, even though Ch3 and Ch5 will describe them. RQ1/RQ2, NFR-14/15/16 are used a few
  lines before their table rows.
- **D12**: flourishes to judge -- "FR-6 is worth reading twice", "The vocabulary of failure has one
  word in it."

## Comments
