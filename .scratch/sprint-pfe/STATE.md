# STATE
Session: 01B (Tue 8 Sep, PRD D1/D2)
Last updated: 2026-09-08T15:10:00+01:00

## Gates
Gate 1 schema        : GREEN (pytest schema/ → 83 passed in 0.20s, tag schema-v1.1)
Gate 2 leakage       : READY (check_leakage.py --strict → exit 0; Session 02B formal gate)
Gate 3 parity        : PENDING (Session 05B)
Gate 4 fsm           : PENDING (Session 08; Table 9 legality & grounded rejection verified in swarm/test_fsm.py)
Gate 5 dataset frozen: PENDING (Session 03)
D1 Environment Gate  : GREEN (requirements.txt pinned, environment.yml exported)

## Artefacts
schema/                     : FROZEN (cmd.gbnf, schema.py, validate.py, canon.py, logger.py, test_grammar.py, test_canon.py)
                              - cmd.gbnf: verbatim from §2.3
                              - schema.py: 10 intent Pydantic models, declaration order fixes key order, nulls omitted
                              - validate.py: Layer 2 validator, slot matrix, clamp-and-log, pos.z ceiling/floor & norm clamp, yaw periodic wrapping, non-finite (NaN/Inf) rejection to HOVER, structured logging
                              - canon.py: canonicaliser rule 1-5, single comparator helper canon_equal(), non-finite protection, total id handling
                              - logger.py: structured JSON lines logging with LogRecord extra field preservation
                              - test_grammar.py: 72 tests (adversarial corpus, Layer 2 overflow/non-finite handling, all clamp boundaries from both sides, yaw wrapping)
                              - test_canon.py: 8 tests (rules 1-5, banker's rounding on dyadic fractions, canon_equal equivalence)
swarm/                      : fsm.py (Table 9 legality, grounded no-op on rejection in LANDED, airborne HOVER fallback), test_fsm.py (19 tests passing)
docs/adr/                   : 0001_physical_envelope_analogies.md (formal rationale for dist/alt bounds, pos.z clamping, yaw wrapping, and non-finite rejection)
data/template_families.json : AUTHORED & SYNCHRONIZED (120 families: 96 train [80%], 12 val [10%], 12 test_synth [10%])
data/template_families.py   : AUTHORED (dataclass and split assignments)
data/check_leakage.py       : AUTHORED & VERIFIED (template family integrity & cross-split surface-form near-duplicate lexical leakage check)
data/test_template_families.py: AUTHORED (6 tests passing)
spikes/s0..s7 scripts       : 8 scripts authored in spikes/
spikes/reports/S0..S7.md    : 8 spike reports in spikes/reports/:
                              - S0: PASS (noise floor -64.5 dBFS) / INCOMPLETE (loopback latency, Table 22 peak miss logged)
                              - S1: PROVISIONAL PASS (Q4_K_M passes at 20.97 tok/s @ -t 3; Q5_K_M fails at 18.16 tok/s; 1.5 GHz throttled)
                              - S2: PROVISIONAL / GATED (2,014 ms p95 @ -t 3 fails 1,200 ms; honest 2.4 GHz projection 2,591-2,984 ms fails NFR-2)
                              - S3: PARTIAL (llama.cpp build 10863 verified; unbounded idlist & zero-shot semantic collapse documented for S02A)
                              - S4: PASS (4.72x RTF workstation physics feasibility; closed-loop setpoint jitter scheduled for Exp-4)
                              - S5: PRE-REGISTERED (system prompt pinned for Gate 3 parity dump; SmolLM2 chatml mapping marked as hypothesis)
                              - S6: COMPLETE (tiny.en approved: 8.89% micro WER matches base.en; macro favors base.en; decided on compute)
                              - S7: DEFERRED / ARCHITECTURE ONLY (dual-path abort callback & mmap fallback designed; live C++ abort in Exp-2)
requirements.txt            : PINNED (all dependencies pinned with ==, conda header updated)
environment.yml             : EXPORTED (conda env pfe_swarm)
.scratch/sprint-pfe/spec.md : AUTHORED (16-day sprint plan, cut ladder, milestones)
.scratch/sprint-pfe/issues/ : Issue 01, 02 resolved; 24 pending human.

## Decisions this session
- Resolved Session 01B audit feedback:
  1. Non-finite values (`NaN`, `Infinity`): Caught by Layer 2 validator and safely rejected to `HOVER` with `validation_fallback` structured log; `canon()` refuses non-finite floats to prevent corrupt JSON row emission.
  2. `move.pos` safety envelope: Clamps $z \in [0.5, 15.0]$ m, then scales horizontal $(x, y)$ to satisfy norm $|pos| \le 50.0$ m while preserving the vertical altitude floor $z \ge 0.5$ m (ADR-0001).
  3. Yaw angular wrapping: Identity on canonical $[-180.0, 180.0]^\circ$; periodic modulo wrapping for out-of-interval angles (ADR-0001).
  4. FSM Table 9 compliance: Rejections in `LANDED`, `LANDING`, and `ABORTED` resolve to safe no-op (`None`), while airborne rejections in `TAKING_OFF` and `FLYING` resolve to `Hover()`. `json` imported and `BaseModel` check fixed so raw operator intent is faithfully preserved in audit logs (ADR-0002).
  5. Emergency abort safety: Stray slots on `abort` are dropped with `slot_dropped` structured log, resolving strictly to `Abort()` and never degrading to `Hover()` fallback (ADR-0002).
  6. Structured logging: Configured `"swarm"` and `"schema"` logger hierarchies via `schema/logger.py` `StructuredJsonFormatter`, capturing all `extra` fields.
  7. Superfluous slot policy: Superfluous slots (`spacing` on circle, `radius` on line/grid/column/wedge, `radius`/`spacing` on flock) are dropped with `slot_dropped` structured log, never rejecting the command.
  8. Authored ADR-0001 and ADR-0002 (`docs/adr/0002_fsm_grounded_rejection_and_canon_helpers.md`).
  9. Reconciled `issue-01` with measured S1/S2 spike reports.
  10. Gate 2 split leakage verification (`data/check_leakage.py`): Enforces family ID disjointness and surface-form lexical near-duplicate detection (> 0.85 Jaccard similarity) across splits; strict exit code hardened.
  11. GBNF `idlist` specification defect resolved (Item 3): Amended `idlist ::= [0-4] ( "," [0-4] ){0,4}` in `schema/cmd.gbnf:43`, eliminating hardware greedy decoding loops and bounding IDs to valid swarm range {0..4}. Verified in `schema/test_grammar.py` and tagged `schema-v1.1`.
- `schema/` and `swarm/`: All 119 tests pass green (Gate 1 verified, tagged `schema-v1.1`).

## Blocked / needs human
- Autorisation de soutenance: Requested Sep 6, pending formal receipt (tracked in Issue 24).

## Next session starts with
Session 02A Task 1. Label-first generation: run `data/generate.py`, author 200 `test_golden` transcripts from held-out template families, 2,400 raw pairs across 10 intents.

