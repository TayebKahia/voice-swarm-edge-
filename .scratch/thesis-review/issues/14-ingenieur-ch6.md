# Issue 14: ingenieur-ch6

Status: closed
Blocked by: 13
Chapter: thesis/ingenieur/ch6_conclusion.tex (390 lines, lead-in + 4 sections: 6.1 Demonstration protocol, 6.2 Limitations, 6.3 Future work, 6.4 Conclusion; cites: pyflyt, koren1991; drafted Thu 24 Sep in bd2ba37; STATE.md record: "Writing progress -- Ingenieur Ch 6 (B11)")
Script: tools/review/ingenieur_ch6.py
Report: .scratch/thesis-review/reports/ingenieur_ch6.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/ingenieur_ch6.py
```

At opening: 0 FAIL, 0 WARN, 81 PASS; 0 significant numbers untraced.

## Agents

- **Reviewer** -- D1, D2, D4, D5c, D6, D8, D10, D11, D12:
  - **Structure and outline (D1):** Four sections strictly mapped: 6.1 Demonstration protocol, 6.2 Limitations, 6.3 Future work, 6.4 Conclusion.
  - **Demonstration Protocol (6.1):** Part A (offline smoke test on recorded audio) and Part B (live tethered speech demonstration); references Table~\ref{tab:demo-script}; four explicit success criteria fixed before the defence.
  - **Limitations (6.2):** Rigid-body dynamics in PyFlyt vs kinematic backend: PyFlyt advances 10 physics steps at 240 Hz per control tick (41.67 ms), yielding an effective 24 Hz control rate rather than 48/50 Hz; evaluated across 600 ticks (25 s); exercised only by smoke tests on seed 42 for 12 s checking terminal position within 0.5 m, without collision logging or separation clamp. Separation clamp: intervened 432 times across 144 of the 150 trials at 0.800 m (collision threshold 0.50 m); velocity commanded at 2.0 m/s vs 3.0 m/s ceiling. Acoustic degradation: safe-failure rate 0.032 clean, remains between 0.014 and 0.039 under noise; golden set reference text yields 13 failures, 0 safe failures. Criteria summary inherits Table~\ref{tab:requirements-summary}: 7 met, 5 missed with confirmed causes (reflex latency, e2e latency, preemption recovery, clean CRR, noise CRR), 2 not demonstrated (KWS FA, KWS FR), 2 not yet run (offline STT, offline operation), 1 planned for defence (live demo).
  - **Future work (6.3):** Three prioritized directions: (1) dynamic potential fields / real-time collision avoidance citing Koren & Borenstein 1991 (\cite{koren1991}); (2) prompt prefix caching in llama.cpp to drop prefill from 751 ms to within 250 ms allowance; (3) socket-level cancellation / signal handling in llama-server to replace 1 s HTTP polling and achieve client's 6 ms cancellation latency; acoustic front-end training.
  - **Conclusion (6.4):** Direct, unhedged answers to RQ2 and RQ3. No hedging words (may, might, could, perhaps, possibly, likely, suggests, appears, seems). RQ1 cited from Mémoire de Master in one sentence. Locked collision phrasing: "zero collisions were observed, backed by a hard geometric separation clamp". Formation accuracy 1.000 vs >= 0.85 requirement. Cancelled decodes: 78 of 78 cancelled, 0 late dispatches, 0 cross-triggers.
  - **Number inheritance:** Every figure in Ch6 must be traceable to earlier chapters or results/; no new measurement may be introduced in Ch6.
- **Verifier:**
  - Verify reviewer findings against chapter text, commit history, and `tools/review/ingenieur_ch6.py`.

## What the script establishes (baseline: 0 FAIL, 0 WARN, 81 PASS)

- Outline check (demonstration protocol, limitations, future work, conclusion).
- Protocol check (Table tab:demo-script referenced, Part A and Part B defined, four criteria stated).
- All measured figures verified against results/ (exp2.csv, exp3_pi.csv, exp4.csv, wake_real_voice.json, wake_training.json).
- Number inheritance: 0 significant numbers introduced; every figure was reported in Ch5 or earlier.
- Register check: 0 hedging words in Section 6.4; no unearned absolutes ("guarantee" absent, "budget met" absent).

## Seeded findings

None.

## Comments

### 2026-09-24 -- review round 1 (1 reviewer + verifier)

**Script.** 0 FAIL, 0 WARN, 81 PASS. All numbers trace cleanly to `results/` or earlier chapters. Agent reports: `.scratch/thesis-review/agents/14-ingenieur-ch6/reviewer.md`, `.scratch/thesis-review/agents/14-ingenieur-ch6/verifier.md`.

**Verdict.** Ready after minor fixes; zero BLOCKER, zero MAJOR. Five minor/nit items identified and applied:
- **MINOR-1 (D8g):** l.138-141: 58-word sentence joining controller mapping with state feedback reporting split into two clear sentences.
- **NIT-1 (D8d):** l.162: American spelling `idealized kinematics` corrected to British `idealised kinematics`.
- **NIT-2 (D8d):** l.196: American spelling `formation maneuvers` corrected to British `formation manoeuvres`.
- **NIT-3 (D8d):** l.294: American spelling `attitude stabilization` corrected to British `attitude stabilisation`.
- **NIT-4 (D8d):** l.301: American spelling `optimized acoustic model` corrected to British `optimised acoustic model`.

**Verified findings table:**

| # | Sev | Line | Finding | Verifier | Fix |
|---|---|---|---|---|---|
| MINOR-1 | MINOR | 138-141 | 58-word sentence joining controller mapping with state feedback reporting. | CONFIRMED | Split into two sentences: "The controller accepts only a formation (Section~\ref{sec:swarm-controller}), while the script also commands a take-off, a movement, a hold, a landing and an abort, so each of these needs a mapping onto the controller. In addition, the state machine's transitions at the take-off height and on ground contact, like the reset, require the vehicles' state reported back to it." |
| NIT-1 | NIT | 162 | American spelling `idealized kinematics`. | CONFIRMED | Replaced with `idealised kinematics`. |
| NIT-2 | NIT | 196 | American spelling `formation maneuvers`. | CONFIRMED | Replaced with `formation manoeuvres`. |
| NIT-3 | NIT | 294 | American spelling `attitude stabilization`. | CONFIRMED | Replaced with `attitude stabilisation`. |
| NIT-4 | NIT | 301 | American spelling `optimized acoustic model`. | CONFIRMED | Replaced with `optimised acoustic model`. |

All 5 fixes applied to `thesis/ingenieur/ch6_conclusion.tex`.
Verification after fixes:
- `tools/review/ingenieur_ch6.py`: 0 FAIL, 0 WARN, 81 PASS.
- Clean XeLaTeX build: 0 errors (`^!`), 0 undefined references/citations, 0 dropped floats.
- Status: closed.
