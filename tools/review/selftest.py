#!/usr/bin/env python3
"""Mutation test for the pre-review scripts: does each one catch an error planted in its chapter?

A checker that passes every chapter proves nothing until it has been seen to fail. For each script
this plants one realistic error in an in-memory copy of the chapter (a mistyped result, a wrong
count, a citation in the wrong document) and requires the script to exit 1 with a FAIL of the
expected kind. The real chapter and the real report are never touched.

    ~/miniconda3/envs/pfe_swarm/bin/python tools/review/selftest.py
"""

import io
import runpy
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lib  # noqa: E402

#: script -> (chapter file, text to replace, replacement, FAIL check that must fire)
MUTATIONS = {
    "master_ch1": ("master/ch1_introduction.tex", "floor at 27.93~tok/s", "floor at 27.39~tok/s", "claim"),
    "master_ch2": ("master/ch3_state_of_the_art.tex", "model~\\cite{gptq}, with on-device", "model~\\cite{gptq,lora}, with on-device", "positioning"),
    "master_ch3": ("master/ch3_method.tex", "difference of 4.0\\%", "difference of 4.5\\%", "claim"),
    "master_bg": ("master/ch2_background.tex", "Hugging Face & 362~M", "Hugging Face & 360~M", "claim"),
    "master_ch4": ("master/ch4_results.tex", "SmolLM2-360M (785~ms)", "SmolLM2-360M (795~ms)", "claim"),
    "master_ch5": ("master/ch5_discussion.tex", "a margin of 67~ms", "a margin of 76~ms", "claim"),
    "ingenieur_ch1": ("ingenieur/ch1_introduction.tex", "& p95 $\\leq$ 150~ms &", "& p95 $\\leq$ 200~ms &", "requirements"),
    "ingenieur_ch3": ("ingenieur/ch3_architecture.tex", "more than 50~m from the origin", "more than 60~m from the origin", "claim"),
    "ingenieur_ch4": ("ingenieur/ch4_implementation.tex", "closer than 0.80~m and moves", "closer than 0.60~m and moves", "claim"),
    "ingenieur_ch5": ("ingenieur/ch5_validation.tex", "keyword offset is 545~ms idle", "keyword offset is 454~ms idle", "claim"),
    "ingenieur_bg": ("ingenieur/ch2_background.tex", "The delay is a wait rather than a computation:",
                     "The delay is a wait of 450~ms rather than a computation:", "foundations"),
    "ingenieur_ch2": ("ingenieur/ch3_state_of_the_art.tex", "\\section{Swarm control}",
                      "\\section{Swarm control}\nGrammars constrain decoding~\\cite{geng2023}.", "table3"),
    "ingenieur_ch6": ("ingenieur/ch6_conclusion.tex", "End-to-end latency (3{,}122~ms", "End-to-end latency (2{,}122~ms", "claim"),
}
#: Common checks, planted once each: a project-internal reference, an undefined code, an \\acrfull.
EXTRA = [
    ("master_ch2", "master/ch3_state_of_the_art.tex", "as part of Contribution~C3.", "as part of Contribution~C3, as prd.md fixes.", "internal"),
    # Background is foundations only: a result slipped into it must FAIL, and a moved passage repeated in Method must FAIL.
    ("master_bg", "master/ch2_background.tex", "and is bounded by arithmetic.", "and is bounded by arithmetic, at 27.93~tok/s here.", "foundations"),
    ("master_bg", "master/ch3_method.tex", "\\paragraph{Adaptation method.}", "\\paragraph{Adaptation method.} LoRA works by freezing the pretrained weight matrices.", "write-once"),
    # The Ingenieur Background names the Master's foundations once; an explanation elsewhere must FAIL.
    ("ingenieur_bg", "ingenieur/ch2_background.tex", "\\paragraph{Operating point.}",
     "\\paragraph{Operating point.} Low-rank adaptation freezes the pretrained weights.", "write-once"),
    # The Ingenieur state of the art: Research gaps may not introduce a source the themes did not review.
    ("ingenieur_ch2", "ingenieur/ch3_state_of_the_art.tex", "\\paragraph{Conceded prior art.} Three",
     "\\paragraph{Conceded prior art.} Simulation is routine~\\cite{pyflyt}. Three", "positioning"),
    ("master_ch5", "master/ch5_discussion.tex", "Only three configurations", "Under Exp-7, only three configurations", "code"),
    ("master_ch1", "master/ch1_introduction.tex", "\\gls{json}", "\\acrfull{json}", "acronym"),
    ("ingenieur_ch3", "ingenieur/ch3_architecture.tex", "\\texttt{takeoff} & \\texttt{LANDED} &",
     "\\texttt{takeoff} & \\texttt{LANDED}, \\texttt{FLYING} &", "legality"),
    # Ch4 promises parameters only: a measured rate slipped in beside the operating point must FAIL.
    ("ingenieur_ch4", "ingenieur/ch4_implementation.tex", "reports those rates.",
     "reports those rates, a test false-reject rate of 0.027 among them.", "promise"),
    # ... and the state machine's code is exercised: a claimed transition the code does not make must FAIL.
    ("ingenieur_ch4", "ingenieur/ch4_implementation.tex", "The 50 cells, five", "The 45 cells, five", "claim"),
    # Ch5's verdicts were fixed before measurement: a softened one must FAIL.
    ("ingenieur_ch5", "ingenieur/ch5_validation.tex", "\\paragraph{Preemption recovery.} The criterion is missed",
     "\\paragraph{Preemption recovery.} The criterion is met", "verdict"),
    # Ch6's Conclusion must remain unhedged: a soft modal slipped into Section 6.4 must FAIL.
    ("ingenieur_ch6", "ingenieur/ch6_conclusion.tex", "The measured data answer the first clause",
     "The measured data suggests the first clause", "register"),
]


