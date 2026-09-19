#!/usr/bin/env python3
"""Pre-review checks for Master Ch2 (Related Work). See tools/review/lib.py.

Ch2 is citation-heavy and number-light, so most of what matters here is MANUAL: the citation
sheet in the report is the citation agent's worklist. The script checks what can be checked
without reading the papers: the four-themes-plus-Positioning shape, that Positioning cites
nothing the theme sections did not introduce, and the Table 3 boundary with the Ingénieur.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import MASTER, RESULTS, Chapter, Review, md_table, outline_check  # noqa: E402

r = Review("master_ch2", "master", MASTER[2], [*MASTER[:2], *MASTER[3:]])  # State of the art, Chapter 3 since 25 Sep
r.common()
text = r.ch.text

# -- Shape: four themes with a comparison table each, then Research gaps = Synthesis / G1-G3 -----
# (prd.md §3.1 since 25 Sep; the supervisor's note is that studies are compared to each other in
# the tables and to this thesis only in the gaps.)
outline_check(r, 2, {"edge LLM inference and SBC benchmarking": r"edge llm|single-board",
                     "quantisation": r"^quantisation$", "constrained decoding": r"constrained decoding",
                     "spoken-language understanding for robotics": r"spoken-language"})
titles = [t for lvl, t, _ in r.ch.sections() if lvl == "section"]
r.expect("outline", titles[-1:] == ["Research gaps"], f"a single closing Research gaps section (last section: {titles[-1:]})")
pos = text[text.find("\\section{Research gaps}"):]
r.expect("outline", "\\paragraph{Synthesis.}" in pos, "Research gaps opens with its `Synthesis.` paragraph")
for g in ("G1", "G2", "G3"):
    r.expect("outline", f"\\paragraph{{Gap {g}," in pos, f"Research gaps has its `Gap {g}` paragraph")
themes_text = text[: text.find("\\section{Research gaps}")]
for sec in ("soa-edge", "soa-quantisation", "soa-constrained-decoding", "soa-slu"):
    chunk = themes_text[themes_text.find(f"\\label{{sec:{sec}}}"):]
    chunk = chunk[: chunk.find("\\section{", 1) if "\\section{" in chunk[1:] else None]
    r.expect("table", "\\begin{table}" in chunk and "\\paragraph{Critical comparison.}" in chunk,
             f"section `{sec}` has a comparison table and a Critical comparison paragraph")
    r.expect("table", "This work &" in chunk, f"section `{sec}`'s table ends with a `This work` row")


def cites(chunk: str) -> set[str]:
    return {k.strip() for m in re.findall(r"\\cite\{([^}]*)\}", chunk) for k in m.split(",")}


themes, positioning = cites(text[: text.find("\\section{Research gaps}")]), cites(pos)
new = positioning - themes
r.expect("positioning", not new, "Research gaps introduces no source the theme sections did not review"
         if not new else f"Research gaps cites {sorted(new)} that no theme section reviewed -- a synthesis "
         "should summarise, not introduce")
for g, c in (("G1", "C1"), ("G2", "C2"), ("G3", "C3")):
    para = pos[pos.find(f"\\paragraph{{Gap {g},"):]
    para = para[: para.find("\\paragraph{", 1) if "\\paragraph{" in para[1:] else None]
    r.expect("positioning", f"Contribution {c}" in para, f"Gap {g} is closed by Contribution {c} in its own paragraph")

# -- Stack honesty and the Table 3 boundary -----------------------------------------------------
r.expect("stack", not re.search(r"\bOutlines\b", r.ch.prose()), "no tool this project never used (e.g. Outlines) named")
voice_uav = {"lim2025", "typefly2024", "simoes2024", "henry2026", "swarmchat2025", "iannoli2026", "silva2026",
             "sikorski2025", "torkamani2025", "llm2swarm2024", "chatwithuav2025", "commandswarm2026", "skysim2026"}
hit = cites(text) & voice_uav
r.expect("table3", not hit, "no voice-UAV literature cited (Table 3 gives it to the Ingénieur Ch2)"
         if not hit else f"voice-UAV keys cited here: {sorted(hit)} -- Table 3 gives these to the Ingénieur")
r.expect("table3", "M\\'emoire d'Ing\\'enieur" in text, "the hand-off to the Ingénieur is named correctly")

# -- The model list against the models actually fine-tuned (results/table33) --------------------
models = [row["Model"].strip("`") for row in md_table(RESULTS / "table33_iso_parameter.md", "Model")]
r.text_claim("coherence", "four fine-tuned models", len(models) == 4,
             f"'four fine-tuned models' = {len(models)} fine-tuned models in results/table33_iso_parameter.md")
for key in ("qwen25", "smollm2", "llama32", "danube3"):
    r.expect("cite", f"\\cite{{{key}}}" in text, f"model {key} cited where first named")
r.text_claim("coherence", "Three of those models are carried through to quantised artefacts", False,
             "Ch2 states three quantised + one fp16 control; Ch1 says 'three deployment candidates' plus a control"
             " -- the argument agent checks the two read as one story", warn=True)

# -- Numbers that belong to a cited paper, not to results/: the citation agent must verify ------
paper_numbers = [("twenty-five quantised language", "sbc2025"), ("three \\glspl{sbc}", "sbc2025"),
                 ("two inference runtimes", "sbc2025"), ("roughly\n1.5~billion parameters", "sbc2025"),
                 ("up to four times", "sbc2025"), ("135~M to 7~B", "sbc2025"),
                 ("8, 70 and 405~B", "kurtic2025"), ("one percent of weight channels", "awq"),
                 ("under one\npercent", "spqr"), ("eight billion parameters and above", "kurtic2025,kurt2026"),
                 ("has 1.5~billion parameters", "kurtic2025"), ("one million\nutterances in 51 languages", "massive"),
                 ("60 intents and 55 slot types", "massive"), ("258 to 580~million", "massive"),
                 ("85.1--86.1", "massive"), ("73.6--76.8", "massive"), ("63.7--66.6", "massive"),
                 ("Seven intents, 2{,}242--2{,}300", "snips2018"), ("Slot F1 93.0", "snips2018"),
                 ("1.4~GHz, 1~GB", "snips2018"), ("in 60~ms", "snips2018"),
                 ("18 scenarios and 46 actions", "slurp2020"), ("72{,}277 recordings of 17{,}181", "slurp2020"),
                 ("90.2, 87.0 and 84.8", "slurp2020"), ("SLU-F1 70.8", "slurp2020")]
rows = ["| line | claim | must be found in |", "|---|---|---|"]
for anchor, key in paper_numbers:
    where = r.ch.find(anchor)
    r.expect("paper-number", bool(where), f"anchor `{anchor}` present", where[0] if where else None)
    if where:
        rows.append(f"| {where[0]} | {anchor} | {key} (primary source, not the candidate notes) |")
# The Q8_0 / Q4_K_M construction moved to the Background chapter on 25 Sep (prd.md §3.1); its
# llama.cpp numbers are checked there, and stay on the citation agent's worklist.
bg = Chapter.load("master", MASTER[1])
for anchor, key in [("blocks of 32", "llamacpp"), ("super-blocks of 256", "llamacpp"),
                    ("8.5~bits per weight", "llamacpp"), ("4.5~bits per weight", "llamacpp")]:
    where = bg.find(anchor)
    r.expect("paper-number", bool(where), f"anchor `{anchor}` present in the Background chapter (moved 25 Sep)")
    if where:
        rows.append(f"| Background l.{where[0]} | {anchor} | {key} (primary source, not the candidate notes) |")
r.manual.append("### Numbers quoted from papers (citation agent: find each in the paper)\n\n" + "\n".join(rows))
r.manual.append("### For the argument agent\n\n- Critical comparisons: each must read its table column by column "
                "and compare the studies to each other; the chapter promises (intro) that they are compared to this "
                "thesis only in Research gaps -- judge whether the closing sentences of each comparison keep that promise.\n"
                "- Silence claims ('none of these studies', 'no work in the table', 'not reported anywhere in the table', "
                "'no study reviewed here combines all four'): each must be scoped to the studies reviewed, never to the "
                "literature.\n- 'This work' rows and Gap G1-G3: promise nothing Chapters 4-6 do not deliver; the reference "
                "is Ch1's C3 wording (three of four models, two levels, accuracy on the workstation, timing on the Pi at "
                "Q4_K_M).\n- .scratch/thesis-bibliography/master-candidates.md 'Notes for the author' flags a tension with "
                "C3's framing: read it.")
sys.exit(r.finish())
