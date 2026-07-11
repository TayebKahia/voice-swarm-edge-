# ADR-0002: Flight State Machine Rejection Fallbacks and Canonicalisation Exports

## Context & Problem

In `IMPLEMENTATION_ROADMAP.md` §2.5, the specification for Layer 3 (`swarm/fsm.py`) states:
> "Table 9 --- legality. Rejections resolve to `HOVER` with a log entry."

However, Table 9 explicitly declares `hover` illegal in states `LANDED`, `LANDING`, and `ABORTED`:
- In `LANDED`, dispatching `Hover` commands rotors to spin up and hover, which violates Table 9 and initiates uncommanded flight.
- In `LANDING`, dispatching `Hover` would arrest the descent at altitude, leaving the swarm hanging mid-descent.
- In `ABORTED`, the swarm has terminated motors and cannot hover until manual reset.

Similarly, in `IMPLEMENTATION_ROADMAP.md` §2.6, the specification for `schema/canon.py` states:
> "Exposes exactly one function, `canon(obj)`, applied to both prediction and reference before any comparison."

In implementation, two additional interfaces were provided:
- `canon_equal(a, b)`: A direct boolean equality helper comparing two commands after canonicalisation.
- `_Command.to_wire()`: A convenience method on Pydantic models invoking `canon(self)`.

## Decisions

### 1. FSM Rejection Resolution per Table 9

Rejections in `swarm/fsm.py` resolve strictly according to whether `hover` is legal in the current flight state:

1. **Where Hover is Legal (`TAKING_OFF`, `FLYING`):**
   An illegal command rejection resolves to `Hover(intent="hover")` accompanied by a structured `fsm_command_rejected` log with `"action": "fallback_hover"`.

2. **Where Hover is Illegal (`LANDED`, `LANDING`, `ABORTED`):**
   An illegal command rejection resolves to a safe no-op (`None`) accompanied by a structured `fsm_command_rejected` log with `"action": "noop_hover_illegal"`.
   - In `LANDED`: Drones stay grounded safely.
   - In `LANDING`: Drones continue descent uninterrupted.
   - In `ABORTED`: Drones remain in the safety reflex state.

3. **Audit Trail Preservation:**
   `swarm/fsm.py` inspects the raw user payload (`cmd_input`) prior to Layer 2 fallback to preserve the operator's original intent (`raw_intent`) in the rejection log, ensuring that Gate 4 accurately tracks which intent was rejected.

4. **Emergency Abort with Stray Slots:**
   In `schema/validate.py`, if an operator issues an emergency `abort` containing stray slots (e.g. `{"intent":"abort","ids":[0]}`), the stray slots are dropped with a structured `slot_dropped` log and the intent resolves strictly to `Abort()`. It NEVER degrades to `Hover()`.

### 2. Canonicalisation Exports

`schema/canon.py` maintains `canon(obj)` as the canonical single comparator. To eliminate code duplication across evaluation and testing harnesses:
- `canon_equal(a, b)` is exported as a helper that evaluates `canon(a) == canon(b)`.
- Model methods (`to_wire()`) delegate to `canon(self)`.

Both helpers share the identical underlying implementation of `canon()`, ensuring zero semantic divergence.
