# Issue 07: ingenieur-ch2

Status: ready-for-human
Blocked by: 06
Chapter: thesis/ingenieur/ch2_state_of_the_art.tex (scaffold: headings and NOTEs, no prose)
Script: tools/review/ingenieur_ch2.py (exits 2 while the chapter is a scaffold)
Report: .scratch/thesis-review/reports/ingenieur_ch2.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/ingenieur_ch2.py
```

## Now (before any prose)

- All 28 citation keys the NOTEs plan to use are in references.bib.
- **Decide first**: the scaffold has three sections prd.md §3.1 does not list -- Swarm control,
  Offline speech components, Gap. SKILL §3: change prd.md, then the scaffold, never the prose alone.

## After the prose is drafted (Status -> ready-for-agent)

- **Citation agent** -- D5 against both the paper and the claim recorded for each key in
  `.scratch/thesis-bibliography/ingenieur-candidates.md` (several were corrected).
- **Argument agent** -- D1, D2, D4, D6: the Gap concedes CommandSwarm and SkySim by name and must
  answer MIRA; no Master-owned literature re-surveyed (the script FAILs on it).
- **Verifier.**

## Comments
