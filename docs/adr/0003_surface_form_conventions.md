# ADR-0003: Surface-Form Conventions for Synthetic Generation

**Status:** Accepted (Session 02A)
**Supersedes:** nothing. **Amended by:** nothing.

## Context

Label-first generation (`02_dataset_plan.md` §3.1) constructs the JSON label
first and then produces text for it. That makes the label correct by
construction, but it does not make the *mapping* obvious: several English phrases
are genuinely ambiguous about which label they denote, and the PRD does not
adjudicate them. Whatever the corpus decides becomes what the fine-tuned model
believes, so each decision below is a semantic commitment, not a formatting
preference.

Three needed deciding before `data/generate.py` could emit a row, and one more
came out of `02_dataset_plan.md` §3.3 while authoring the hard negatives.

## Decision 1 --- Yaw sign: positive is counter-clockwise, so positive is *left*

`schema/cmd.gbnf` admits `yaw` in [-180, 180] and the PRD fixes the range
(Table 6) but not the sign. We adopt the ROS/ENU convention already implicit in
the `pos` frame: **yaw is measured counter-clockwise seen from above**, so

- `"turn left ninety degrees"`  -> `{"intent":"rotate","yaw":90.0}`
- `"turn right ninety degrees"` -> `{"intent":"rotate","yaw":-90.0}`

and cardinal headings, if a later version adds absolute-heading phrasing, are
East = 0, North = 90, West = 180, South = -90.

**Why.** The alternative (positive = clockwise, matching a compass bearing) reads
more naturally to a pilot, but it would put the corpus in disagreement with the
frame `pos` is expressed in, and Session 04's simulator consumes both from the
same command object. One convention across the whole system is worth more than a
locally nicer reading, and the ambiguity is confined to the surface layer where
`data/surface_forms.py` can express the sign either as a word ("minus ninety") or
as a hand ("ninety left") for the same label.

**Cost.** A model trained on this will read "right ninety" as `-90.0`. If a
downstream consumer assumes compass bearings, every rotation is mirrored. The
convention is therefore restated in `data/surface_forms.py::_rotate_cores` at
the point of use, not only here.

## Decision 2 --- "ten metres wide" is a *diameter*, so radius 5

`"form a circle ten metres wide"` -> `{"intent":"formation","shape":"circle","radius":5.0}`

Diameter phrasing appears in roughly 18% of circle rows, and only where the
halved value lands on the 0.1 grid.

**Why.** This is the one place where the operator's number and the label's number
legitimately differ, and it is common in real speech --- "wide", "across", "in
diameter" all denote the span, not the radius. A corpus that only ever says
"radius five" teaches the model that the number in the sentence is the number in
the label, and it will then mis-size every diameter-phrased command it meets by a
factor of two. Getting the halving *wrong* costs a factor of two; not learning it
at all costs the same factor on a phrasing operators actually use.

**Cost.** It is a harder mapping and will show up as circle-radius errors in
Exp-1's per-slot breakdown. Kept at low frequency so it does not dominate the
`radius` signal, and the frequency is a named constant so the mix is auditable.

## Decision 3 --- Negated commands resolve to `hover`, and `abort` is exempt

`02_dataset_plan.md` §3.3 requires `"don't land yet"` -> `hover`, not `land`:
"a model that gets this wrong lands a swarm on a 'don't land' command". We apply
that generally --- negation of any command resolves to `{"intent":"hover"}` (family
F118) --- **except for `abort`**.

No utterance containing an abort word maps to anything other than
`{"intent":"abort"}`. There is no `"don't abort"` row and no
`"we aborted the last run"` -> `unknown` row, and `data/hard_negatives.py` fails
at import if one is ever added.

**Why the asymmetry.** The two error directions are not symmetric. A spurious
abort stops a swarm that did not need stopping --- recoverable, embarrassing. A
missed abort is precisely the failure the reflex path exists to prevent. Teaching
the model that "abort" is sometimes not an abort buys a little precision on a
rare utterance and pays for it in the one case that matters.

Layer 3 makes the general rule safe: a `hover` that is illegal in the current
state resolves to a grounded no-op rather than a Table 9 violation
(`swarm/fsm.py`, ADR-0002), so `"don't land"` in `LANDED` does not spin the
rotors back up.

**Cost.** `"we aborted the last run"` --- past-tense narration --- will be
classified as an abort. That is an accepted false positive.

## Decision 4 --- Unresolvable ellipsis is `unknown`, not a partial command

`"tighter"`, `"higher"`, `"faster"` carry no value, and §2.4 requires
`set_param` to have at least one of `speed` / `spacing` / `alt`. There is no
representable label for them, so they are `{"intent":"unknown"}` (family F117).
Resolvable ellipsis --- `"tighten the spacing to two metres"` --- is a normal
`set_param`.

**Why.** The alternatives are worse. Inventing a step size ("tighter" = spacing
-0.5 m) would put a number in the label that the operator never said, which is
the one thing label-first generation exists to prevent. Silently dropping the row
would leave the corpus with no example of a comparative at all, and the model
would guess.

**Cost.** The operator gets no action from a phrase they consider meaningful. That
is the correct outcome for v1.0: the runtime cannot ask a follow-up question, so
declining is the only honest response. If a later version adds relative
parameter deltas to the schema, these rows are re-labelled, not re-authored.

## Consequences

- `data/surface_forms.py` is the single implementation of decisions 1 and 2.
  `data/hard_negatives.py` enforces 3 at import time and authors the F117 rows
  that realise 4 --- those rows carry authored text, so `_unknown_cores()` in
  `surface_forms.py` raises rather than composing a surface form for them.
- All four are restated in the dataset card (Session 03 Task 4), because a model
  consumer cannot read them off the corpus.
- Decisions 1 and 2 are the two places where a *correct* label may look wrong to
  a reviewer spot-checking rows. They are commented at the point of use for that
  reason.
