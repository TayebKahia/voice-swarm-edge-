"""Surface realisation --- the *text* half of label-first generation.

Session 02A inverts the usual NLU recipe: the JSON label is constructed first
(`data/generate.py`), and only then is text produced for it. So this module never
decides what a command *means*; it decides how an operator would *say* something
whose meaning is already fixed. Nothing here can produce a wrong label.

**Where the paraphrases come from.** `02_dataset_plan.md:65` specifies asking a
frontier model for "K=8 distinct ways a human operator would say this". The
frontier model in the loop is the agent authoring this file: the lexicon and the
frame banks below *are* that step's output, written out once and committed,
rather than fetched from an API at generation time. Three reasons that is the
right shape and not a shortcut:

1. **`run_all.sh` must reproduce every artefact from a clean clone.** A live API
   call needs a key and a network and returns different text each run, so the
   dataset would not be reproducible and neither would any number measured on it.
2. **`02_dataset_plan.md` §3.2 forbids letting the model choose diversity** ---
   "or you get 2,400 rows of the same three sentence shapes". The seven axes have
   to be swept by construction. That means enumerating them in code, which means
   the frame bank has to live in code.
3. The committed lexicon is auditable. A reviewer can read every phrasing the
   corpus can contain; they cannot read an API transcript that no longer exists.

**The seven diversity axes** (`02_dataset_plan.md` §3.2, not superseded) are
swept explicitly and recorded per row, so coverage is a measured property of the
corpus rather than a claim about it: register · number surface form · synonym
set · drone addressing · ellipsis fragments · disfluency and self-correction ·
politeness prefixes.

**Units, stated once, never violated** (roadmap 02A task 3): metres, metres per
second, degrees. `ids` are 0-indexed in the label but *spoken* 1-indexed ---
"drone one" is `[0]`. That mapping lives in `spoken_ids()` and nowhere else.

**Transcript style.** Lowercase, no terminal punctuation; internal commas and em
dashes only where they carry prosody. This is the reference-text convention for
the whole project: `eval/norm.py` lowercases and strips punctuation before WER
anyway, and EM is measured on this same text, so nothing downstream depends on
casing. The round-trip variants added in Session 02B arrive in Whisper's own
capitalised, punctuated style, which is what gives the model both distributions.

**Four surface conventions are recorded in `docs/adr/0003`,** because they are
semantic decisions the PRD does not make: the yaw sign convention (and therefore
what "turn left" means), the diameter-vs-radius reading of "ten metres wide",
negation resolving to `hover`, and unresolvable ellipsis resolving to `unknown`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

__all__ = [
    "REGISTERS",
    "NUMBER_FORMS",
    "ADDRESSING_MODES",
    "ELLIPSIS_INTENTS",
    "Axes",
    "num_to_words",
    "render_number",
    "render_addressing",
    "spoken_ids",
    "synonym_pool",
    "realise",
    "SHAPE_SYNONYMS",
    "DIRECTION_SYNONYMS",
]

# --- axis 1: register ------------------------------------------------------
REGISTERS: tuple[str, ...] = ("terse_radio", "conversational", "imperative", "hesitant")

# --- axis 2: number surface form ------------------------------------------
NUMBER_FORMS: tuple[str, ...] = (
    "digit",       # 5      / 5.5
    "word",        # five   / five point five
    "decimal",     # 5.0    / 5.5
    "digit_unit",  # 5m     / 5.5 m
    "word_unit",   # five metres
    "approx",      # about five
)

# --- axis 4: drone addressing ---------------------------------------------
ADDRESSING_MODES: tuple[str, ...] = (
    "implicit_all",  # no addressing at all      -> ids omitted
    "explicit_all",  # "everyone", "all drones"  -> ids omitted
    "single",        # "drone two"               -> ids [1]
    "subset",        # "drones one and three"    -> ids [0, 2]
    "range",         # "drones one through three"-> ids [0, 1, 2]
)


@dataclass(frozen=True)
class Axes:
    """The diversity-axis assignment for one row, recorded in the corpus.

    Written to every row so that axis coverage can be *counted* rather than
    asserted, and so a per-axis error breakdown is available in Exp-1 without
    re-deriving the axis from the text.
    """

    register: str
    number_form: str
    addressing: str
    synonym: str            # which synonym set member the head word came from
    disfluency: bool        # axis 6
    politeness: bool        # axis 7
    ellipsis: bool          # axis 5

    def as_dict(self) -> dict[str, object]:
        return {
            "register": self.register,
            "number_form": self.number_form,
            "addressing": self.addressing,
            "synonym": self.synonym,
            "disfluency": self.disfluency,
            "politeness": self.politeness,
            "ellipsis": self.ellipsis,
        }


# --- numbers ---------------------------------------------------------------

_ONES = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
)
_TENS = (
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety",
)


def _int_to_words(n: int) -> str:
    """English words for 0 <= n <= 999."""
    if not 0 <= n <= 999:
        raise ValueError(f"only 0..999 are spoken in this vocabulary, got {n}")
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] if ones == 0 else f"{_TENS[tens]}-{_ONES[ones]}"
    hundreds, rest = divmod(n, 100)
    head = f"{_ONES[hundreds]} hundred"
    return head if rest == 0 else f"{head} and {_int_to_words(rest)}"


def num_to_words(value: float, half: bool = False) -> str:
    """Spoken form of a one-decimal number.

    `half=True` renders a trailing .5 as "and a half" ("four and a half")
    instead of "point five" --- the way an operator actually says it. Both forms
    appear in the corpus so the model is not tuned to one of them.
    """
    negative = value < 0
    magnitude = round(abs(value), 1)
    whole = int(magnitude)
    tenths = int(round((magnitude - whole) * 10))

    if tenths == 0:
        words = _int_to_words(whole)
    elif half and tenths == 5:
        words = "half" if whole == 0 else f"{_int_to_words(whole)} and a half"
    elif whole == 0:
        words = f"nought point {_ONES[tenths]}"
    else:
        words = f"{_int_to_words(whole)} point {_ONES[tenths]}"

    return f"minus {words}" if negative else words


def _digits(value: float, force_decimal: bool = False) -> str:
    """Digit form: `5` when the value is whole, `5.5` otherwise."""
    rounded = round(value, 1)
    if force_decimal or rounded != int(rounded):
        return f"{rounded:.1f}"
    return str(int(rounded))


_UNIT_WORDS: dict[str, tuple[str, ...]] = {
    # Both spellings on purpose: whisper.cpp's English models emit "meters",
    # a human reference is as likely to write "metres". The model should be
    # invariant to it before Session 02B ever mixes the two distributions.
    "m": ("metres", "meters", "m"),
    "mps": ("metres per second", "meters per second", "m/s"),
    "deg": ("degrees", "degrees", "deg"),
}

_APPROX = ("about", "roughly", "around", "something like", "call it")


def render_number(
    value: float,
    form: str,
    unit: str | None,
    rng: random.Random,
) -> str:
    """Render `value` in one of the six surface forms of axis 2.

    `unit` is one of `"m"`, `"mps"`, `"deg"`, or None. Whatever the surface, the
    label already holds the number, so this can never disagree with the label.
    """
    if form == "digit":
        return _digits(value)
    if form == "decimal":
        return _digits(value, force_decimal=True)
    if form == "word":
        return num_to_words(value, half=rng.random() < 0.5)
    if form == "approx":
        return f"{rng.choice(_APPROX)} {num_to_words(value, half=rng.random() < 0.4)}"
    if form == "digit_unit":
        if unit is None:
            return _digits(value)
        suffix = _UNIT_WORDS[unit][2]
        joiner = "" if unit == "m" and rng.random() < 0.5 else " "
        return f"{_digits(value)}{joiner}{suffix}"
    if form == "word_unit":
        words = num_to_words(value, half=rng.random() < 0.4)
        if unit is None:
            return words
        return f"{words} {rng.choice(_UNIT_WORDS[unit][:2])}"
    raise ValueError(f"unknown number form {form!r}")


# --- axis 4: addressing ----------------------------------------------------

_ALL_WORDS = ("everyone", "all drones", "all units", "the swarm", "everybody", "all of you")
_UNIT_NOUNS = ("drone", "unit", "bird", "number")
_UNIT_NOUNS_PLURAL = {"drone": "drones", "unit": "units", "bird": "birds", "number": "numbers"}


def spoken_ids(ids: list[int]) -> list[int]:
    """The 1-indexed identifiers an operator speaks for a 0-indexed label.

    Roadmap 02A task 3: `ids` are 0-indexed but spoken 1-indexed, so `[0]` is
    "drone one". This is the only place the offset is applied; every surface form
    that mentions a drone number goes through it.
    """
    return [i + 1 for i in ids]


def render_addressing(
    ids: list[int] | None,
    mode: str,
    form: str,
    rng: random.Random,
) -> str:
    """Surface form for the addressing axis, consistent with the label's `ids`."""
    if mode == "implicit_all":
        return ""
    if mode == "explicit_all":
        return rng.choice(_ALL_WORDS)
    if ids is None:
        raise ValueError(f"addressing mode {mode!r} needs ids in the label")

    spoken = spoken_ids(ids)
    noun = rng.choice(_UNIT_NOUNS)
    plural = _UNIT_NOUNS_PLURAL[noun]
    # Numbers inside an address are spoken as words or bare digits only; "drone
    # 2.0" is not something anyone says, so the unit-bearing forms are excluded.
    style = "digit" if form in ("digit", "decimal", "digit_unit") else "word"

    def one(value: int) -> str:
        return str(value) if style == "digit" else _int_to_words(value)

    if mode == "single":
        if len(spoken) != 1:
            raise ValueError(f"single addressing needs exactly one id, got {ids}")
        return f"{noun} {one(spoken[0])}"
    if mode == "subset":
        heads = [one(v) for v in spoken]
        if rng.random() < 0.35:
            # "drone one and drone three" --- the fully repeated form
            return " and ".join(f"{noun} {h}" for h in heads)
        joined = ", ".join(heads[:-1]) + f" and {heads[-1]}"
        return f"{plural} {joined}"
    if mode == "range":
        connector = rng.choice(("through", "to", "thru"))
        return f"{plural} {one(spoken[0])} {connector} {one(spoken[-1])}"
    raise ValueError(f"unknown addressing mode {mode!r}")


