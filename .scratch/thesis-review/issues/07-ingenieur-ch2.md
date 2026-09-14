# Issue 07: ingenieur-ch2

Status: closed
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

### 2026-09-24 -- outline decided: all five sections kept, prd.md amended

The "decide first" item is settled. The author keeps Swarm control, Offline speech components and
Gap. The change followed SKILL §3 order: prd.md first, then the scaffold (unchanged, since it
already had the five sections), then the prose.
- prd.md §3.1 item 2 now reads: "State of the art: voice-controlled UAV systems; positioning
  against Lim et al. [1]; swarm control; offline speech components; the gap this document fills."
  A dated note under the Ingénieur list gives the reason. prd.md is untracked, so this comment and
  the commit are the record.
- SKILL.md §3 (Ingénieur item 2) is updated to match.
- `tools/review/ingenieur_ch2.py` checks all five topics. The "sections beyond prd.md" WARN is
  gone: 0 FAIL, 7 WARN, 41 PASS, exit 2 (scaffold; the WARNs are "no prose yet" plus `UAV` typed
  in the first section title).

Open for the drafting: the section order is the scaffold's (positioning against Lim et al.
second, gap last). An alternative is survey first (voice UAV, swarm control, speech components),
then positioning, then gap, so that the comparison follows the material it draws on. The author
decides when drafting; prd.md must then list the new order.

Status stays `ready-for-human` until the prose is drafted.

### 2026-09-24 -- prose drafted (7ad9bc4); Status -> ready-for-agent

All five sections drafted in the scaffold's order (kept, so prd.md is unchanged). Script: 0 FAIL,
3 WARN (justified in the commit message), exit 0. Clean build, 0 errors, 0 undefined refs.

For the review agents:
- **No Table 21.** The scaffold's promise of a quantitative Lim comparison in Ch5 was dropped; the
  positioning is tab:lim-positioning in Ch2, explicitly by design point. Check Ch1 l.448-450 still
  agrees ("the baseline against which this work is compared").
- **Citation agent:** every key must carry only its recorded claim. Highest-risk sentences:
  - MIRA (Gap, "The membership rule"): the contrast "preemption acts on the robot's own response"
    and "not designed for offline operation" rest on the abstract and the scaffold NOTE. Read the paper.
  - SkySim: geofence -> position hold (conceded); malformed output -> previous command retained.
  - CommandSwarm: 4.0 s SeamlessM4T is compared with the 2,500 ms budget "on unstated hardware".
  - tab:voice-uav-survey: every non-dash cell must be traceable to ingenieur-candidates.md.
  - speechcmd (Warden) is cited for "KWS is a distinct task with its own methodology"; its
    candidate entry has no "Verified" line.
- **Argument agent:** the Gap concedes (i) to CommandSwarm and (ii) to SkySim and claims (iii) and
  (iv); check that (iv) is framed as a setting, not as a contribution, consistent with Ch1
  sec:contributions.
- Licences in "Offline speech components" come from installed package metadata, not from a paper.

### 2026-09-24 -- scoped citation check run and applied (feb7371); Status -> closed

**Scope, stated so nobody mistakes this for the full review:** one agent, citations only (D5),
against the full MIRA, CommandSwarm and SkySim papers, the arXiv abstracts of TypeFly, Warden,
Henry and Contreras, and the verified claims in ingenieur-candidates.md for every survey-table
cell. The argument agent (D1, D2, D4, D6) and the separate verifier of spec.md were NOT run,
because of the depot deadline. Chosen by the author.

Findings: 1 load-bearing (the MIRA contrast; its fast gate aborts on voice activity alone and then
holds, so "originates vs withdraws" failed; now "one action vs a choice between two commands"),
1 unverifiable (MIRA offline), 6 over-statements (SkySim x2, CommandSwarm simulation, the
"every LLM system checks" synthesis, the TypeFly cell and caption, Henry attribution). All 8 were
applied, with the author's approval. Everything else SUPPORTS, including all CommandSwarm facts,
the remaining SkySim facts, speechcmd, and all other table cells.

After the fixes: script 0 FAIL / 3 WARN (justified), clean build 0 errors.
Left for after the depot, if ever: the argument pass. The whole-document pass (issue 10) should
check that Ch1 sec:contributions and Ch6's "System contribution" paragraph still agree with the
Gap as rewritten (the contribution is the membership rule for a path that CHOOSES between commands;
preemption and an uninterpreted stop are conceded to MIRA).
