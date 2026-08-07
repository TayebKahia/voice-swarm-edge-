#!/usr/bin/env python3
r"""
check_tex.py -- structural pre-flight check for a LaTeX source.

Not a compiler. It catches the error classes that actually break pdflatex on a
table-heavy document, without needing a TeX installation:

  1. non-ASCII characters in text mode      (pdflatex cannot render them)
  2. unmatched \begin / \end
  3. unbalanced braces
  4. wrong cell count in a tabular/longtable row  (-> "Extra alignment tab")
  5. P{} / p{} column widths summing past \textwidth  (-> overfull hbox)
  6. \ref with no \label, \cite with no \bibitem
  7. bare _ or # in text mode

Comments and lstlisting/verbatim bodies are excluded from every check.

Usage
-----
    python check_tex.py docs/PRD.tex     # exit 0 = clean, 1 = problems found
    python check_tex.py --selftest       # verify the checker itself
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

VERBATIM = ("lstlisting", "verbatim", "Verbatim", "minted", "alltt")

# Page geometry, used only for the column-width sum. Matches PRD.tex:
# a4paper, margin=2.2cm  ->  \textwidth = 16.6cm = 471.4pt
TEXTWIDTH_PT = 471.4
TABCOLSEP_PT = 4.0

# Commands that appear between \\ markers but are not part of a row.
RULE_CMD = re.compile(
    r"\\(?:top|mid|bottom)rule(?:\[[^\]]*\])?"
    r"|\\hline"
    r"|\\cmidrule(?:\([^)]*\))?(?:\[[^\]]*\])?\{[^}]*\}"
    r"|\\addlinespace(?:\[[^\]]*\])?"
    r"|\\end(?:first)?head|\\endlastfoot|\\endfoot"
    r"|\\nopagebreak|\\pagebreak|\\newpage"
)

# Lines where a bare # or _ is legitimate (macro definitions use #1, #2, ...).
DEFN = re.compile(
    r"\\(?:re)?newcommand|\\newcolumntype|\\newenvironment|\\def[^a-zA-Z]"
    r"|\\providecommand|\\lstdefinestyle|\\lstset|\\DeclareRobustCommand"
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def balanced(s: str, start: int) -> tuple[str, int]:
    """s[start] must be '{'. Return (inner text, offset just past matching '}')."""
    d, k = 0, start
    while k < len(s):
        if s[k] == "\\":
            k += 2
            continue
        if s[k] == "{":
            d += 1
        elif s[k] == "}":
            d -= 1
            if d == 0:
                return s[start + 1:k], k + 1
        k += 1
    return "", len(s)


def count_cols(spec: str) -> tuple[int, list[float | None]]:
    """Parse a column spec. Return (ncols, per-column \\textwidth fraction or None)."""
    cols, widths, k = 0, [], 0
    while k < len(spec):
        c = spec[k]
        if c in "@><!":                                    # @{..} >{..} <{..} !{..}
            k += 1
            if k < len(spec) and spec[k] == "{":
                _, k = balanced(spec, k)
            continue
        if c in "| \t\n":
            k += 1
            continue
        if c in "lcrX":
            cols += 1
            widths.append(None)
            k += 1
            continue
        if c in "pmbPCLR":                                 # takes a {..} argument
            cols += 1
            k += 1
            arg = ""
            if k < len(spec) and spec[k] == "{":
                arg, k = balanced(spec, k)
            arg = arg.strip()
            if re.fullmatch(r"[0-9.]+", arg):              # P{0.24} custom coltype
                widths.append(float(arg))
            elif (mm := re.fullmatch(r"([0-9.]+)\s*\\textwidth", arg)):
                widths.append(float(mm.group(1)))          # p{0.24\textwidth}
            else:
                widths.append(None)
            continue
        if c == "*":                                       # *{n}{spec}
            k += 1
            rep, k = balanced(spec, k)
            sub, k = balanced(spec, k)
            try:
                n = int(rep.strip())
            except ValueError:
                continue
            n_sub, w_sub = count_cols(sub)
            cols += n * n_sub
            widths += w_sub * n
            continue
        k += 1
    return cols, widths


def count_cells(row: str) -> int:
    """Number of cells in a row: unescaped & at brace depth 0, plus one."""
    n, d, k = 1, 0, 0
    while k < len(row):
        if row[k] == "\\":
            k += 2
            continue
        if row[k] == "{":
            d += 1
        elif row[k] == "}":
            d -= 1
        elif row[k] == "&" and d == 0:
            n += 1
        k += 1
    return n


# ---------------------------------------------------------------------------
# main check
# ---------------------------------------------------------------------------

def bib_keys(doc: str, src: Path | None) -> set[str]:
    """Citation keys defined in BibTeX files.

    The bibliography used to be a `thebibliography` in a sibling .tex, so a chapter
    checked on its own could never resolve its own \\cite calls.  It is now
    thesis/references.bib, which this walks up to find -- so a standalone chapter
    check is conclusive about citations.  Files named by \\addbibresource are read
    too, for a main.tex that points somewhere else.
    """
    base = (src.parent if src else Path(".")).resolve()
    files = [base / name for name in re.findall(r"\\addbibresource\{([^}]+)\}", doc)]
    for d in (base, *base.parents):
        cand = d / "references.bib"
        if cand.exists():
            files.append(cand)
            break
    keys: set[str] = set()
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue                           # named but absent: not this tool's problem
        keys |= {k for t, k in re.findall(r"@([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,", text)
                 if t.lower() not in {"string", "comment", "preamble"}}
    return keys


def check(raw: str, src: Path | None = None) -> tuple[list[str], list[str], dict]:
    problems: list[str] = []
    notes: list[str] = []

    # Build `doc`: same length as `raw`, with comments and verbatim bodies
    # blanked to spaces, so every offset still maps to its original line.
    buf = list(raw)

    def blank(a: int, b: int) -> None:
        for k in range(a, b):
            if buf[k] != "\n":
                buf[k] = " "

    verb_spans: list[tuple[int, int]] = []
    for env in VERBATIM:                       # verbatim first: % there is literal
        for m in re.finditer(r"\\begin\{" + env + r"\}", raw):
            e = re.search(r"\\end\{" + env + r"\}", raw[m.end():])
            if not e:
                problems.append(f"L{raw.count(chr(10), 0, m.start()) + 1}: "
                                f"\\begin{{{env}}} never closed")
                continue
            verb_spans.append((m.start(), m.end() + e.end()))
            blank(m.end(), m.end() + e.start())

    i = 0
    while i < len(raw):                        # comments: unescaped % to EOL
        if raw[i] == "\\":
            i += 2
            continue
        if raw[i] == "%" and buf[i] == "%":
            j = raw.find("\n", i)
            j = len(raw) if j < 0 else j
            blank(i, j)
            i = j
            continue
        i += 1

    doc = "".join(buf)
    nl = [m.start() for m in re.finditer("\n", doc)]
    raw_lines = raw.split("\n")

    def line_of(off: int) -> int:
        lo, hi = 0, len(nl)
        while lo < hi:
            mid = (lo + hi) // 2
            if nl[mid] < off:
                lo = mid + 1
            else:
                hi = mid
        return lo + 1

    def in_verb(off: int) -> bool:
        return any(a <= off < b for a, b in verb_spans)

    # -- 1. non-ASCII in text mode -----------------------------------------
    flagged_lines = set()
    for off, ch in enumerate(doc):
        if ord(ch) > 127 and not in_verb(off):
            n = line_of(off)
            if n in flagged_lines:
                continue
            flagged_lines.add(n)
            problems.append(f"L{n}: non-ASCII U+{ord(ch):04X} -- pdflatex text mode "
                            f"cannot render this: {raw_lines[n - 1].strip()[:70]}")

    # -- 2. environment matching -------------------------------------------
    stack: list[tuple[str, int]] = []
    for m in re.finditer(r"\\(begin|end)\{([A-Za-z]+\*?)\}", doc):
        kind, env = m.group(1), m.group(2)
        n = line_of(m.start())
        if kind == "begin":
            stack.append((env, n))
        elif not stack:
            problems.append(f"L{n}: \\end{{{env}}} with nothing open")
        elif stack[-1][0] != env:
            problems.append(f"L{n}: \\end{{{env}}} closes \\begin{{{stack[-1][0]}}} "
                            f"opened at L{stack[-1][1]}")
            stack.pop()
        else:
            stack.pop()
    for env, n in stack:
        problems.append(f"L{n}: \\begin{{{env}}} never closed")

    # -- 3. brace balance --------------------------------------------------
    depth, i = 0, 0
    while i < len(doc):
        if doc[i] == "\\":
            i += 2
            continue
        if doc[i] == "{":
            depth += 1
        elif doc[i] == "}":
            depth -= 1
            if depth < 0:
                problems.append(f"L{line_of(i)}: closing brace with no opener")
                depth = 0
        i += 1
    if depth:
        problems.append(f"EOF: {depth} unclosed brace(s)")

    # -- 4. table cell counts and column widths ----------------------------
    tables = 0
    for m in re.finditer(r"\\begin\{(tabular|longtable|tabularx)\}", doc):
        env = m.group(1)
        k = m.end()
        while k < len(doc) and doc[k] in " \t\n":
            k += 1
        if k < len(doc) and doc[k] == "[":                 # optional [t]/[b]
            k = doc.index("]", k) + 1
            while k < len(doc) and doc[k] in " \t\n":
                k += 1
        if env == "tabularx":                              # width argument
            _, k = balanced(doc, k)
            while k < len(doc) and doc[k] in " \t\n":
                k += 1
        if k >= len(doc) or doc[k] != "{":
            problems.append(f"L{line_of(m.start())}: {env} has no column spec")
            continue
        spec, body_start = balanced(doc, k)
        ncols, widths = count_cols(spec)
        if ncols == 0:
            problems.append(f"L{line_of(m.start())}: {env} column spec parsed as "
                            f"0 columns: {spec!r}")
            continue
        tables += 1

        known = [w for w in widths if w is not None]
        if known and len(known) == ncols:
            total = sum(known) + ncols * 2 * TABCOLSEP_PT / TEXTWIDTH_PT
            tag = (f"L{line_of(m.start())}: {env} ({ncols} cols) widths + tabcolsep "
                   f"= {total:.3f}\\textwidth")
            if total > 1.0:
                problems.append(tag + "  -> exceeds \\textwidth, guaranteed overfull hbox")
            elif total > 0.985:
                notes.append(tag + "  -- very tight, may overfull")
        elif known:
            notes.append(f"L{line_of(m.start())}: {env} mixes fixed and fraction "
                         f"columns -- width sum not checked")

        # body up to the matching \end{env}, honouring nesting
        d, k2, body_end = 1, body_start, None
        pat = re.compile(r"\\(begin|end)\{(tabular|longtable|tabularx)\}")
        while (mm := pat.search(doc, k2)):
            d += 1 if mm.group(1) == "begin" else -1
            k2 = mm.end()
            if d == 0:
                body_end = mm.start()
                break
        if body_end is None:
            problems.append(f"L{line_of(m.start())}: {env} never closed")
            continue
        body = doc[body_start:body_end]
        if re.search(r"\\begin\{(tabular|longtable|tabularx)\}", body):
            notes.append(f"L{line_of(m.start())}: {env} contains a nested table -- "
                         f"cell counts not checked")
            continue

        # split into rows on \\ at brace depth 0
        rows, d, k3, last = [], 0, 0, 0
        while k3 < len(body):
            if body[k3] == "\\" and k3 + 1 < len(body) and body[k3 + 1] == "\\":
                if d == 0:
                    rows.append((last, body[last:k3]))
                    k3 += 2
                    while k3 < len(body) and body[k3] in " \t":
                        k3 += 1
                    if k3 < len(body) and body[k3] == "[":  # optional \\[2pt]
                        nx = body.find("]", k3)
                        if 0 <= nx < k3 + 20:
                            k3 = nx + 1
                    last = k3
                    continue
                k3 += 2
                continue
            if body[k3] == "\\":
                k3 += 2
                continue
            if body[k3] == "{":
                d += 1
            elif body[k3] == "}":
                d -= 1
            k3 += 1
        rows.append((last, body[last:]))

        for rel, chunk in rows:
            # booktabs rules and longtable head/foot markers sit between \\
            # markers, so strip them from the chunk rather than skipping it.
            row = RULE_CMD.sub("", chunk)
            if not row.strip():
                continue
            if "\\multicolumn" in row or "\\caption" in row:
                continue                       # spans columns / is not a row
            c = count_cells(row)
            if c != ncols:
                problems.append(f"L{line_of(body_start + rel)}: {env} row has "
                                f"{c} cell(s) but the spec declares {ncols}: "
                                f"{' '.join(row.split())[:70]!r}")

    # -- 5. refs / labels / cites ------------------------------------------
    labels = set(re.findall(r"\\label\{([^}]+)\}", doc))
    refs = {r.strip() for g in re.findall(r"\\(?:ref|autoref|pageref)\{([^}]+)\}", doc)
            for r in g.split(",")}
    bibs = set(re.findall(r"\\bibitem\{([^}]+)\}", doc))
    bibs |= bib_keys(doc, src)
    cites = {c.strip() for g in re.findall(r"\\cite[tp]?\{([^}]+)\}", doc)
             for c in g.split(",")}
    for r in sorted(refs - labels):
        problems.append(f"\\ref{{{r}}} has no matching \\label")
    for c in sorted(cites - bibs):
        problems.append(f"\\cite{{{c}}} has no matching \\bibitem")
    for l in sorted(labels - refs):
        notes.append(f"\\label{{{l}}} never referenced (harmless)")

    # -- 6. bare special characters in text mode ---------------------------
    for n, line in enumerate(doc.split("\n"), 1):
        if DEFN.search(line):
            continue
        s = re.sub(r"\\(?:[a-zA-Z]+\*?|.)", "", line)      # drop macros + escapes
        s = re.sub(r"\$[^$]*\$", "", s)                    # drop inline math
        for ch, name in (("_", "underscore"), ("#", "hash")):
            if ch in s:
                problems.append(f"L{n}: bare {name} {ch!r} in text mode: "
                                f"{line.strip()[:70]}")

    stats = {"lines": raw.count("\n") + 1, "tables": tables, "labels": len(labels),
             "refs": len(refs), "bibitems": len(bibs), "cites": len(cites)}
    return problems, notes, stats


# ---------------------------------------------------------------------------
# self-test -- a synthetic document with one instance of every fault
# ---------------------------------------------------------------------------

SELFTEST_DOC = r"""
\documentclass{article}
\usepackage{longtable,booktabs,array,ragged2e}
\newcolumntype{P}[1]{>{\RaggedRight\arraybackslash}p{#1\textwidth}}
\begin{document}

% a comment with a bare _ and # and an accent e -- must be ignored
\section{Good things}
See Table~\ref{tab:good} and \cite{ok2024}.

\begin{tabular}{@{}P{0.30}P{0.30}P{0.30}@{}}
\toprule
\textbf{A} & \textbf{B} & \textbf{C} \\
\midrule
one & two & three \\
\multicolumn{3}{@{}l}{spanning row is skipped} \\
\bottomrule
\end{tabular}

\begin{longtable}{@{}P{0.16}P{0.20}P{0.20}P{0.20}@{}}
\caption{Fine}\label{tab:good}\\
\toprule
\textbf{W} & \textbf{X} & \textbf{Y} & \textbf{Z} \\
\midrule
\endfirsthead
n & p & q & r \\
\end{longtable}

\lstlisting-free zone. Verbatim content is exempt:
\begin{verbatim}
  raw_underscore #1 100% and an accent: e
\end{verbatim}

FAULT 1: an accent in text mode -- \'e is fine but this is not: caf@ACCENT@
FAULT 7: bare underscore in run_all and hash \#ok vs #bad

\begin{tabular}{@{}P{0.60}P{0.60}@{}}
\toprule
too & wide \\
\bottomrule
\end{tabular}

\begin{tabular}{@{}P{0.16}P{0.16}P{0.16}P{0.16}P{0.16}@{}}
\toprule
a & b & c & d & e \\
f & g & h & i & j & k \\
\bottomrule
\end{tabular}

FAULT: \ref{nosuchlabel} and \cite{nosuchbib}

\begin{itemize}
\item unclosed on purpose
\end{itemiz}

\begin{thebibliography}{9}
\bibitem{ok2024} A reference.
\end{thebibliography}
\end{document}
"""
# The raw string above cannot hold a real accented byte, so splice one in here.
SELFTEST_DOC = SELFTEST_DOC.replace("@ACCENT@", "é")

EXPECTED = [
    ("non-ASCII in text mode",        "non-ASCII"),
    ("environment mismatch",          "closes \\begin{itemize}"),
    ("over-wide column spec",         "exceeds \\textwidth"),
    ("wrong cell count",              "declares 5"),
    ("dangling \\ref",                "nosuchlabel"),
    ("dangling \\cite",               "nosuchbib"),
    ("bare underscore in text",       "bare underscore"),
    ("bare hash in text",             "bare hash"),
]

MUST_NOT = [
    ("verbatim body flagged",         "raw_underscore"),
    ("comment flagged",               "a comment with a bare"),
    ("good 3-col tabular flagged",    "declares 3"),
    ("good 4-col longtable flagged",  "declares 4"),
    ("\\multicolumn row flagged",     "spanning row"),
]


def selftest() -> int:
    problems, notes, _ = check(SELFTEST_DOC)
    blob = "\n".join(problems)
    print("self-test on a synthetic document with 8 seeded faults\n")
    bad = 0
    for label, needle in EXPECTED:
        hit = needle in blob
        print(f"  {'detected' if hit else 'MISSED  '}  {label}")
        bad += 0 if hit else 1
    print()
    for label, needle in MUST_NOT:
        hit = needle in blob
        print(f"  {'FALSE POSITIVE' if hit else 'clean         '}  {label}")
        bad += 1 if hit else 0
    print()
    if bad:
        print(f"SELF-TEST FAILED ({bad} issue(s))\n")
        print("raw findings:")
        for p in problems:
            print("  ! " + p)
        return 1
    print("SELF-TEST PASSED -- the checker detects all 8 fault classes "
          "with no false positives")
    return 0


# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()

    path = Path(argv[1]) if len(argv) > 1 else Path("docs") / "project" / "PRD.tex"
    if not path.exists():
        print(f"not found: {path}", file=sys.stderr)
        return 2

    raw = path.read_text(encoding="utf-8")
    problems, notes, st = check(raw, path)

    print(f"checked {path}  ({st['lines']} lines, {st['tables']} tables)")
    print(f"  {st['labels']} labels, {st['refs']} refs, "
          f"{st['bibitems']} bibitems, {st['cites']} cites")
    print()
    if problems:
        print(f"{len(problems)} PROBLEM(S) -- these will break or disfigure the build:")
        for p in problems:
            print("  ! " + p)
    else:
        print("no problems found")
    if notes:
        print(f"\n{len(notes)} note(s):")
        for t in notes:
            print("  - " + t)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
