# Issue 09: master-ch6

Status: ready-for-agent
Blocked by: 05
Chapter: thesis/master/ch6_conclusion.tex (107 lines, no \cite; chapter `602447e`, STATE.md record `c2da438`)
Script: tools/review/master_ch6.py
Report: .scratch/thesis-review/reports/master_ch6.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch6.py
```

## Agents

- **Reviewer** -- D1, D2, D4, D6, D8, D10, D11, D12, and D5c only: there are no citations, so look
  for literature or tool claims that need one. D3 is the script's job. Focus:
  - **Unhedged means no hedging words, not stronger claims.** No Ch4 figure may carry a stronger
    qualifier in Ch6 than Ch4 gave it. The qualifiers are "significant" and "established"
    (Ch4 §4.6 l.290, §4.7 l.372), "exploratory" (the family control, Ch4 l.173) and "not
    distinguishable" (Ch4 l.296).
  - **No new caveat** (SKILL.md, Ch6). A limitation that first appears here belongs in Ch5, so
    report it as a Ch5 finding.
  - **The RQ1 verdict must match Ch4 §4.7** (l.349-392) **and Ch5 §5.1** (l.52-64):
    - Qwen2.5-0.5B Q4\_K\_M is selected on EM against re-baselined constraints.
    - It misses 2,500 ms as specified by 622 ms (25%).
    - The budget is re-baselined to 3,122 ms (n = 226).
    - Memory is confirmed for the language-model process only.
    - If the rule is restated, it says "satisfying", never "not ruled out" (issue 04, option B).
      Ch4 l.378 uses "not ruled out by the memory ceiling" for memory (issue 04 A10). That use is
      correct and is not a restatement of the rule.
  - **The three next steps must match** Ch5's closing hand-off (`ch5_discussion.tex`, final
    paragraph) and §5.2 (l.174-177):
    1. the confidence gate;
    2. training pairs mapping degraded commands to `unknown`;
    3. the end-to-end measurement of SmolLM2-360M (the hand-off places it in §5.1).
  - **The 81 unknown training pairs.** Ch6 must agree with Ch3 l.174-180 as corrected in `644c8fb`:
    20 assistant queries, 21 unsupported capabilities and 40 lexical near-misses, none of them a
    supported command made unreadable.
  - **"What the comparison establishes"** must cover each contribution C1-C3 exactly as Ch1 states
    it (`ch1_introduction.tex` l.107-125), and claim nothing Ch1 did not promise.
  - **Carried from STATE.md** (the Ch6 entry; this is a check, not a finding). Ch6 was checked against
    a working-tree Ch5 before issue 05's edits were committed (`f1f7732`, `c985c13`, `535352c`,
    `1bd566e`). Re-read 6.2 P2 and 6.3 against Ch5 as committed, in particular the 5.2 taxonomy
    paragraph and the 5.3.1 untuned-baseline paragraph.
- **Verifier.**

## What the script establishes (baseline: 0 FAIL, 0 WARN, 54 PASS)

- Every Ch6 figure is recomputed from the file Ch4 draws it from: `surface_b.csv`,
  `surface_b_nogrammar.csv`, `surface_a.csv`, `exp1_cooled.csv` / `exp1.csv` (nearest-rank p95),
  `exp2_latency_budget.md`, `mcnemar.csv`, the abstention CSV and `data/train.jsonl` (81 `unknown`
  rows).
- Any significant number that appears in no earlier chapter is a FAIL.
- Hedging words FAIL.
- Five banned phrasings are absent: "budget met", "oversampling", "only instance",
  acoustic-robustness/Exp-N, and "guarantee".
- The prd.md §3.1 outline maps to the three sections, and the first paragraph of 6.1 answers RQ1.

## Seeded findings

None.

## Comments
