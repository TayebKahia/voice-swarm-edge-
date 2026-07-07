# ADR-0001: Physical Envelope Analogies, Coordinate Clamping, and Angular Wrapping

- **Status:** Accepted
- **Date:** 2026-09-07 (D1 Freeze)
- **Author:** PFE Swarm Edge Architecture

## Context
PRD §5.2 and Roadmap §2.4 specify the Layer 2 physical safety envelope with the core directive:
> **"Physical envelope --- CLAMP AND LOG, NEVER REJECT. A clamped command is safer than a dropped one."**

The PRD explicitly tabulates ranges for:
- `radius` $\in [1, 10]$ m
- `spacing` $\in [1, 5]$ m
- `z` $\in [0.5, 15]$ m
- `speed` $\in [0.2, 2.0]$ m/s
- $|pos| \le 50$ m (Euclidean norm)
- `yaw` $\in [-180, 180]^\circ$

However, two slots emitted by `cmd.gbnf` lacked explicit bounds in Table 14, and the 3D position vector $|pos| \le 50$ m required geometric resolution regarding vertical bounds and angular coordinate representation.

## Decisions

### 1. Analogous Envelope Extensions
- **`dist` (travel distance in relative move): $[0.0, 50.0]$ m.**
  - *Rationale:* Governs relative displacement ($\text{dir} + \text{dist}$). Set by direct analogy to the arena boundary radius $|pos| \le 50.0$ m. Negative distance is clamped to $0.0$ m.
- **`alt` (target altitude parameter in `set_param`): $[0.5, 15.0]$ m.**
  - *Rationale:* Governs default altitude setpoint. Set by direct analogy to vertical flight bounds $z \in [0.5, 15.0]$ m.

### 2. 3D Position Vector (`pos`) Clamping & Ordering Decision
- A commanded waypoint $pos = [x, y, z]$ has distinct horizontal and vertical physical constraints:
  1. **Vertical Bounds Priority ($z$):** Must satisfy ground floor $z \ge 0.5$ m (prevent ground collision) and ceiling $z \le 15.0$ m (prevent airspace breach). The $z$ component is strictly clamped to $[0.5, 15.0]$ m first.
  2. **Total Arena Norm ($|pos|$):** The Euclidean norm $\sqrt{x^2 + y^2 + z^2} \le 50.0$ m. If the norm exceeds $50.0$ m, the horizontal displacement $(x, y)$ is scaled so that $\sqrt{x^2 + y^2} \le \sqrt{50.0^2 - z^2}$. This preserves the commanded horizontal heading and ensures the 3D position vector remains within the 50 m sphere without dragging the vertical altitude below the $0.5$ m ground floor. Rounding to 1 decimal place is guarded so the resulting norm never exceeds $50.0$ m.

### 3. Periodic Angular Domain Wrapping (`yaw`)
- Yaw is an angular heading in degrees, inherently periodic modulo $360^\circ$.
- Clamping $360^\circ \to 180^\circ$ or $270^\circ \to 180^\circ$ introduces artificial maximum angular errors ($90^\circ$ to $180^\circ$).
- Therefore, `yaw` is normalized into the canonical interval $[-180.0, 180.0]^\circ$ via modulo wrapping:
  $$\text{yaw}_{\text{wrapped}} = ((\text{yaw} + 180) \pmod{360}) - 180$$
- Any wrap is logged as a structured normalization event.

### 4. Finite Numeric Assurance (NaN and Infinity Protection)
- All floating-point inputs must be finite (`math.isfinite`).
- Non-finite values (`NaN`, `+Inf`, `-Inf`) cannot be safely clamped to physical coordinates. Any non-finite coordinate or slot triggers Layer 2 validation failure, resolving to a safe `HOVER` command with a structured log entry.

## Consequences
- Guarantees 100% finite, valid JSON output from `canon()`.
- Eliminates underground ($z < 0.5$ m) or stratospheric ($z > 15$ m) setpoints via `move.pos`.
- Eliminates large angular heading errors from operator commands exceeding $180^\circ$.
