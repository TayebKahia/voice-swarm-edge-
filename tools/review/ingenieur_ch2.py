#!/usr/bin/env python3
"""Pre-review checks for Ingénieur Ch3 (State of the art). See tools/review/lib.py.

The file keeps its historical name; since 26 Sep the chapter is Chapter 3 of seven, in the
Master's form (prd.md §3.1): four themes, each a taxonomy with ONE comparison table ending in a
"This work" row and a "Critical comparison." paragraph comparing the studies to each other, then
one Research gaps section (Synthesis, Conceded prior art, Gap G1-G3, the baseline). The script
checks that shape, that Research gaps introduces no source the themes did not review, that each gap
names what closes it, and the Table 3 boundary with the Master. Whether each cell and each sentence
is what its source says is the citation agent's job; the MANUAL sheets are its worklists.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import INGENIEUR, Review, outline_check  # noqa: E402

r = Review("ingenieur_ch2", "ingenieur", INGENIEUR[2], [*INGENIEUR[:2], *INGENIEUR[3:]])  # Chapter 3 since 26 Sep
r.common()
text = r.ch.text

# -- Shape: four themes with a comparison table each, then Research gaps ------------------------
TOPICS = {"language interfaces to robots (voice-controlled UAV systems among them)": r"language interfaces",
          "fast-path and dual-path architectures": r"dual-path", "swarm control": r"^swarm control$",
          "offline speech components": r"offline speech"}
outline_check(r, 2, TOPICS)
titles = [t for lvl, t, _ in r.ch.sections() if lvl == "section"]
r.expect("outline", titles[-1:] == ["Research gaps"], f"a single closing Research gaps section (last section: {titles[-1:]})")
extra = [t for t in titles[:-1] if not any(re.search(p, t, flags=re.I) for p in TOPICS.values())]
r.expect("outline", not extra, "no sections beyond prd.md §3.1 item 3" if not extra
         else f"sections beyond prd.md §3.1 item 3: {extra} -- change prd.md first (SKILL §3)", warn=True)
r.expect("label", "\\label{chap:state-of-the-art}" in text, "carries \\label{chap:state-of-the-art}")
cut = text.find("\\section{Research gaps}")
themes_text, gaps = text[:cut], text[cut:]
for sec in ("voice-uav", "soa-dual-path", "swarm-control-sota", "speech-components"):
    chunk = themes_text[themes_text.find(f"\\label{{sec:{sec}}}"):]
    chunk = chunk[: chunk.find("\\section{", 1) if "\\section{" in chunk[1:] else None]
    r.expect("table", chunk.count("\\begin{table}") == 1 and "\\paragraph{Critical comparison.}" in chunk,
             f"section `{sec}` has one comparison table and a Critical comparison paragraph")
    r.expect("table", "This work &" in chunk, f"section `{sec}`'s table ends with a `This work` row")
r.expect("outline", "\\paragraph{Synthesis.}" in gaps, "Research gaps opens with its `Synthesis.` paragraph")
r.expect("outline", "\\paragraph{Conceded prior art.}" in gaps, "the published systems are conceded by name before the gaps")
for g in ("G1", "G2", "G3"):
    r.expect("outline", f"\\paragraph{{Gap {g}," in gaps, f"Research gaps has its `Gap {g}` paragraph")
r.expect("outline", "\\label{tab:lim-positioning}" in gaps and "\\cite{lim2025}" in gaps,
         "the positioning against Lim et al. sits in Research gaps (it compares a study to this work)")

# -- Studies compared to this work only in the gaps (the Master's rule, prd.md §3.1) -------------
# The survey may name "this work" only in the tables' last rows; a sentence in a theme section that
# compares a study to "this document"/"this system"/"this design" is positioning out of place.
prose_themes = re.sub(r"\\begin\{table\}.*?\\end\{table\}", "", themes_text, flags=re.S)
leaks = [(m.group(), r.ch.line_of(text.find(m.group()))) for m in
         re.finditer(r"[^.]*\bthis (?:document|system|design|work)\b[^.]*\.", prose_themes[prose_themes.find("\\section{"):])]
r.expect("positioning", not leaks, "no theme section compares a study to this work" if not leaks
         else f"{len(leaks)} theme-section sentence(s) mention this work -- move to Research gaps: "
         + "; ".join(f"l.{ln}: {s.strip()[:80]}" for s, ln in leaks[:3]), warn=True)


def cites(chunk: str) -> set[str]:
    return {k.strip() for m in re.findall(r"\\cite\{([^}]*)\}", chunk) for k in m.split(",")}


new = cites(gaps) - cites(themes_text)
r.expect("positioning", not new, "Research gaps introduces no source the theme sections did not review"
         if not new else f"Research gaps cites {sorted(new)} that no theme section reviewed -- a synthesis "
         "should summarise, not introduce")
closers = {"G1": ("sec:membership-rule", "sec:contributions"), "G2": ("sec:dual-path", "sec:latency-budget"),
           "G3": ("sec:resource-allocation",)}
for g, labels in closers.items():
    para = gaps[gaps.find(f"\\paragraph{{Gap {g},"):]
    para = para[: para.find("\\paragraph{", 1) if "\\paragraph{" in para[1:] else None]
    missing = [lb for lb in labels if f"\\ref{{{lb}}}" not in para]
    r.expect("positioning", not missing, f"Gap {g} names what closes it ({', '.join(labels)})"
             if not missing else f"Gap {g} does not point at {missing}")

# -- Table 3: the constrained-decoding and quantisation surveys belong to the Master -------------
master_only = {"geng2023", "willard2023", "koo2024", "park2024", "tam2024", "gptq", "awq", "spqr",
               "kurtic2025", "kurt2026", "slmquant", "sbc2025", "qin2021", "massive", "snips2018", "slurp2020"}
used = cites(text)
r.expect("table3", not used & master_only, "no Master-owned literature re-surveyed here" if not used & master_only
         else f"Master literature cited here: {sorted(used & master_only)} -- one sentence and a cross-reference "
         "to the \\emph{Mémoire de Master} instead (Table 3, write-once)")
r.expect("table3", "M\\'emoire de\nMaster" in text or "M\\'emoire de Master" in text, "the hand-off to the Master is named")

# -- Numbers that belong to a cited paper: the citation agent must verify ------------------------
paper_numbers = [("74.81\\%", "contreras2020"), ("93.33\\%", "contreras2020"), ("up to 62\\%", "typefly2024"),
                 ("below 1.5~s", "typefly2024"), ("eleven tasks", "typefly2024"), ("more than 1{,}000", "silva2026"),
                 ("110 geofence-violation", "silva2026"), ("three real quadcopters", "silva2026"),
                 ("Q5\\_K\\_M", "sikorski2025"), ("six general-purpose language models", "iannoli2026"),
                 ("0.81 at 1.233~s", "simoes2024"), ("0.99 at\n0.021~s", "simoes2024"), ("93\\% at 7~ms", "henry2026"),
                 ("79\\% at 202~ms", "henry2026"), ("82\\% and 59\\%", "henry2026"), ("106~ms on a", "henry2026"),
                 ("1{,}006~ms to 81~ms", "relays2s"), ("20~Hz", "skysim2026"), ("0.5~m/s", "skysim2026"),
                 ("3, 10 and 30", "skysim2026"), ("34~s for 3 drones", "skysim2026"), ("above 100~s", "skysim2026"),
                 ("about 4.0~s", "commandswarm2026"), ("about 5.2~s", "commandswarm2026"),
                 ("6.7--14B", "commandswarm2026"), ("680{,}000 hours", "whisper"), ("39 million", "whisper"),
                 ("80~ms frame", "oww"), ("32~ms windows", "silero"), ("in 38\\%", "lim2025"),
                 ("40\\%, is obtained", "lim2025"), ("temperature of 0.2", "lim2025")]
rows = ["| line | claim | must be found in |", "|---|---|---|"]
for anchor, key in paper_numbers:
    where = r.ch.find(anchor)
    r.expect("paper-number", bool(where), f"anchor `{anchor}` present", where[0] if where else None)
    if where:
        rows.append(f"| {where[0]} | {anchor} | {key} (primary source, not the candidate notes) |")
r.manual.append("### Numbers quoted from papers (citation agent: find each in the paper)\n\n" + "\n".join(rows))
r.manual.append("### For the citation agent\n\n- Every TABLE CELL is a claim about its source. A dash is correct "
                "when the source does not state the property; a filled cell the source does not support is a "
                "BLOCKER. Check tab:voice-uav-survey, tab:soa-dual-path, tab:soa-swarm and tab:soa-speech cell by "
                "cell, and the Lim et al. column of tab:lim-positioning.\n- "
                ".scratch/thesis-bibliography/ingenieur-candidates.md records corrected claims for several keys "
                "(dualattn2023 especially); it is a lead, the paper is the evidence.")
r.manual.append("### For the argument agent\n\n- Critical comparisons: each must read its table column by column "
                "and compare the studies to each other; the chapter promises they are compared to this work only "
                "in Research gaps. The script's positioning WARN lists theme sentences that mention this work.\n"
                "- Silence claims ('no system in the table', 'none of the sources', 'no prior row'): each must be "
                "scoped to the studies reviewed, never to the literature, and must be true of the table as drawn.\n"
                "- Gaps G1-G3: each must follow from the tables, and each must be closed by what it names (C4's "
                "two clauses, the core allocation of Chapter 4) without promising a result Chapter 6 does not "
                "report (the reflex budget is MISSED under load: a gap may say it is measured, not that it is met).\n"
                "- Conceded prior art: CommandSwarm, SkySim and MIRA were conceded in the reviewed Ch2 (issue 07); "
                "check nothing conceded there is now claimed, and that the concession to Silva and Burke and to the "
                "fixed-language systems is fair.")
sys.exit(r.finish())