# --- axis 3: synonym sets --------------------------------------------------

SHAPE_SYNONYMS: dict[str, tuple[str, ...]] = {
    "circle": ("circle", "ring", "circular formation", "round formation"),
    "line": ("line", "row", "straight line", "line abreast"),
    "wedge": ("wedge", "vee", "v formation", "arrow formation"),
    "grid": ("grid", "square grid", "box grid", "lattice"),
    "column": ("column", "stack", "vertical stack", "column stack"),
    "flock": ("flock", "loose flock", "cluster", "flocking formation"),
}

DIRECTION_SYNONYMS: dict[str, tuple[str, ...]] = {
    "north": ("north", "northward", "to the north", "northbound"),
    "south": ("south", "southward", "to the south", "southbound"),
    "east": ("east", "eastward", "to the east", "eastbound"),
    "west": ("west", "westward", "to the west", "westbound"),
    "up": ("up", "upward", "higher", "straight up"),
    "down": ("down", "downward", "lower", "straight down"),
    "forward": ("forward", "ahead", "forwards", "straight ahead"),
    "back": ("back", "backward", "backwards", "astern"),
    "left": ("left", "to port", "off to the left", "leftward"),
    "right": ("right", "to starboard", "off to the right", "rightward"),
}

_FORM_VERBS = ("form", "get into", "make", "set up", "assume", "take up", "go into")
_MOVE_VERBS = ("move", "go", "head", "shift", "push", "proceed", "translate")
_CLIMB_VERBS = ("climb to", "go up to", "ascend to", "rise to", "come up to")
_DESCEND_VERBS = ("drop to", "descend to", "come down to", "go down to", "settle to")
_HOLD_ALT_VERBS = ("hold at", "level off at", "sit at", "maintain")
_TAKEOFF_VERBS = ("take off", "launch", "lift off", "get airborne", "spin up and launch", "get in the air")
_LAND_VERBS = ("land", "set down", "touch down", "put it down", "bring it down", "come home")
_HOVER_VERBS = ("hover", "hold position", "hold", "stay put", "freeze", "hold station", "station keep")
_ABORT_VERBS = ("abort", "emergency stop", "kill it", "all stop", "cut the motors", "abort abort", "kill the motors", "shut it down")
_ROTATE_VERBS = ("rotate", "turn", "yaw", "spin", "pivot", "come round", "swing round")
_SET_VERBS = ("set", "make", "limit", "cap", "configure", "put")

