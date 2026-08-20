# Issue 05: master-ch5

Status: ready-for-agent
Blocked by: 04
Chapter: thesis/master/ch5_discussion.tex (§5.1 written; §5.2, §5.3.1, §5.3.2 and the lead-in are \TODO)
Script: tools/review/master_ch5.py
Report: .scratch/thesis-review/reports/master_ch5.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch5.py
```

## Agents

- **Reviewer** -- D2, D4, D5, D6, D8, D10, D11, D12 on §5.1. Focus: Ch5 may not quote a Ch4 figure with a
  stronger qualifier than Ch4 gave it; no RQ1 verdict (Ch6's); "modest" margin at n = 60 on one board.
- **Verifier.**
- Re-run this issue when §5.2-5.3 are drafted, adding claims to the script first.

## What the script establishes (baseline: 0 FAIL, 19 WARN, 37 PASS)

- Every §5.1 figure recomputed (178 ms, 0.13 GB, 17.5 pp, 1,210 ms, 0.95 GB, 1,771.5 and 1,610.2 ms
  uncooled, the 67 ms / 6% decode margin). No number appears that Ch1-Ch4 did not report.

## Seeded findings

- l.40 "more than a third of the distance": 6.5 pp is a Surface-A (FP16) gap and 17.5 pp a
  Surface-B (Q4_K_M) gap -- the ratio mixes surfaces without saying so.

- **D12**: three lead-ins are claims ("The knee belongs to a model, not to a size.", ...).

## Comments
