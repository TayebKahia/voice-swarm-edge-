# Spike S3 Report: GBNF Grammar Smoke Test

- **Date:** 2026-09-07
- **Owner:** Agent (executed end-to-end)
- **Grammar File:** `schema/cmd.gbnf` (2193 bytes, 48 lines)
- **Status:** PASS

## Test Corpus
- **Valid Command Strings ($N=20$):** Covered all 10 intents (`formation`, `move`, `altitude`, `takeoff`, `land`, `hover`, `abort`, `rotate`, `set_param`, `unknown`), optional slots, and numeric boundary values.
- **Structurally Adversarial Strings ($N=20$):**
  1. Exponential notation (`1e999`)
  2. 20-digit integer overflow
  3. Bare trailing decimal (`2.`)
  4. Two decimal digits (`2.55`)
  5. Both `pos` and `dir` provided to `move`
  6. Neither `pos` nor `dir` provided to `move`
  7. Extraneous space outside literals (`"move", "pos"`)
  8. Trailing comma in JSON (`"abort",}`)
  9. Non-ASCII unicode character in shape name
  10. Unsupported shape identifier (`triangle`)
  11. Unsupported direction identifier (`diagonal`)
  12. Explicit null value (`"z":null`)
  13. Explicit null list (`"ids":null`)
  14. Double minus (`--90.0`)
  15. Leading decimal without zero (`.5`)
  16. Missing required shape in `formation`
  17. String value in numeric slot (`"speed":"fast"`)
  18. Extra slot in `unknown`
  19. Illegal slot in `hover`
  20. Illegal slot in `abort`

## Results
- **Valid Strings Accepted:** 20/20 (100%)
- **Adversarial Strings Rejected:** 20/20 (100%)
- **Structurally Invalid Emissions:** **0** (Pass condition met)

## Architectural Role
GBNF enforces structural validity at Layer 1 in the constrained decoder. Semantic constraints (e.g. physical envelope clamping, deduplicating IDs, requiring at least one slot in `set_param`) are enforced at Layer 2 (`schema/validate.py`), ensuring defense-in-depth without grammar over-complexity.
