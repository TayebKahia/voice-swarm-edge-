# Annotation cheat sheet — the 50 golden items

**The job.** You are shown a transcript. You write the JSON command it should
produce. Read the transcript, read this sheet, decide. You are labelling *against
the schema*, so having the schema in front of you is correct — that is what this
sheet is.

You are **not** trying to guess what the generator produced. A disagreement
between your two passes is a result, not a mistake.

---

## The ten intents and their slots

| intent | required | optional |
|---|---|---|
| `formation` | `shape` — **plus** `radius` if circle; `spacing` if line / grid / column | `ids` |
| `move` | **exactly one of** `pos` **or** (`dir` **and** `dist`) | `speed`, `ids` |
| `altitude` | `z` | `ids` |
| `rotate` | `yaw` | `ids` |
| `set_param` | at least one of `speed`, `spacing`, `alt` | — |
| `takeoff` | — | `z`, `ids` |
| `land` | — | `ids` |
| `hover` | — | `ids` |
| `abort` | — | **nothing** |
| `unknown` | — | **nothing** |

`shape` ∈ `circle` `line` `wedge` `grid` `column` `flock`

`dir` ∈ `north` `south` `east` `west` `up` `down` `forward` `back` `left` `right`

`pos` is `[x, y, z]`.

---

## Two rules that decide most items

**Omit anything that is absent.** Write `{"intent":"hover"}`, never
`{"intent":"hover","ids":null}`.

**"All drones" means omit `ids` entirely.** "everyone", "all of you", "all
drones", "the swarm" → no `ids` key at all.

---

## What the tool fixes for you — do not fuss over these

| you type | stored as |
|---|---|
| `"z":4` | `"z":4.0` — int or float, either is fine |
| `"ids":[3,1,1]` | `"ids":[1,3]` — deduplicated and sorted for you |
| `"ids":[]` | `ids` dropped — empty means all drones |
| `"yaw":-200` | `"yaw":160.0` — wrapped into [−180, 180] |
| `{"intent":"abort","ids":[0]}` | `{"intent":"abort"}` — abort is always everyone |

**One where your input really is altered:** values outside the physical envelope
are **clamped**, not rejected. `"z":30` is stored as `15.0`. Write what the
speaker said and let it clamp — that is the deployed behaviour.

Envelope: `radius` 1–10 · `spacing` 1–5 · `z` 0.5–15 · `alt` 0.5–15 ·
`speed` 0.2–2.0 · `dist` 0–50 · `|pos|` ≤ 50 · `yaw` −180…180

---

## What gets rejected (you will be re-prompted)

- `formation` + `circle` with no `radius`
- `move` with `dir` but no `dist`, or with **both** `pos` and `dir`/`dist`
- `set_param` with no slot at all
- `altitude` with no `z`, `rotate` with no `yaw`

---

## Two things the schema does NOT settle

Decide in the moment. **Both times. Do not write your choice down.**

1. **The sign of `yaw`.** The range is fixed at [−180, 180]; whether "left" or
   "clockwise" is positive is never stated anywhere.
2. **Spoken drone number → index.** `ids ⊆ {0…N−1}`, so zero-based — but whether
   "drone 2" is index 1 or index 2 is nowhere written.

If your two passes split on either, that is the finding this exercise exists to
produce. Keeping a crib sheet would turn "is the schema clear?" into "can I follow
my own notes?", which measures nothing.

---

## Worked examples

None of these is one of your 50.

```
unit 1 heading 60.2 left
  {"intent":"rotate","yaw":60.2,"ids":[0]}

change spacing to 3.0 and the default height to 0.6
  {"intent":"set_param","spacing":3.0,"alt":0.6}

spread out into a row spaced around two point seven, drones one and five
  {"intent":"formation","shape":"line","spacing":2.7,"ids":[0,4]}

proceed to the point minus thirty-three point four, five point two, eight
no more than two metres per second, everyone
  {"intent":"move","pos":[-33.4,5.2,8.0],"speed":2.0}

hold at call it two point four for me
  {"intent":"altitude","z":2.4}

drones one to two stop and stay put
  {"intent":"hover","ids":[0,1]}

recover, um, drone 2
  {"intent":"land","ids":[1]}

number erm, 4, get airborne... okay get airborne to 8m
  {"intent":"takeoff","z":8.0,"ids":[3]}

okay abort abort, all of you
  {"intent":"abort"}

how long is the runway
  {"intent":"unknown"}
```

---

## Traps

- **"hold at 2.4" is `altitude`. "stop and stay put" is `hover`.** Both sound
  like holding; one names a height.
- **Fillers carry no meaning.** "um", "erm", "okay", "call it", "maybe", "for me",
  "please" — ignore them all.
- **Self-corrections: take the second version.** "go east— eastbound about
  twenty-nine" is east. "proceed back — make that eastbound forty-six" is east.
- **`unknown` is for anything outside the ten intents** — questions, chatter,
  requests the swarm cannot act on. It is a real answer, not a giving-up.
- **A command with no addressee is all drones**, so no `ids`.

---

## Keys

`?` reprint the intent list · `s` skip · `q` save and quit (re-running resumes)

Invalid JSON or a schema violation is rejected with the reason and re-prompted —
you cannot record a malformed label.
