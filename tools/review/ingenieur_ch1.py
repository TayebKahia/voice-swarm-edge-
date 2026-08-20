#!/usr/bin/env python3
"""Pre-review checks for Ingénieur Ch1 (Introduction). See tools/review/lib.py.

Ch1 of the Ingénieur quotes requirements, not results ("no requirement is quoted here with a
result attached to it"), so its sources are prd.md's requirement tables and research questions.
The script also enforces that promise: no measured value from results/ may appear in the prose.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (INGENIEUR, RESULTS, Review, csv_rows, main_order, numbers, outline_check, prd,  # noqa: E402
                 prd_requirements, requirement_table_check, rq_check)

r = Review("ingenieur_ch1", "ingenieur", INGENIEUR[0], INGENIEUR[1:])
r.common()
text = r.ch.text

outline_check(r, 0, {"operational context": r"operational context", "engineering requirements": r"requirements",
                     "the safety problem": r"safety problem"})
r.expect("label", "\\label{chap:introduction}" in text, "carries \\label{chap:introduction}")

# -- RQs and contribution against prd.md §2 -----------------------------------------------------
rq_check(r, 2)
rq_check(r, 3)
c4 = re.search(r"\*\*C4\.\*\* (.*?) \(\[", prd())
body = re.search(r"\\textbf\{C4\.\}\s*(.*?)\\end\{itemize\}", text, flags=re.S)
r.expect("contribution", bool(c4 and body) and re.sub(r"\s+", " ", body.group(1)).strip().rstrip(".") ==
         c4.group(1).strip().rstrip("."), "C4 matches prd.md §2.1 verbatim")
r.expect("contribution", not re.search(r"\\textbf\{C[123]\.\}", text), "C1-C3 not claimed here (Master's, Table 2)")
n_contrib = len(re.findall(r"^- \*\*C\d\.\*\*", prd(), flags=re.M))
r.text_claim("claim", "four claimed contributions", n_contrib == 4, f"prd.md §2.1 lists {n_contrib} contributions")

# -- Requirement tables and the counts quoted about them ----------------------------------------
requirement_table_check(r, "tab:functional-requirements", target_col=2, source_col=None, strict=False)
requirement_table_check(r, "tab:nonfunctional-requirements", target_col=2, source_col=3)
reqs = prd_requirements()
n_fr = sum(k.startswith("FR-") for k in reqs)
n_nfr = sum(k.startswith("NFR-") for k in reqs)
r.number("Twelve functional requirements", n_fr, "FR rows in prd.md Table 11")
r.number("twenty-one non-functional rows", n_nfr, "NFR rows in prd.md Table 12 (9a and 9b included)")
fr_shown = len(re.findall(r"^FR-\d+ &", text, flags=re.M))
r.number("The remaining six functional", n_fr - fr_shown, f"{n_fr} - {fr_shown} tabulated here")
r.text_claim("claim", "more than sixteenfold", 16 < 2500 / 150 < 17, f"NFR-2 / NFR-1 = 2500 / 150 = {2500 / 150:.1f}")
r.text_claim("claim", "Five chapters follow", len(main_order("ingenieur")) - 1 == 5,
             f"{len(main_order('ingenieur')) - 1} chapters after this one in main_ingenieur.tex")

# -- Hardware and controller facts against prd.md -----------------------------------------------
p = prd()
for anchor, needle in (("8~GB of memory", "8 GB"), ("four Cortex-A76 cores", "Cortex-A76"),
                       ("$N = 5$ vehicles at 50~Hz", "50 Hz")):
    r.text_claim("fact", anchor, needle in p, f"`{needle}` stated in prd.md")

# -- Structure paragraph: chapters in order, labels as the header comment fixes them ------------
refs = list(dict.fromkeys(re.findall(r"Chapter~\\ref\{(chap:[^}]*)\}", text[text.find("Structure of this document"):])))
want = ["chap:state-of-the-art", "chap:architecture", "chap:implementation", "chap:validation", "chap:demonstration"]
r.expect("outline", refs == want, f"structure paragraph order {refs}")

# -- The chapter's own promise: no result quoted --------------------------------------------------
measured = set()
for f in ("surface_b.csv", "exp3.csv", "exp4.csv", "mcnemar.csv"):
    for row in csv_rows(RESULTS / f):
        for v in row.values():
            if re.fullmatch(r"\d+\.\d{2,}", v or ""):
                measured.add(v.rstrip("0"))
targets = {v.rstrip("0") for row in prd_requirements().values() for v in re.findall(r"\d+\.\d+", " ".join(row))}
leaks = [n for n in numbers(r.ch) if n.places >= 2 and n.text.rstrip("0") in measured - targets]
r.expect("promise", not leaks, "no measured result quoted (the chapter promises targets only)" if not leaks
         else f"measured values in the prose: {[(n.text, n.line) for n in leaks]}")
r.expect("table3", "\\cite{lim2025}" in text, "Lim et al. named as the baseline (Ch2 owns the positioning)")

r.manual.append("### For the argument agent\n\n- The safety argument (l.167-276) makes several design claims that "
                "Ch3 must later derive (membership rule, clamp placement). List each promise with the chapter it "
                "points to, so the Ch3-Ch6 reviews can check them.\n- NFR-12 phrasing is locked project-wide "
                "(SKILL §2): check both occurrences (table row and l.146-151, l.256-258) match it.\n"
                "- Requirement wording diffs below: a paraphrase that narrows or widens a requirement is a finding.")
sys.exit(r.finish())
