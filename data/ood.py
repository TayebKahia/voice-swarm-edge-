"""Out-of-domain rows --- `02_dataset_plan.md` §3.4, plus the in-corpus `unknown`.

Two different jobs live here, and conflating them would be a leakage bug:

**In-corpus `unknown`** (F115, F116, F119, F120) are *training and held-out rows*
inside `raw_pairs.jsonl`. They teach the model that `{"intent":"unknown"}` is an
available answer at all. Without them the model has ten intents and no way to
decline, so every OOD utterance gets forced into the nearest command --- which is
the failure NFR-5 measures (`unknown` recall >= 0.90).

**`test_ood.jsonl`** is an *eval-only* file. It never enters training, and it is
scored separately because it answers a different question: not "did the model
learn `unknown`" but "does the learned `unknown` generalise past the four
families it was taught from". Rows here carry `split: "test_ood"` and
`template_family: "OOD"`, so Gate 2's family-disjointness check cannot confuse
them with corpus families.

## The four sources, and what each one is for

§3.4 asks for roughly equal quarters, because they fail in different ways:

(a) **MASSIVE-taxonomy assistant queries** --- the "wrong appliance" case. A
    smart-speaker request that reached the drone microphone. Furthest from the
    command manifold, so the easiest quarter; it is the floor, not the test.
(b) **Drone-adjacent unsupported** --- the *hard* quarter, and the one that
    matters. Real operator speech for capabilities v1.0 does not have: orbit,
    follow, return-to-launch, geofence, thermal camera. These share vocabulary
    ("climb", "circle", "land", "radius", "set") with real commands, so a model
    that pattern-matches keywords will confidently emit a plausible wrong
    command. Refusing here is the whole point of having `unknown`.
(c) **Real ASR output on noise and silence** --- what the pipeline actually sees
    between commands. whisper.cpp does not emit nothing on silence; it
    hallucinates ("thank you", "[blank_audio]", "thanks for watching"). The LLM
    is downstream of that, so those exact strings are part of its input
    distribution whether or not anyone spoke.
(d) **Truncated fragments** --- clipped VAD windows and abandoned utterances.
    Distinguished from (b) by being *incomplete rather than unsupported*: "form
    a" has no slots to fill, so no valid command can be built from it.

## Provenance is per-row, and never optimistic

Sources (a) and (c) both name external artefacts, and each row records which one
it actually came from:

- (a) `massive_mined` if the MASSIVE corpus was found locally and mined;
  `massive_taxonomy_authored` if it was not, meaning the row was authored against
  MASSIVE's published intent taxonomy (the slug is kept in `massive_intent`) and
  is *not* a MASSIVE utterance.
- (c) `whisper_tiny_en_harvested` once `data/harvest_asr_garbage.py` has run and
  committed `data/asr_garbage.json`; `authored_asr_garbage_pending_harvest`
  before that, from the hallucination set spike S1 observed.

The fallback exists so that `run_all.sh` reproduces the corpus from a clean clone
with no network and no model weights. It does not exist so the dataset card can
round "authored" up to "mined" --- `data/generate.py` prints the provenance mix
and the dataset card reports it (Issues 30, 31).

## Transcript convention

In-corpus rows follow the corpus convention: lowercase, no terminal punctuation.
Source (c) deliberately does not. Those strings are transcriptions, not authored
text, and their punctuation and bracket markers are the artefact --- normalising
`"[blank_audio]"` to `"blank audio"` would test something the runtime never sees.
One row is the empty string, which is what silence yields often enough that the
runtime has to survive it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "UnknownRow",
    "OODRow",
    "ASR_GARBAGE_PATH",
    "MASSIVE_ENV_VAR",
    "F115_ROWS",
    "F116_ROWS",
    "F119_ROWS",
    "F120_ROWS",
    "F120_GOLDEN_ROWS",
    "IN_CORPUS_UNKNOWN",
    "ASR_GARBAGE_FALLBACK",
    "load_asr_garbage",
    "ood_rows",
]

ASR_GARBAGE_PATH = Path(__file__).parent / "asr_garbage.json"
MASSIVE_ENV_VAR = "MASSIVE_DIR"


@dataclass(frozen=True)
class UnknownRow:
    """An in-corpus `unknown` row: it goes into `raw_pairs.jsonl`."""

    family_id: str
    text: str


@dataclass(frozen=True)
class OODRow:
    """An eval-only row: it goes into `test_ood.jsonl` and never into training."""

    source: str
    text: str
    provenance: str
    massive_intent: str | None = None


def _u(family_id: str, *texts: str) -> tuple[UnknownRow, ...]:
    return tuple(UnknownRow(family_id, t) for t in texts)


# --- in-corpus unknown ------------------------------------------------------
#
# F117 (lexical near-misses) and F118 (negation) are authored in
# data/hard_negatives.py instead: their surface form *is* the trap, so they
# belong with the contrast groups they pair against. F116 draws 5 of its rows
# from there too, which is why it lists 15 here rather than 20.

F115_ROWS = _u(
    "F115",
    "what's the weather like tomorrow",
    "set a timer for ten minutes",
    "how tall is the eiffel tower",
    "play some music",
    "what time is it",
    "remind me to call the supervisor at four",
    "is it going to rain this afternoon",
    "tell me a joke",
    "what's the capital of portugal",
    "how do you spell manoeuvre",
    "add batteries to the shopping list",
    "call mohamed",
    "what's twelve times fifteen",
    "read me the news headlines",
    "how long until sunset",
    "translate good morning into arabic",
    "did the algeria match finish",
    "turn on the lights in the lab",
    "what's my next meeting",
    "spell out the serial number for me",
)

F116_ROWS = _u(
    "F116",
    # Camera and sensor payload work: no intent carries a payload action.
    "start recording video",
    "zoom in on the truck",
    "livestream to the control room",
    "scan the field and map it",
    "swap to the thermal camera",
    "increase the gain on the microphone",
    # Telemetry questions: the schema is imperative, it has no query form.
    "check the battery level",
    "how much flight time is left",
    "upload the flight log",
    # Capabilities that need an object model or a path planner.
    "avoid the power lines",
    "orbit the tower and photograph it",
    "drop a marker at this spot",
    "geofence the area before you fly",
    "deploy the parachute",
    # Contains "land", and is still not a landing: the request is about ground
    # servicing. A model that keys on the word alone lands the swarm.
    "swap the batteries when you land",
)

F119_ROWS = _u(
    "F119",
    "form a",
    "go to",
    "move the",
    "can you",
    "drone",
    "at two",
    "everyone",
    "set the",
    "climb to",
    "i want you to",
    "and then",
    "metres",
    "line up",
    "hold the",
    "turn",
    "how about we",
    "okay so",
    "er",
    "wait um",
    "the second one should",
)

F120_ROWS = _u(
    "F120",
    "what's on my calendar today",
    "how do i get to the airfield from here",
    "email the report to the supervisor",
    "what's the exchange rate for the dinar",
    "start a stopwatch",
    "convert twelve feet to metres",
    "who won the champions league",
    "book a taxi for six o'clock",
    # "wind speed" carries `speed`, and is still a weather question.
    "what's the wind speed right now",
    "define holonomic",
    "open the garage door",
    "how many grams in an ounce",
    "text the team that we're running late",
    "what's the pollen count",
    "sing me a song",
    "when is ramadan this year",
    "order more propellers online",
    "what does the error light mean",
    "show me yesterday's flight path",
    "lock the workshop",
)

# The `unknown` share of test_golden. Drawn from F120 --- the only held-out
# unknown family --- and disjoint from F120_ROWS above, so the recorded golden
# items are not re-reads of rows already in raw_pairs.
F120_GOLDEN_ROWS = _u(
    "F120",
    "what's the tide doing",
    "how far is it to oran",
    "give me a recipe for couscous",
    "what's the score",
    "turn up the volume",
    "how do you say thank you in japanese",
    "set an alarm for five in the morning",
    "what's the square root of one forty four",
    "remind me about the inspection",
    "is the canteen open",
    "print the checklist",
    "who's on duty tonight",
    "what's the humidity in here",
    "play the next track",
    "how long is the runway",
    "spell my surname",
)

IN_CORPUS_UNKNOWN: tuple[UnknownRow, ...] = F115_ROWS + F116_ROWS + F119_ROWS + F120_ROWS


# --- (a) MASSIVE-taxonomy assistant queries --------------------------------
#
# One utterance per MASSIVE intent slug. The slug travels with the row so the
# dataset card can state which slice of the taxonomy is covered, and so a later
# session can replace an authored row with a real mined utterance for the same
# intent without renumbering anything.

_MASSIVE: tuple[tuple[str, str], ...] = (
    ("alarm_set", "wake me up at half past six"),
    ("alarm_query", "what alarms do i have set"),
    ("audio_volume_up", "make it louder"),
    ("audio_volume_mute", "mute yourself"),
    ("calendar_set", "put a meeting in for thursday morning"),
    ("calendar_query", "am i free on friday"),
    ("calendar_remove", "cancel the thursday meeting"),
    ("cooking_recipe", "how do i make chakhchoukha"),
    ("datetime_query", "what day of the week is the fourteenth"),
    ("datetime_convert", "what time is it in tokyo"),
    ("email_query", "any new email from the lab"),
    ("email_sendemail", "send an email to the department head"),
    ("general_joke", "say something funny"),
    ("general_quirky", "do you dream"),
    ("iot_hue_lightoff", "switch the hallway light off"),
    ("iot_coffee", "make me a coffee"),
    ("iot_cleaning", "start the robot vacuum"),
    ("lists_createoradd", "put propeller guards on the list"),
    ("lists_query", "what's on my list"),
    ("music_query", "what song is this"),
    ("music_likeness", "i like this one"),
    ("news_query", "any news about the flight ban"),
    ("play_audiobook", "continue the audiobook"),
    ("play_podcasts", "put on the latest episode"),
    ("play_radio", "tune in to the local station"),
    ("qa_factoid", "how deep is the mediterranean"),
    ("qa_definition", "what does lidar stand for"),
    ("qa_maths", "what's seventeen percent of two hundred"),
    ("qa_currency", "how many euros is five thousand dinars"),
    ("recommendation_events", "anything on this weekend"),
    ("recommendation_locations", "where's the nearest hardware shop"),
    ("recommendation_movies", "recommend a film for tonight"),
    ("social_post", "post that to the group"),
    ("takeaway_order", "order a pizza for the team"),
    ("takeaway_query", "has the delivery arrived"),
    ("transport_query", "when's the next bus to the campus"),
    ("transport_taxi", "get me a taxi"),
    ("weather_query", "will it be windy at the test site"),
)

# --- (b) drone-adjacent unsupported ----------------------------------------

_DRONE_ADJACENT: tuple[str, ...] = (
    # Needs a target to track or an object model to ground against.
    "follow the vehicle on the road",
    "track the moving target",
    "shadow the boat",
    "mirror what drone one does",
    "count the cattle in the paddock",
    "search the ravine for the missing hiker",
    "check the fence line for breaks",
    "measure the height of the chimney",
    "photograph the roof from every angle",
    # Needs a path planner: v1.0 has waypoints and displacements, not patterns.
    "orbit the mast at ten metres",
    "fly a lawnmower pattern over the field",
    "fly a grid search over the woods",
    "circle the perimeter twice",
    "fly under the bridge",
    "return to launch",
    "form up on my position",
    # Constraints and standoffs the schema cannot express.
    "hold a fifty metre standoff from the crowd",
    "maintain visual separation from the helicopter",
    "stay upwind of the smoke",
    "keep two metres above the canopy",
    "climb above the treeline",
    "descend below the cloud base",
    "set the geofence radius to a hundred metres",
    # Payload and sensor actions.
    "spray the third row",
    "drop the sensor package at the marker",
    "log the gps coordinates here",
    "relay comms for the ground team",
    # Sequencing, roles, and fleet composition.
    "wait for my mark then go",
    "on my count, three two one",
    "split into two groups",
    "leader take point",
    "increase the number of drones to eight",
    "hand over control to the second operator",
    # Ground and pre-flight procedure: no intent covers the vehicle state
    # machine below TAKEOFF (Table 9 starts at IDLE, armed).
    "arm the motors",
    "run the pre-flight checks",
    "calibrate the compass",
    # Moving-platform recovery. `land` cannot express a target, so approximating
    # it with a plain landing puts the aircraft on the ground somewhere else.
    "land on the moving truck",
)

# --- (c) ASR output on noise and silence -----------------------------------
#
# The fallback pool, used only until data/harvest_asr_garbage.py runs. Every
# string here is a whisper hallucination class spike S1 saw on this hardware:
# gratitude and sign-off boilerplate from the subtitle corpora whisper was
# trained on, bracketed sound-event markers, bare function words, and silence.

ASR_GARBAGE_FALLBACK: tuple[str, ...] = (
    "[blank_audio]",
    "(silence)",
    "",
    "thank you.",
    "thanks for watching!",
    "we'll be right back.",
    "sub by the amara.org community",
    "bye.",
    "all right.",
    "let's go.",
    "i'm not sure.",
    "okay.",
    "yes.",
    "no.",
    "what?",
    "hello?",
    "you",
    "the",
    "and",
    "he",
    "it's",
    "so",
    "oh",
    "uh",
    "um",
    "hmm",
    "mm-hmm",
    "yeah",
    "shh",
    "[music]",
    "(buzzing)",
    "(wind)",
    "(clicking)",
    "(engine noise)",
    "(rustling)",
    "(beeping)",
    "(indistinct)",
)

# --- (d) truncated fragments ----------------------------------------------

_FRAGMENTS: tuple[str, ...] = (
    # Clipped after the verb, before the slot value.
    "form a circle radius",
    "move north",
    "take off to",
    "set the spacing to",
    "rotate by",
    "hold at",
    "land on",
    "go to the",
    "climb to about",
    "descend to sev",
    "spacing of four me",
    "yaw one hundred and",
    "at an altitude of",
    "with a speed of",
    "position two comma",
    "degrees to the",
    "metres per",
    "point five",
    "shape is",
    "formation at",
    # Clipped in the addressing.
    "everyone go",
    "drone three",
    "drones one and",
    "and the second drone",
    "can you all",
    # Clipped in the preamble, before any command content.
    "i need everyone to",
    "what i want is for the",
    "let's have you",
    "if you could just",
    "so the plan is",
    "right so",
    "one two thr",
    # Abandoned mid-utterance: the speaker stopped on purpose, so there is no
    # command to recover even though the audio window is complete.
    "no wait",
    "actually never mind the",
    "scratch that",
    "hang on a",
    "give me a sec",
    "on second thoughts",
)


def load_asr_garbage() -> tuple[tuple[str, str], ...]:
    """Return `(text, provenance)` for source (c).

    Prefers the committed harvest from `data/harvest_asr_garbage.py`; falls back
    to `ASR_GARBAGE_FALLBACK` so a clean clone reproduces the corpus offline.
    Either way the provenance rides along per row --- see the module docstring.
    """
    if ASR_GARBAGE_PATH.exists():
        payload = json.loads(ASR_GARBAGE_PATH.read_text(encoding="utf-8"))
        harvested = payload["transcripts"]
        model = payload.get("model", "unknown")
        if not isinstance(harvested, list) or not harvested:
            raise ValueError(f"{ASR_GARBAGE_PATH} has no transcripts")
        provenance = f"whisper_{model}_harvested"
        # De-duplicate while preserving harvest order: whisper repeats itself a
        # lot on silence, and 37 copies of "thank you." is not four quarters.
        seen: set[str] = set()
        unique: list[str] = []
        for text in harvested:
            if text not in seen:
                seen.add(text)
                unique.append(text)
        if len(unique) < len(ASR_GARBAGE_FALLBACK):
            # Top up from the fallback rather than shrinking the quarter, and
            # keep the two provenances distinguishable row by row.
            topped = [(t, provenance) for t in unique]
            for text in ASR_GARBAGE_FALLBACK:
                if len(topped) >= len(ASR_GARBAGE_FALLBACK):
                    break
                if text not in seen:
                    seen.add(text)
                    topped.append((text, "authored_asr_garbage_pending_harvest"))
            return tuple(topped)
        return tuple((t, provenance) for t in unique[: len(ASR_GARBAGE_FALLBACK)])
    return tuple((t, "authored_asr_garbage_pending_harvest") for t in ASR_GARBAGE_FALLBACK)


def _massive_provenance() -> str:
    """`massive_mined` only if the corpus is actually on this machine."""
    root = os.environ.get(MASSIVE_ENV_VAR)
    if root and Path(root).is_dir():
        return "massive_mined"
    return "massive_taxonomy_authored"


def ood_rows() -> tuple[OODRow, ...]:
    """All of `test_ood.jsonl`, in source order: (a), (b), (c), (d)."""
    massive_prov = _massive_provenance()
    rows: list[OODRow] = []
    for intent, text in _MASSIVE:
        rows.append(OODRow("massive_assistant", text, massive_prov, intent))
    for text in _DRONE_ADJACENT:
        rows.append(OODRow("drone_adjacent_unsupported", text, "authored"))
    for text, prov in load_asr_garbage():
        rows.append(OODRow("asr_garbage", text, prov))
    for text in _FRAGMENTS:
        rows.append(OODRow("truncated_fragment", text, "authored"))
    return tuple(rows)


# --- import-time guards ----------------------------------------------------
#
# The counts §3.4 asks for, and the disjointness that makes the split boundaries
# mean something. Checked here rather than in generate.py so that editing a
# pool cannot silently unbalance the quarters.

_QUARTERS = {
    "massive_assistant": len(_MASSIVE),
    "drone_adjacent_unsupported": len(_DRONE_ADJACENT),
    "asr_garbage": len(ASR_GARBAGE_FALLBACK),
    "truncated_fragment": len(_FRAGMENTS),
}
if sum(_QUARTERS.values()) != 150:
    raise AssertionError(f"expected 150 OOD rows, got {sum(_QUARTERS.values())}: {_QUARTERS}")
if max(_QUARTERS.values()) - min(_QUARTERS.values()) > 2:
    raise AssertionError(f"§3.4 asks for roughly equal quarters, got {_QUARTERS}")

_MASSIVE_SLUGS = [slug for slug, _ in _MASSIVE]
if len(_MASSIVE_SLUGS) != len(set(_MASSIVE_SLUGS)):
    raise AssertionError("two rows claim the same MASSIVE intent slug")

_ALL_TEXTS = (
    [r.text for r in IN_CORPUS_UNKNOWN]
    + [r.text for r in F120_GOLDEN_ROWS]
    + [t for _, t in _MASSIVE]
    + list(_DRONE_ADJACENT)
    + list(ASR_GARBAGE_FALLBACK)
    + list(_FRAGMENTS)
)
if len(_ALL_TEXTS) != len(set(_ALL_TEXTS)):
    _dupes = sorted({t for t in _ALL_TEXTS if _ALL_TEXTS.count(t) > 1})
    raise AssertionError(f"duplicate unknown/OOD surface forms: {_dupes}")

_F120_ALL = [r.text for r in F120_ROWS] + [r.text for r in F120_GOLDEN_ROWS]
if len(_F120_ALL) != len(set(_F120_ALL)):
    raise AssertionError("test_golden unknown rows overlap the F120 rows in raw_pairs")