def run(script: str, mutate: tuple[str, str, str] | None) -> tuple[int, str]:
    original = lib.Chapter.load.__func__

    def load(cls, doc, rel):
        ch = original(cls, doc, rel)
        if mutate and rel == mutate[0]:
            assert mutate[1] in ch.raw, f"{script}: mutation target not in chapter -- update selftest.py"
            raw = ch.raw.replace(mutate[1], mutate[2], 1)
            ch = cls(doc, ch.path, raw, [lib.strip_comment(line) for line in raw.splitlines()])
        return ch

    lib.Chapter.load = classmethod(load)
    lib._INDEX = None
    out = io.StringIO()
    try:
        with redirect_stdout(out):
            runpy.run_path(str(HERE / f"{script}.py"), run_name="__main__")
        code = 0
    except SystemExit as e:
        code = int(e.code or 0)
    finally:
        lib.Chapter.load = classmethod(original)
    return code, out.getvalue()


def main() -> int:
    lib.REPORTS = Path(tempfile.mkdtemp())  # never overwrite the real reports
    bad = 0
    for script, rel, old, new, check in [(k, *v) for k, v in MUTATIONS.items()] + EXTRA:
        # The baseline may already FAIL on a real finding; the planted error must add a NEW failure.
        base, base_out = run(script, None)
        code, out = run(script, (rel, old, new))
        fails = lambda text: {l.strip() for l in text.splitlines() if l.strip().startswith(f"FAIL {check}")}  # noqa: E731
        caught = code == 1 and bool(fails(out) - fails(base_out))
        print(f"  {'ok  ' if caught else 'FAIL'} {script:<14} baseline exit {base}; "
              f"planted `{new[:40]!r}` -> exit {code}, {'caught by ' + check if caught else 'NOT caught'}")
        bad += not caught
    print("\nSELF-TEST " + ("PASSED" if not bad else f"FAILED ({bad})"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
