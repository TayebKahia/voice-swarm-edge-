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
from lib import MASTER, RESULTS, Review, md_table, outline_check  # noqa: E402

r = Review("master_ch2", "master", MASTER[1], [MASTER[0], *MASTER[2:]])
r.common()
text = r.ch.text

# -- Shape: four themes, then Positioning = Synthesis / Gap / Delta (SKILL §3, Ch2) --------------
outline_check(r, 1, {"edge LLM inference and SBC benchmarking": r"edge llm|single-board",
                     "quantisation": r"^quantisation$", "constrained decoding": r"constrained decoding",
                     "spoken-language understanding for robotics": r"spoken-language"})
titles = [t for lvl, t, _ in r.ch.sections() if lvl == "section"]
r.expect("outline", titles[-1:] == ["Positioning"], f"a single closing Positioning section (last section: {titles[-1:]})")
pos = text[text.find("\\section{Positioning}"):]
for part in ("Synthesis", "Gap", "Delta"):
    r.expect("outline", f"\\paragraph{{{part}.}}" in pos, f"Positioning has its `{part}.` paragraph")


def cites(chunk: str) -> set[str]:
    return {k.strip() for m in re.findall(r"\\cite\{([^}]*)\}", chunk) for k in m.split(",")}


themes, positioning = cites(text[: text.find("\\section{Positioning}")]), cites(pos)
new = positioning - themes
r.expect("positioning", not new, "Positioning introduces no source the theme sections did not review"
         if not new else f"Positioning cites {sorted(new)} that no theme section reviewed -- a synthesis "
         "should summarise, not introduce")
gap_para = pos[pos.find("\\paragraph{Gap.}"): pos.find("\\paragraph{Delta.}")]
r.expect("positioning", "gap" in gap_para.lower(), "Gap paragraph states the gap", warn=True)
for c in ("C1", "C2", "C3"):
    r.expect("positioning", f"Contribution {c}" in pos, f"Delta maps {c} onto the gap")

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
r.text_claim("coherence", "Three of those models are carried through to the quantised artefact", False,
             "Ch2 states three quantised + one reference-precision control; Ch1 says 'three deployment candidates' plus a control"
             " -- the argument agent checks the two read as one story", warn=True)

# -- Numbers that belong to a cited paper, not to results/: the citation agent must verify ------
paper_numbers = [("twenty-five quantised language", "sbc2025"), ("three single-board computers", "sbc2025"),
                 ("two inference runtimes", "sbc2025"), ("roughly 1.5~billion parameters", "sbc2025"),
                 ("up to four times", "sbc2025"), ("under one percent in perplexity", "spqr,gptq"),
                 ("seven billion parameters and above", "kurtic2025,kurt2026"),
                 ("one-million-example", "massive")]
rows = ["| line | claim | must be found in |", "|---|---|---|"]
for anchor, key in paper_numbers:
    where = r.ch.find(anchor)
    r.expect("paper-number", bool(where), f"anchor `{anchor}` present", where[0] if where else None)
    if where:
        rows.append(f"| {where[0]} | {anchor} | {key} (primary source, not the candidate notes) |")
r.manual.append("### Numbers quoted from papers (citation agent: find each in the paper)\n\n" + "\n".join(rows))
r.manual.append("### For the argument agent\n\n- Gap (l.162-176): each of the four sentences claims a literature "
                "is *silent* on something. Silence is only defensible for the papers actually cited -- check the "
                "claim is scoped to 'the literature reviewed here'.\n- Delta: C1 is described as 'isolating the "
                "grammar's own contribution'. The isolation is the ablation (Ch4), not the schema -- judge whether "
                "C1 is being credited with C3's measurement.\n- .scratch/thesis-bibliography/master-candidates.md "
                "'Notes for the author' flags a tension with C3's framing: read it.")
sys.exit(r.finish())