# --- axis 7: politeness / prefix noise ------------------------------------

_STANDALONE_PREFIXES = ("okay so", "alright", "right", "right then", "listen up", "okay", "so", "now then")
_REQUEST_PREFIXES = ("can you", "could you", "please", "I want you to", "I need you to", "let's")

# --- axis 6: disfluency ----------------------------------------------------

_FILLERS = ("uh", "um", "er", "erm")


def _inject_disfluency(text: str, rng: random.Random) -> str:
    """Add a filler, a partial-word repair, or a stutter to a rendered sentence."""
    words = text.split()
    if not words:
        return text
    style = rng.randrange(3)
    if style == 0:
        return f"{rng.choice(_FILLERS)}, {text}"
    if style == 1 and len(words) > 2:
        cut = rng.randrange(1, min(3, len(words)))
        head = words[cut]
        partial = head[: max(1, len(head) // 2)]
        words[cut] = f"{partial}— {head}"
        return " ".join(words)
    insert_at = 1 if len(words) > 1 else 0
    words.insert(insert_at, f"{rng.choice(_FILLERS)},")
    return " ".join(words)


def _self_correction(right: str, wrong: str, rng: random.Random) -> str:
    """"north — no, south": a spoken repair whose *final* value is the label's."""
    repair = rng.choice(("no,", "sorry,", "scratch that,", "correction,", "make that"))
    return f"{wrong} — {repair} {right}"


# --- assembly --------------------------------------------------------------


def _attach_addressing(core: str, addr: str, register: str, rng: random.Random) -> str:
    """Place the addressing phrase before or after the command core."""
    if not addr:
        return core
    if register == "terse_radio":
        return f"{addr}, {core}" if rng.random() < 0.5 else f"{core}, {addr}"
    roll = rng.random()
    if roll < 0.55:
        return f"{addr} {core}"
    if roll < 0.8:
        return f"{core}, {addr}"
    return f"{addr}, {core}"


def _apply_politeness(text: str, register: str, rng: random.Random) -> str:
    if register == "conversational" and rng.random() < 0.55:
        prefix = rng.choice(_REQUEST_PREFIXES)
        if prefix == "let's":
            return f"let's {text}"
        return f"{prefix} {text}"
    return f"{rng.choice(_STANDALONE_PREFIXES)}, {text}"


def _finish(core: str, addr: str, axes: Axes, rng: random.Random) -> str:
    text = _attach_addressing(core, addr, axes.register, rng)
    if axes.politeness:
        text = _apply_politeness(text, axes.register, rng)
    if axes.disfluency:
        text = _inject_disfluency(text, rng)
    # Lowercase last, once: several frames above are written with a capital "I"
    # because that is how the phrase reads in isolation, and the corpus
    # convention is lowercase throughout (see the module docstring).
    return " ".join(text.split()).lower()


# --- per-intent cores ------------------------------------------------------
#
# Each builder returns candidate cores for one register. The caller picks one
# with the row's rng, so diversity is the product of (register x synonym x
# number form x addressing x candidate), not the sum.

# ADR-0003 Decision 2 requires this frequency to be named rather than inlined, so
# the diameter/radius mix in the corpus is auditable without reading the sampler.
DIAMETER_PHRASING_RATE = 0.18


def _formation_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    shape = gold["shape"]
    noun = axes.synonym
    verb = rng.choice(_FORM_VERBS)
    reg = axes.register

    size = ""
    if gold.get("radius") is not None:
        radius = float(gold["radius"])
        # Diameter phrasing: "ten metres wide" is radius 5. Kept deliberately
        # and at low frequency (ADR-0003) --- it is the one place the operator's
        # words and the label's number legitimately differ, and a model that
        # cannot do it will mis-size half of the real commands it hears.
        if rng.random() < DIAMETER_PHRASING_RATE and float(radius * 2).is_integer():
            span = render_number(radius * 2, axes.number_form, "m", rng)
            size = rng.choice((f"{span} wide", f"{span} across", f"{span} in diameter"))
        else:
            value = render_number(radius, axes.number_form, "m", rng)
            size = rng.choice(
                (f"radius {value}", f"{value} radius", f"with a radius of {value}", f"at {value} radius")
            )
    elif gold.get("spacing") is not None:
        value = render_number(float(gold["spacing"]), axes.number_form, "m", rng)
        size = rng.choice(
            (
                f"{value} apart",
                f"{value} spacing",
                f"spaced {value}",
                f"with {value} between you",
                f"{value} separation",
            )
        )

    # `size` is empty for F019/F023, the bare-shape families (wedge and flock):
    # the operator names a shape and gives no size, and the label omits the slot
    # rather than inventing a value. Every branch below reads correctly without it.
    #
    # There is deliberately no transit-speed phrasing here. `Formation` has no
    # `speed` field and `c-form` has no `o-speed`, so rendering one would produce a
    # transcript no legal label can express (Issue 30). Transit speed is
    # `set_param`, and `_set_param_cores` renders it.

    if reg == "terse_radio":
        candidates = [
            f"{noun}{', ' + size if size else ''}",
            f"{verb} {noun}{', ' + size if size else ''}",
            f"{noun} formation{', ' + size if size else ''}",
        ]
    elif reg == "imperative":
        candidates = [
            f"{verb} a {noun}{' ' + size if size else ''}",
            f"{verb} up in a {noun}{', ' + size if size else ''}",
            f"{verb} the {noun}{' ' + size if size else ''}",
        ]
    elif reg == "conversational":
        candidates = [
            f"{verb} into a {noun}{' ' + size if size else ''}",
            f"{verb} yourselves into a {noun}{' ' + size if size else ''}",
            f"spread out into a {noun}{' ' + size if size else ''}",
        ]
    else:  # hesitant
        candidates = [
            f"{verb} a... a {noun}{', ' + size if size else ''} I think",
            f"{verb} a {noun} — {size} maybe" if size else f"{verb} a {noun}, maybe",
            f"can we get a {noun}{', ' + size if size else ''}, sort of",
        ]

    return candidates


def _move_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    verb = rng.choice(_MOVE_VERBS)
    reg = axes.register
    speed = ""
    if gold.get("speed") is not None:
        value = render_number(float(gold["speed"]), axes.number_form, "mps", rng)
        speed = rng.choice((f"at {value}", f"keep it to {value}", f"speed {value}", f"no more than {value}"))

    if gold.get("pos") is not None:
        x, y, z = (float(v) for v in gold["pos"])
        coords = [render_number(v, axes.number_form, None, rng) for v in (x, y, z)]
        triple = ", ".join(coords)
        alt = render_number(z, axes.number_form, "m", rng)
        if reg == "terse_radio":
            candidates = [
                f"waypoint {triple}",
                f"position {triple}",
                f"{verb} {triple}",
            ]
        elif reg == "imperative":
            candidates = [
                f"{verb} to {triple}",
                f"{verb} to x {coords[0]} y {coords[1]} z {coords[2]}",
                f"{verb} to the point {triple}",
            ]
        elif reg == "conversational":
            candidates = [
                f"{verb} over to {triple}",
                f"{verb} to {coords[0]}, {coords[1]}, and hold {alt}",
                f"head for the coordinates {triple}",
            ]
        else:
            candidates = [
                f"{verb} to, uh, {triple} I think",
                f"{verb} to {coords[0]}... {coords[1]}... {coords[2]}",
                f"go to about {triple}, roughly",
            ]
        return [f"{c} {speed}" if speed else c for c in candidates]

    direction = gold["dir"]
    dir_word = axes.synonym
    dist = render_number(float(gold["dist"]), axes.number_form, "m", rng)

    # Self-correction (axis 6) is only meaningful where a plausible wrong value
    # exists to be repaired, and the *repaired* value is always the label's.
    if axes.disfluency and rng.random() < 0.4:
        wrong = rng.choice([d for d in DIRECTION_SYNONYMS if d != direction])
        dir_word = _self_correction(dir_word, wrong, rng)

    if reg == "terse_radio":
        candidates = [
            f"{dir_word} {dist}",
            f"{verb} {dir_word} {dist}",
            f"{dist} {dir_word}",
        ]
    elif reg == "imperative":
        candidates = [
            f"{verb} {dist} {dir_word}",
            f"{verb} {dir_word} by {dist}",
            f"{verb} {dir_word} {dist}",
        ]
    elif reg == "conversational":
        candidates = [
            f"{verb} {dist} {dir_word} please",
            f"let's go {dir_word} about {dist}",
            f"{verb} on {dir_word} for {dist}",
        ]
    else:
        candidates = [
            f"{verb}, uh, {dir_word} {dist} or so",
            f"{verb} {dir_word}... {dist} I guess",
            f"maybe {verb} {dir_word} {dist}",
        ]
    return [f"{c} {speed}" if speed else c for c in candidates]


def _altitude_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    z = float(gold["z"])
    value = render_number(z, axes.number_form, "m", rng)
    reg = axes.register
    verb = axes.synonym

    if reg == "terse_radio":
        return [f"altitude {value}", f"level {value}", f"{value} altitude", f"height {value}"]
    if reg == "imperative":
        return [
            f"{verb} {value}",
            f"set altitude {value}",
            f"{verb} an altitude of {value}",
        ]
    if reg == "conversational":
        return [
            f"{verb} {value} for me",
            f"let's be at {value}",
            f"{verb} around {value} and hold there",
        ]
    return [
        f"{verb}, uh, {value} maybe",
        f"{verb} {value}... yeah {value}",
        f"can you {verb} {value}, roughly",
    ]


def _takeoff_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    verb = axes.synonym
    reg = axes.register
    height = ""
    if gold.get("z") is not None:
        value = render_number(float(gold["z"]), axes.number_form, "m", rng)
        height = rng.choice((f"to {value}", f"and climb to {value}", f"up to {value}", f"and hold {value}"))

    if reg == "terse_radio":
        base = [f"{verb}", f"{verb} now", f"cleared to {verb}"]
    elif reg == "imperative":
        base = [f"{verb}", f"{verb} immediately", f"arm and {verb}"]
    elif reg == "conversational":
        base = [f"let's {verb}", f"time to {verb}", f"{verb} whenever you're ready"]
    else:
        base = [f"uh, {verb} I suppose", f"{verb}... okay {verb}", f"maybe {verb} now"]
    return [f"{c} {height}".strip() if height else c for c in base]


def _land_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    verb = axes.synonym
    reg = axes.register
    if reg == "terse_radio":
        return [f"{verb}", f"{verb} now", "recover"]
    if reg == "imperative":
        # The pad phrasing stands alone rather than taking the synonym: several
        # members of the pool ("come home", "bring it down") already carry a
        # destination, and stacking two reads as neither.
        return [f"{verb}", f"{verb} immediately", "put it down on the pad"]
    if reg == "conversational":
        return [f"let's {verb}", f"bring everything down and {verb}", f"{verb} when you can"]
    return [f"uh, {verb} I think", f"{verb}... yeah {verb}", f"maybe {verb} now"]


def _hover_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    verb = axes.synonym
    reg = axes.register
    if reg == "terse_radio":
        return [f"{verb}", f"{verb} now", f"{verb} there"]
    if reg == "imperative":
        return [f"{verb}", f"{verb} right there", f"stop and {verb}"]
    if reg == "conversational":
        return [f"just {verb} for a moment", f"let's {verb} here", f"{verb} where you are"]
    return [f"uh, {verb} I guess", f"{verb}... just {verb}", f"maybe {verb} for now"]


def _abort_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    verb = axes.synonym
    reg = axes.register
    # Repetition is how the call is actually made on the radio, but only for the
    # one-word members --- "emergency stop emergency stop" is nobody's utterance.
    doubled = f"{verb} {verb}" if " " not in verb else f"{verb}, and I mean now"
    if reg == "terse_radio":
        return [f"{verb}", doubled, f"{verb} now"]
    if reg == "imperative":
        return [f"{verb}", f"{verb} immediately", f"{verb}, everything down"]
    if reg == "conversational":
        return [f"okay {verb}", f"we need to {verb}", f"{verb}, something's wrong"]
    return [f"uh, {verb}", f"{verb}... {verb} now", f"just {verb} I think"]


def _rotate_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    yaw = float(gold["yaw"])
    verb = axes.synonym
    reg = axes.register

    # ADR-0003: positive yaw is counter-clockwise seen from above, so a positive
    # angle is a turn to the LEFT and a negative angle a turn to the RIGHT. The
    # signed magnitude is what the label holds; the surface form may express the
    # sign either as a word ("minus ninety") or as a hand ("right ninety").
    magnitude = abs(yaw)
    signed = render_number(yaw, axes.number_form, "deg", rng)
    unsigned = render_number(magnitude, axes.number_form, "deg", rng)
    hand = "left" if yaw > 0 else "right"
    spin = "counter-clockwise" if yaw > 0 else "clockwise"

    if yaw == 0.0:
        phrases = ["to zero", "back to zero degrees", "to heading zero"]
    elif abs(magnitude - 180.0) < 1e-9:
        phrases = [f"{unsigned}", "one eighty", "right around", f"{unsigned} about face"]
    else:
        phrases = [signed, f"{unsigned} {hand}", f"{hand} {unsigned}", f"{unsigned} {spin}"]

    phrase = rng.choice(phrases)
    if reg == "terse_radio":
        return [f"{verb} {phrase}", f"yaw {phrase}", f"heading {phrase}"]
    if reg == "imperative":
        return [f"{verb} {phrase}", f"{verb} by {phrase}", f"come round {phrase}"]
    if reg == "conversational":
        return [f"{verb} {phrase} for me", f"let's {verb} {phrase}", f"can you {verb} {phrase}"]
    return [f"{verb}, uh, {phrase}", f"{verb} {phrase}... yeah", f"maybe {verb} {phrase}"]


def _set_param_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    verb = rng.choice(_SET_VERBS)
    reg = axes.register
    parts: list[str] = []
    if gold.get("speed") is not None:
        value = render_number(float(gold["speed"]), axes.number_form, "mps", rng)
        parts.append(rng.choice((f"speed to {value}", f"the speed limit to {value}", f"cruise to {value}")))
    if gold.get("spacing") is not None:
        value = render_number(float(gold["spacing"]), axes.number_form, "m", rng)
        parts.append(rng.choice((f"spacing to {value}", f"the gap to {value}", f"separation to {value}")))
    if gold.get("alt") is not None:
        value = render_number(float(gold["alt"]), axes.number_form, "m", rng)
        parts.append(
            rng.choice((f"transit altitude to {value}", f"the default height to {value}", f"cruise altitude to {value}"))
        )
    body = " and ".join(parts)
    short = body.replace("the ", "")

    if reg == "terse_radio":
        return [f"{short}", f"{verb} {short}", f"parameter {short}"]
    if reg == "imperative":
        return [f"{verb} {body}", f"{verb} the {body}" if not body.startswith("the") else f"{verb} {body}", f"change {body}"]
    if reg == "conversational":
        return [f"let's {verb} {body}", f"{verb} {body} from now on", f"I'd like to {verb} {body}"]
    return [f"{verb}, uh, {body}", f"{verb} {body}... yeah", f"maybe {verb} {body}"]


def _unknown_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    """`unknown` and `hover`-from-negation rows carry authored text.

    Their surface forms are the *point* of the row (a near-miss, a negation, a
    fragment), so they are authored in `data/hard_negatives.py` and passed through
    verbatim rather than composed from frames. Reaching this function means the
    caller forgot to.
    """
    raise ValueError(
        "unknown/hard-negative rows must supply their own surface form; "
        "see data/hard_negatives.py"
    )


_CORE_BUILDERS = {
    "formation": _formation_cores,
    "move": _move_cores,
    "altitude": _altitude_cores,
    "takeoff": _takeoff_cores,
    "land": _land_cores,
    "hover": _hover_cores,
    "abort": _abort_cores,
    "rotate": _rotate_cores,
    "set_param": _set_param_cores,
    "unknown": _unknown_cores,
}

# The synonym set each intent draws its head word from. Recorded on the row as
# axis 3 so a per-synonym error breakdown is available without re-parsing text.
_SYNONYM_POOLS: dict[str, tuple[str, ...]] = {
    "altitude": _CLIMB_VERBS + _DESCEND_VERBS + _HOLD_ALT_VERBS,
    "takeoff": _TAKEOFF_VERBS,
    "land": _LAND_VERBS,
    "hover": _HOVER_VERBS,
    "abort": _ABORT_VERBS,
    "rotate": _ROTATE_VERBS,
}


# --- axis 5: ellipsis fragments -------------------------------------------
#
# An elliptical command drops the verb and keeps the content: "circle, radius
# five", "north fifteen metres", "yaw ninety". It is the register a practised
# operator falls into after the first few commands, and it is the case where the
# model has the least to go on --- no verb means the intent has to come from the
# slot shape alone.
#
# Ellipsis only exists where there *is* content to keep. `takeoff`, `land`,
# `hover`, `abort` and `unknown` are carried entirely by their verb, so eliding
# it leaves nothing; those intents opt out and `data/generate.py` reports axis
# coverage over the applicable subset rather than pretending otherwise.
ELLIPSIS_INTENTS: frozenset[str] = frozenset(
    {"formation", "move", "altitude", "rotate", "set_param"}
)

_ALL_VERBS: tuple[str, ...] = tuple(
    sorted(
        set(
            _FORM_VERBS
            + _MOVE_VERBS
            + _CLIMB_VERBS
            + _DESCEND_VERBS
            + _HOLD_ALT_VERBS
            + _TAKEOFF_VERBS
            + _LAND_VERBS
            + _HOVER_VERBS
            + _ABORT_VERBS
            + _ROTATE_VERBS
            + _SET_VERBS
        ),
        key=len,
        reverse=True,
    )
)


def _starts_with_verb(core: str) -> bool:
    """Does this core open with a command verb, on a word boundary?"""
    return any(core == v or core.startswith(v + " ") for v in _ALL_VERBS)


def _elliptical_cores(gold: dict, axes: Axes, rng: random.Random) -> list[str]:
    """The verbless frames for this label.

    Built by asking the intent's own frame bank for its terse-radio candidates
    and keeping the ones that do not open with a verb, rather than by editing
    text after the fact. So there is exactly one place that knows how to render a
    radius or a heading, and ellipsis cannot drift away from it.

    Addressing, politeness and disfluency are still applied afterwards from the
    row's *own* register, so an elliptical row is not a duplicate of a terse one.
    """
    terse = replace(axes, register="terse_radio")
    candidates = _CORE_BUILDERS[gold["intent"]](gold, terse, rng)
    verbless = [c for c in candidates if not _starts_with_verb(c)]
    return verbless or candidates


def synonym_pool(gold: dict, rng: random.Random) -> tuple[str, ...]:
    """Candidate head words for this label, i.e. axis 3's alphabet for the row."""
    intent = gold["intent"]
    if intent == "formation":
        return SHAPE_SYNONYMS[gold["shape"]]
    if intent == "move":
        if gold.get("dir") is not None:
            return DIRECTION_SYNONYMS[gold["dir"]]
        return ("coordinates", "waypoint", "position", "point")
    if intent == "altitude":
        z = float(gold["z"])
        # "drop to two metres" only makes sense downward; the corpus must not
        # teach "climb to" for a descent it cannot know the sign of, so the
        # neutral hold-verbs cover the ambiguous middle.
        if z <= 3.0:
            return _DESCEND_VERBS + _HOLD_ALT_VERBS
        if z >= 8.0:
            return _CLIMB_VERBS + _HOLD_ALT_VERBS
        return _CLIMB_VERBS + _DESCEND_VERBS + _HOLD_ALT_VERBS
    if intent == "set_param":
        return _SET_VERBS
    return _SYNONYM_POOLS.get(intent, ("",))


def realise(gold: dict, axes: Axes, rng: random.Random) -> str:
    """Render one transcript for an already-constructed label.

    The label is an input and is never modified, which is what makes every row
    correct by construction (`02_dataset_plan.md` §3.1).
    """
    builder = _CORE_BUILDERS[gold["intent"]]
    if axes.ellipsis:
        candidates = _elliptical_cores(gold, axes, rng)
    else:
        candidates = builder(gold, axes, rng)
    core = rng.choice(candidates)
    addr = render_addressing(gold.get("ids"), axes.addressing, axes.number_form, rng)
    return _finish(core, addr, axes, rng)
