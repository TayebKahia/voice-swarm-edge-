#!/usr/bin/env python3
"""Pre-review checks for Ingénieur Ch2 (State of the Art). See tools/review/lib.py.

At the time of writing this chapter is a scaffold: section headings and NOTE comments, no prose.
The script therefore does two jobs. While the chapter is a scaffold it checks the plan -- that
every citation key the NOTEs intend to use is in references.bib, and that the section list agrees
with prd.md §3.1 -- and it exits 2 ("not reviewable yet") so a review run knows to stop. Once
prose exists, the common checks and the Table 3 boundary apply as for any other chapter.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import INGENIEUR, Review, bib, outline_check  # noqa: E402

r = Review("ingenieur_ch2", "ingenieur", INGENIEUR[1], [INGENIEUR[0], *INGENIEUR[2:]])
r.common()
text, raw = r.ch.text, r.ch.raw

outline_check(r, 1, {"voice-controlled UAV systems": r"voice-controlled", "positioning against Lim et al.": r"lim"})
extra = [t for lvl, t, _ in r.ch.sections() if lvl == "section"
         and not re.search(r"voice-controlled|lim", t, flags=re.I)]
r.expect("outline", not extra, f"sections beyond prd.md §3.1 item 2: {extra} -- SKILL §3: change prd.md first, "
         "then the scaffold" if extra else "no sections beyond prd.md §3.1", warn=True)

# -- The plan in the NOTE comments --------------------------------------------------------------
entries = bib()
planned = set(re.findall(r"\\cite\{(\w+)\}", raw))
planned |= {k for k in re.findall(r"\b([a-z]+\d{4})\b", " ".join(l for l in raw.splitlines() if "Verified keys" in l
                                                                  or re.match(r"%\s{2,}\w", l)))}
for k in sorted(planned):
    r.expect("planned-cite", k in entries, f"planned key `{k}` is in references.bib" if k in entries
             else f"planned key `{k}` is NOT in references.bib -- add it (author's job) or drop it from the plan")

# -- Table 3: the constrained-decoding survey belongs to the Master ------------------------------
master_only = {"geng2023", "willard2023", "koo2024", "park2024", "tam2024", "gptq", "awq", "spqr",
               "kurtic2025", "kurt2026", "slmquant", "sbc2025"}
used = {k.strip() for m in re.findall(r"\\cite\{([^}]*)\}", text) for k in m.split(",")}
r.expect("table3", not used & master_only, "no Master-owned literature re-surveyed here" if not used & master_only
         else f"Master Ch2 literature cited here: {sorted(used & master_only)} -- state it in one sentence and cite "
         "the \\emph{Mémoire de Master} instead (Table 3, write-once)")

# -- Reviewable yet? ------------------------------------------------------------------------------
words = len(re.findall(r"[A-Za-z]{2,}", re.sub(r"\\(?:chapter|section|label)\{[^}]*\}", "", text)))
ready = words >= 300
r.expect("ready", ready, f"{words} words of prose -- " + ("reviewable" if ready else
         "scaffold only; run the review after the prose is drafted"), warn=True)
if ready:
    r.expect("table3", "\\cite{lim2025}" in text, "positions against \\cite{lim2025}")
    r.manual.append("### For the argument agent\n\n- The Gap NOTE concedes two conjuncts by name (CommandSwarm, "
                    "SkySim) and flags MIRA: check each concession made in the prose is the one the NOTE records.\n"
                    "- .scratch/thesis-bibliography/ingenieur-candidates.md records the claim each key may carry; "
                    "several were corrected. Every citation must be checked against that record AND the paper.")
code = r.finish()
sys.exit(code if code or ready else 2)
