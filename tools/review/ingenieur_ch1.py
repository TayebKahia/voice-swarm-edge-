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
from lib import (INGENIEUR, RESULTS, THESIS, Review, csv_rows, main_order, numbers, outline_check, prd,  # noqa: E402
                 prd_requirements, requirement_table_check, rq_check)

r = Review("ingenieur_ch1", "ingenieur", INGENIEUR[0], INGENIEUR[1:])
r.common()
text = r.ch.text

outline_check(r, 0, {"operational context": r"operational context", "engineering requirements": r"requirements",
                     "the safety problem": r"safety problem", "objectives": r"objectives",
                     "contribution": r"contribution", "structure of the document": r"structure"})
r.expect("label", "\\label{chap:introduction}" in text, "carries \\label{chap:introduction}")

# -- RQs and contribution against prd.md §2 -----------------------------------------------------
rq_check(r, 2)
rq_check(r, 3)
# This document has one contribution, so it is named, not numbered (issue 06); its text is prd C4.
c4 = re.search(r"\*\*C4\.\*\* (.*?) \(\[", prd())
body = re.search(r"\\textbf\{Contribution\.\}\s*(.*?)\\end\{quote\}", text, flags=re.S)
r.expect("contribution", bool(c4 and body) and re.sub(r"\s+", " ", body.group(1)).strip().rstrip(".") ==
         c4.group(1).strip().rstrip("."), "the contribution matches prd.md §2.1 C4 verbatim")
r.expect("contribution", not re.search(r"\\textbf\{C[123]\.\}", text), "C1-C3 not claimed here (Master's, Table 2)")
n_contrib = len(re.findall(r"^- \*\*C\d\.\*\*", prd(), flags=re.M))
r.text_claim("claim", "four contributions claimed", n_contrib == 4, f"prd.md §2.1 lists {n_contrib} contributions")

# -- Requirement tables and the counts quoted about them ----------------------------------------
# Both tables name their criteria instead of printing prd IDs (issue 06, as the Master does); the
# maps send each name back to its prd row, so every cell is still compared with prd.
FR_NAMES = {"Offline speech recognition": "FR-5", "Reflex path": "FR-6", "Swarm controller": "FR-7",
            "Simulation backends": "FR-8", "Live demonstration": "FR-9", "Flight state machine": "FR-11"}
NFR_NAMES = {"Reflex latency": "NFR-1", "End-to-end latency": "NFR-2", "Per-stage attribution": "NFR-3",
             "Preemption recovery": "NFR-17", "Keyword false accepts": "NFR-15",
             "Keyword false rejects": "NFR-16", "Clean-audio recognition": "NFR-7",
             "Recognition in noise": "NFR-8", "Collisions": "NFR-12", "Formation accuracy": "NFR-13",
             "Offline operation": "NFR-14"}
EXPERIMENTS = {"Latency experiment": "Exp-2", "Acoustic-robustness experiment": "Exp-3",
               "Formation-control experiment": "Exp-4", "End-to-end run, networking disabled": "FR-5"}
requirement_table_check(r, "tab:functional-requirements", target_col=2, source_col=None, strict=False,
                        row_ids=FR_NAMES)
# prd Table 12 still records the plan to select the keyword operating point inside Exp-2. As built,
# train/train_wake.py fixes it on the validation split and scores the ambient-speech stream;
# eval/exp2.py quotes that result and never re-selects it (issue 06, pass 2, W2).
DEVIATIONS = {"NFR-15": ("Keyword-spotter evaluation",
                         "operating point and ambient false accepts come from train/train_wake.py "
                         "(results/wake_training.md); eval/exp2.py only quotes them")}
requirement_table_check(r, "tab:nonfunctional-requirements", target_col=2, source_col=3,
                        row_ids=NFR_NAMES, source_names=EXPERIMENTS, deviations=DEVIATIONS)
# "a criterion shared with the Memoire de Master carries the same name there": check it.
master_rows = set(re.findall(r"^([^&\n\\]+?) & ", (THESIS / "master/ch3_method.tex").read_text(), flags=re.M))
master_ids = {"NFR-2", "NFR-4", "NFR-5", "NFR-6", "NFR-7", "NFR-8", "NFR-9", "NFR-9a", "NFR-9b", "NFR-10",
              "NFR-11", "NFR-18"}   # the rows of Master tab:requirements (master_ch3.py CRITERIA)
for name, rid in NFR_NAMES.items():
    if rid in master_ids:
        r.expect("requirements", name in master_rows, f"shared criterion `{name}` ({rid}) has the same name "
                 "in Master tab:requirements", r.ch.find(f"{name} &")[0])
reqs = prd_requirements()
n_fr = sum(k.startswith("FR-") for k in reqs)
n_nfr = sum(k.startswith("NFR-") for k in reqs)
r.number("Twelve \\glspl{fr}", n_fr, "FR rows in prd.md Table 11")
r.number("twenty-one \\glspl{nfr}", n_nfr, "NFR rows in prd.md Table 12 (9a and 9b included)")
fr_shown = sum(bool(re.search(rf"^{re.escape(n)} &", text, flags=re.M)) for n in FR_NAMES)
r.number("The remaining six of the twelve", n_fr - fr_shown, f"{n_fr} - {fr_shown} tabulated here")
r.text_claim("claim", "The rest of this document has six chapters", len(main_order("ingenieur")) - 1 == 6,
             f"{len(main_order('ingenieur')) - 1} chapters after this one in main_ingenieur.tex")

# -- Hardware and controller facts against prd.md -----------------------------------------------
p = prd()
for anchor, needle in (("8~GB of memory", "8 GB"), ("four Cortex-A76 cores", "Cortex-A76"),
                       ("ticking at a nominal 50~Hz", "50 Hz")):
    r.text_claim("fact", anchor, needle in p, f"`{needle}` stated in prd.md")

# -- Structure paragraph: chapters in order, labels as the header comment fixes them ------------
refs = list(dict.fromkeys(re.findall(r"Chapter~\\ref\{(chap:[^}]*)\}", text[text.find("Structure of this document"):])))
want = ["chap:background", "chap:state-of-the-art", "chap:architecture", "chap:implementation", "chap:validation", "chap:demonstration"]
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
