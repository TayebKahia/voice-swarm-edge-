"""Deterministic pre-review checks for one thesis chapter.

A chapter script (`tools/review/master_ch1.py`, ...) builds a `Review`, runs the common checks
every chapter gets, then adds its own claims: each claim names an *anchor* -- a literal string in
the chapter -- and the value the sources say it should hold. The script therefore fails loudly in
two situations, and both are wanted: the prose disagrees with results/, or the prose changed and
the claim no longer finds its anchor (update the script, do not delete the claim).

What this does NOT do: judge argument, tone, or whether a cited paper supports its sentence. It
hands those to the review agents as MANUAL items (the citation sheet, untraced numbers), so the
agents spend their attention where a script cannot reach.

Run from anywhere, in the pfe_swarm env (Ch4/Ch5 import eval/, which needs numpy and scipy):
    ~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch4.py
Writes .scratch/thesis-review/reports/<script>.md and prints the summary. Exit 1 on any FAIL.
"""

from __future__ import annotations

import csv
import re
from decimal import ROUND_HALF_UP, Decimal
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
THESIS = REPO / "thesis"
RESULTS = REPO / "results"
REPORTS = REPO / ".scratch" / "thesis-review" / "reports"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from check_tex import check as check_tex  # noqa: E402

# ---------------------------------------------------------------------------------------------
# Word lists, from .agents/skills/thesis-writing/SKILL.md §2. A hit is a WARN, not a FAIL: the
# skill forbids the unearned use, and whether a use is earned is the reviewer's judgement.
MARKETING = r"groundbreaking|revolutionary|game-changing|obviously|state-of-the-art|huge|seamless(?:ly)?"
#: SKILL §2 names these five; "never" is left out on purpose -- it is mostly ordinary English here.
ABSOLUTES = r"guarantee[sd]?|proves?|proven|ensures?|ensured|always|impossible|clearly"
#: "fixes" is left out: "Table 3 fixes every setting" is the right verb.
WEAK_VERBS = r"shows|gets|deals with|handles"
WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve "
                                     "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
WORDS |= {f"twenty-{w}": 20 + i for w, i in list(WORDS.items())[1:10]}
#: Artefacts of how the project was run. A thesis is read by someone who has never seen prd.md,
#: STATE.md or the sprint plan, so none of these may reach the prose (FAIL). Each has a thesis
#: equivalent: "the requirements of Section X", "a preliminary experiment", "reduced to 60".
INTERNAL = (r"\bprd(?:\.md|\.tex)?\b|\bPRD\b|project specification|hardware specification|STATE\.md|\bspike(?:-era)?\b|"
            r"\bS[0-9]\b|triag(?:e|ed|ing)|\bsprint\b|build schedule|this project executed|\bGate~?\s*\d|\bD[0-9]{1,2}\b|"
            r"\bsession~?\s*\d+|Table~?\s*3 of|escalation rule")
#: Short codes a reader must be given before they meet them. Defined = first cell of a table row,
#: inside \textbf{}, or followed at once by a parenthesis or colon that says what it is.
CODES = r"\b(?:Exp-\d|N?FR-\d+[a-z]?|RQ\d|C[1-4]\b|Surface~?\s?[AB]\b|Branch~?\s?[AB]\b)"
#: A heading is a noun phrase. These words make it read as a sentence or a claim.
HEADING_VERBS = (r"\b(?:is|are|was|were|has|have|had|belongs|eliminates|selects|misses|faced|travel|"
                 r"cannot|does|do|did)\b")
MARKERS = ("\\TODO", "\\CHECK", "\\figtodo")
DOC_NAMES = {"master": "M\\'emoire de Master", "ingenieur": "M\\'emoire d'Ing\\'enieur"}


# ---------------------------------------------------------------------------------------------
@dataclass
class Item:
    status: str          # FAIL | WARN | PASS | MANUAL
    check: str
    message: str
    line: int | None = None


@dataclass
class Chapter:
    doc: str             # "master" | "ingenieur"
    path: Path
    raw: str = ""
    lines: list[str] = field(default_factory=list)   # comment-stripped, 1-indexed via lines[i-1]

    @classmethod
    def load(cls, doc: str, rel: str) -> "Chapter":
        path = THESIS / rel
        raw = path.read_text(encoding="utf-8")
        return cls(doc, path, raw, [strip_comment(l) for l in raw.splitlines()])

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def line_of(self, offset: int) -> int:
        return self.text.count("\n", 0, offset) + 1

    def find(self, needle: str) -> list[int]:
        """Lines on which `needle` occurs, matched across line breaks (whitespace-insensitive)."""
        pattern = r"\s+".join(re.escape(part) for part in needle.split())
        return [self.line_of(m.start()) for m in re.finditer(pattern, self.text)]

    def prose(self) -> str:
        """Text with listings, texttt, labels, refs, cites and inputs removed -- what a reader reads."""
        t = re.sub(r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}", lambda m: "\n" * m.group().count("\n"),
                   self.text, flags=re.S)
        t = re.sub(r"\\(?:label|ref|cite|input|includegraphics|texttt)(?:\[[^\]]*\])?\{[^}]*\}",
                   lambda m: " " + "\n" * m.group().count("\n"), t)
        return t  # newline-preserving, so an offset in prose() maps to the same line as in text

    def sections(self) -> list[tuple[str, str, int]]:
        return [(m.group(1), m.group(2), self.line_of(m.start()))
                for m in re.finditer(r"\\((?:sub)?section|chapter|paragraph)\*?\{([^}]*)\}", self.text)]

    def inputs(self) -> list[Path]:
        return [THESIS / (m.group(1) + ("" if m.group(1).endswith(".tex") else ".tex"))
                for m in re.finditer(r"\\input\{([^}]*)\}", self.text)]


def _flex(s: str) -> str:
    """Regex for literal `s` with any whitespace run matching any whitespace run (line breaks)."""
    return "".join(r"\s+" if part.isspace() else re.escape(part) for part in re.split(r"(\s+)", s) if part)


def _line(s: str, offset: int) -> int:
    return s.count("\n", 0, offset) + 1


def strip_comment(line: str) -> str:
    m = re.search(r"(?<!\\)%", line)
    return line[: m.start()] if m else line


# ---------------------------------------------------------------------------------------------
# Numbers. `1{,}100` -> 1100; model names, requirement IDs and file stems are removed first so
# "Qwen2.5-0.5B" or "NFR-18" do not register as numbers the prose claims.
_IDENT = re.compile(r"(?<![\w\\])[A-Za-z][\w.\-\\]*?\d[\w\-\\]*(?:\.\d[\w\-\\]*)*")
#: No leading minus: in "0.36--1.2" the dash is a range, and prose writes negatives as $-$1.5.
_NUM = re.compile(r"(?<![\w.])\d{1,3}(?:\{,\}\d{3})+(?:\.\d+)?|(?<![\w.{])\d+(?:\.\d+)?")
_UNIT = re.compile(r"^\s*(?:~|\\,)?\s*(?:\\%|%|pp|ms|tok/s|GB|MB|GiB|dB|Hz|\\times|\$\\times|x\b|-?fold)")


@dataclass
class Num:
    text: str
    value: float
    places: int
    line: int
    unit: bool


def numbers(ch: Chapter) -> list[Num]:
    prose = ch.prose()
    out = []
    for lineno, line in enumerate(prose.split("\n"), 1):
        clean = _IDENT.sub(lambda m: " " * len(m.group()), line)
        for m in _NUM.finditer(clean):
            s = m.group().replace("{,}", "")
            places = len(s.split(".")[1]) if "." in s else 0
            out.append(Num(m.group(), float(s), places, lineno, bool(_UNIT.match(clean[m.end():]))))
    return out


def significant(n: Num) -> bool:
    """Worth tracing: has a decimal, is >= 100, or carries a unit. Small bare integers are counts
    and ordinals ("three models", "Chapter 4") that the index would match everywhere."""
    return n.places > 0 or abs(n.value) >= 100 or n.unit


def _source_files() -> list[tuple[Path, str]]:
    measured = [*RESULTS.glob("*.md"), *RESULTS.glob("*.json"), *(THESIS / "generated").glob("*.tex"),
                *(REPO / "spikes" / "reports").glob("*.md"), REPO / "train" / "kaggle_out" / "surface_a.csv"]
    measured += [p for p in RESULTS.glob("*.csv") if sum(1 for _ in p.open()) < 200]
    declared = [REPO / "prd.md", REPO / ".scratch" / "sprint-pfe" / "STATE.md", REPO / "data" / "dataset_card.md",
                *(REPO / "docs" / "adr").glob("*.md"), *(REPO / "train" / "configs").glob("*.yaml")]
    return [(p, "measured") for p in measured if p.is_file()] + [(p, "declared") for p in declared if p.is_file()]


_INDEX: list[tuple[float, str, str]] | None = None


def source_index() -> list[tuple[float, str, str]]:
    """(value, 'path:line', kind) for every number in the files a thesis number may come from."""
    global _INDEX
    if _INDEX is None:
        _INDEX = []
        for path, kind in _source_files():
            for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                for m in re.finditer(r"\d[\d,]*(?:\.\d+)?(?:e-?\d+)?", line):  # unsigned: "-25.1%" traces 25.1
                    try:
                        v = float(m.group().replace(",", ""))
                    except ValueError:
                        continue
                    _INDEX.append((v, f"{path.relative_to(REPO)}:{i}", kind))
    return _INDEX


def trace(n: Num) -> list[tuple[str, str, str]]:
    """Source locations whose value, rounded to the chapter's precision under one of the unit
    conversions a thesis applies (fraction->percent, MB->GB, ms->s), equals the written number."""
    hits = []
    for v, loc, kind in source_index():
        for conv, name in ((v, ""), (v * 100, "x100"), (v / 1024, "/1024"), (v / 1000, "/1000")):
            if round(conv, n.places) == round(n.value, n.places) and (conv != 0 or n.value == 0):
                hits.append((loc, kind, name))
                break
    # Unconverted hits before converted ones, measured before declared: the most direct source first.
    return sorted(hits, key=lambda h: (h[2] != "", h[1] != "measured"))


# ---------------------------------------------------------------------------------------------
# Bibliography, acronyms, prd.md
def bib() -> dict[str, dict[str, str]]:
    entries = {}
    text = (THESIS / "references.bib").read_text(encoding="utf-8")
    for m in re.finditer(r"@(\w+)\{([^,\s]+),(.*?)(?=\n@|\Z)", text, flags=re.S):
        fields, body = {"_type": m.group(1)}, m.group(3)
        for f in re.finditer(r"(\w+)\s*=\s*", body):
            i = f.end()
            if body[i:i + 1] == "{":           # brace-balanced value: titles nest {LLM} inside {...}
                depth, j = 0, i
                for j, ch in enumerate(body[i:], i):
                    depth += (ch == "{") - (ch == "}")
                    if depth == 0:
                        break
                value = body[i + 1:j]
            else:
                value = re.match(r'"[^"]*"|[^,\n]*', body[i:]).group().strip('"')
            fields.setdefault(f.group(1).lower(), re.sub(r"\s+", " ", value).replace("{", "").replace("}", "").strip())
        entries[m.group(2)] = fields
    return entries


def acronyms() -> dict[str, tuple[str, str]]:
    text = (THESIS / "shared" / "acronyms.tex").read_text(encoding="utf-8")
    return {k: (s, l) for k, s, l in re.findall(r"\\newacronym\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}", text)}


def prd() -> str:
    path = REPO / "prd.md"
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def prd_requirements() -> dict[str, list[str]]:
    """'NFR-9a' -> [requirement, target/verification, source] cells from prd Tables 11-12."""
    rows = {}
    for m in re.finditer(r"^\| \*\*((?:N?FR)-\w+)\*\* \|(.*)\|\s*$", prd(), flags=re.M):
        rows[m.group(1)] = [c.strip() for c in m.group(2).split("|")]
    return rows


def prd_rq(n: int) -> str:
    m = re.search(rf"\*\*RQ{n}: [^*]*\.\*\* (.*?) \$\\rightarrow\$", prd())
    return m.group(1).strip() if m else ""


def prd_outline(doc: str) -> list[str]:
    head = "Mémoire de Master" if doc == "master" else "Mémoire d'Ingénieur"
    m = re.search(rf"\*\*{head} — six chapters:\*\*\n((?:\d\..*\n)+)", prd())
    return [re.sub(r"^\d\.\s*", "", l) for l in m.group(1).strip().splitlines()] if m else []


def norm(s: str) -> str:
    """Compare prose across LaTeX and Markdown: drop markup, unify dashes and spacing."""
    s = re.sub(r"\\(?:texttt|emph|textbf)\{([^}]*)\}", r"\1", s)
    s = s.replace("~", " ").replace("{,}", ",").replace("\\_", "_").replace("$", "").replace("`", "")
    s = s.replace("\\leq", "≤").replace("\\geq", "≥").replace("--", "–").replace("*", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def md_table(path: Path, first_col: str | None = None) -> list[dict[str, str]]:
    """Rows of the first Markdown table in `path` (optionally the first whose header starts with
    `first_col`), header -> cell, with **bold** stripped."""
    rows, header = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            if header and rows:
                break
            continue
        cells = [c.strip().strip("*").strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            if first_col is None or cells[0].startswith(first_col):
                header = cells
        elif not set(line) <= set("|:- "):
            rows.append(dict(zip(header, cells)))
    return rows


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as h:
        return list(csv.DictReader(h))


# ---------------------------------------------------------------------------------------------
class Review:
    def __init__(self, name: str, doc: str, rel: str, siblings: list[str]):
        """`siblings`: the other chapter files of the same document, for cross-chapter \\ref."""
        self.name, self.ch = name, Chapter.load(doc, rel)
        self.siblings = [Chapter.load(doc, s) for s in siblings if (THESIS / s).is_file()]
        self.items: list[Item] = []
        self.manual: list[str] = []

    # -- recording ----------------------------------------------------------------------------
    def add(self, status: str, check: str, message: str, line: int | None = None) -> None:
        self.items.append(Item(status, check, message, line))

    def expect(self, check: str, ok: bool, message: str, line: int | None = None, warn: bool = False) -> None:
        self.add("PASS" if ok else ("WARN" if warn else "FAIL"), check, message, line)

    def number(self, anchor: str, computed: float, source: str, places: int | None = None,
               tol: float | None = None, note: str = "", nth: int = 0) -> None:
        """The `nth` number in `anchor` must equal `computed`, rounded half-up to the precision the
        chapter writes it at (or within `tol`).

        The anchor locates the sentence by the words AROUND the number, and the number itself is
        read from the chapter. So when the chapter's number changes, the check reports the new
        value against the source -- it does not report "anchor not found", which would invite
        someone to copy the wrong number into this script to make it pass."""
        masked = _IDENT.sub(lambda x: " " * len(x.group()), anchor)
        alts = "|".join(sorted(WORDS, key=len, reverse=True))  # "twenty-one" before "twenty"
        tokens = [(m.start(), m.end(), "num") for m in _NUM.finditer(masked)]
        tokens += [(m.start(), m.end(), "word") for m in re.finditer(rf"\b(?:{alts})\b", anchor.lower())]
        tokens.sort()
        if len(tokens) <= nth:
            self.add("FAIL", "claim", f"anchor `{anchor}` has no number #{nth} -- fix the script")
            return
        a, b, kind = tokens[nth]
        capture = (r"(\d{1,3}(?:\{,\}\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)" if kind == "num"
                   else rf"((?i:{alts}))")
        # The exact anchor first: the normal case, and unambiguous by construction of the claims.
        # Only if it is gone -- the number changed -- search by context, which must then be unique.
        pattern = _flex(anchor[:a]) + capture + _flex(anchor[b:])
        m = re.search(_flex(anchor[:a]) + "(" + re.escape(anchor[a:b]) + ")" + _flex(anchor[b:]), self.ch.text)
        if not m:
            hits = list(re.finditer(pattern, self.ch.text))
            if len(hits) != 1:
                self.add("FAIL", "claim", f"`{anchor}` not found as written"
                         + (f"; by context it matches {len(hits)} places (lines "
                            f"{', '.join(str(self.ch.line_of(h.start())) for h in hits)}) -- lengthen the anchor"
                            if hits else " nor by context -- prose changed; re-anchor the claim, do not change "
                            "the expected value"))
                return
            m = hits[0]
        g = m.group(1)
        written_s = g.replace("{,}", "") if kind == "num" else str(WORDS[g.lower()])
        written = float(written_s)
        p = places if places is not None else (len(written_s.split(".")[1]) if "." in written_s else 0)
        # Half-up, the rounding a reader assumes: 785.5 must be written 786. round() is half-to-even.
        ok = (abs(written - computed) <= tol if tol is not None
              else Decimal(repr(computed)).quantize(Decimal(1).scaleb(-p), rounding=ROUND_HALF_UP) == Decimal(written_s))
        shown = re.sub(r"\s+", " ", m.group())
        msg = f"`{shown}` -> written {written_s}, source gives {computed:.{max(p, 2)}f} ({source})"
        self.add("PASS" if ok else "FAIL", "claim", msg + (f" -- {note}" if note else ""), self.ch.line_of(m.start(1)))

    def text_claim(self, check: str, anchor: str, ok: bool, message: str, warn: bool = False) -> None:
        where = self.ch.find(anchor)
        if not where:
            self.add("FAIL", check, f"anchor not found -- prose changed, update the script: `{anchor}`")
        else:
            self.expect(check, ok, message, where[0], warn=warn)

    # -- common checks ------------------------------------------------------------------------
    def common(self) -> None:
        self._check_tex()
        self._refs()
        self._markers()
        self._citations()
        self._hardcoded_numbers()
        self._tilde()
        self._words()
        self._companion()
        self._acronyms()
        self._floats()
        self._paths()
        self._sections()
        self._internal()
        self._codes()
        self._headings()

    def _check_tex(self) -> None:
        problems, notes, _ = check_tex(self.ch.raw, self.ch.path, xelatex=False)
        own = [p for p in problems if "has no matching \\label" not in p]
        for p in own:
            self.add("FAIL", "check_tex", p)
        if not own:
            self.add("PASS", "check_tex", "tools/check_tex.py: no problems beyond cross-chapter \\ref (resolved below)")

    def _refs(self) -> None:
        labels = set()
        for c in [self.ch, *self.siblings]:
            for src in [c.text, *[p.read_text(encoding="utf-8") for p in c.inputs() if p.is_file()]]:
                labels |= set(re.findall(r"\\label\{([^}]*)\}", src))
        bad, pending = 0, {}
        for m in re.finditer(r"\\ref\{([^}]*)\}", self.ch.text):
            key, line = m.group(1), self.ch.line_of(m.start())
            if key in labels:
                continue
            bad += 1
            if key.startswith("chap:"):
                pending.setdefault(key, []).append(line)
            else:
                self.add("FAIL", "ref", f"\\ref{{{key}}} resolves nowhere in this document", line)
        for key, lines in pending.items():
            self.add("WARN", "ref", f"\\ref{{{key}}} x{len(lines)} (lines {', '.join(map(str, lines))}) -- chapter not "
                     "written yet; its file must carry exactly this label", lines[0])
        if not bad:
            self.add("PASS", "ref", "every \\ref resolves within the document")

    def _markers(self) -> None:
        for i, line in enumerate(self.ch.lines, 1):
            for mk in MARKERS:
                if mk + "{" in line:
                    self.add("WARN", "marker", f"{mk} left in text: {line.strip()[:110]}", i)

    def _citations(self) -> None:
        entries = bib()
        text = self.ch.text
        seen: dict[str, int] = {}
        sheet = ["| # | line | keys | sentence the citation must support |", "|---|---|---|---|"]
        for n, m in enumerate(re.finditer(r"\\cite(?:\[[^\]]*\])?\{([^}]*)\}", text), 1):
            keys = [k.strip() for k in m.group(1).split(",")]
            line = self.ch.line_of(m.start())
            start = max(text.rfind(". ", 0, m.start()), text.rfind("\n\n", 0, m.start())) + 1
            end_m = re.search(r"\.(\s|$)", text[m.end():])
            end = m.end() + (end_m.end() if end_m else 200)
            sentence = re.sub(r"\s+", " ", text[start:end]).strip()[:320]
            sheet.append(f"| {n} | {line} | {', '.join(keys)} | {sentence.replace('|', '/')} |")
            for k in keys:
                seen.setdefault(k, line)
                if k not in entries:
                    self.add("FAIL", "cite", f"\\cite{{{k}}} is not in references.bib", line)
        for k, line in seen.items():
            e = entries.get(k)
            if e and not any(e.get(f) for f in ("doi", "eprint", "url")):
                self.add("FAIL", "bib", f"{k}: no doi, eprint or url -- unverifiable (bib house rules)", line)
        if seen:
            keys = ["| key | title | year | identifier |", "|---|---|---|---|"]
            for k in seen:
                e = entries.get(k, {})
                ident = e.get("doi") and f"doi:{e['doi']}" or e.get("eprint") and f"arXiv:{e['eprint']}" or e.get("url", "--")
                keys.append(f"| {k} | {e.get('title', '?')[:90]} | {e.get('year', '?')} | {ident} |")
            self.manual.append("### Citation sheet (for the citation agent: open each identifier, "
                               "judge SUPPORTS / PARTIAL / DOES NOT SUPPORT per row)\n\n"
                               + "\n".join(sheet) + "\n\n" + "\n".join(keys))
        if all(k in entries for k in seen):
            self.add("PASS", "cite", f"{len(seen)} distinct keys cited, all resolved" if seen else "no citations")

    def _hardcoded_numbers(self) -> None:
        prose = self.ch.prose()
        for m in re.finditer(r"\b(Table|Figure|Section|Chapter|Equation)s?(?:~|\s+)(\d+(?:\.\d+)*)\b", prose):
            self.add("WARN", "hardcoded-ref",
                     f"`{m.group()}` typed by hand -- use \\ref within this document; across documents the "
                     "number goes stale (SKILL §4.1)", _line(prose, m.start()))

    def _tilde(self) -> None:
        for m in re.finditer(r"(\w)[ \t]+\\(cite|ref)\{", self.ch.text):
            self.add("WARN", "tilde", f"breakable space before \\{m.group(2)} -- use ~", self.ch.line_of(m.start()))
        for m in re.finditer(r"\b(Table|Figure|Section|Chapter)s?\\ref", self.ch.text):
            self.add("WARN", "tilde", f"`{m.group()}` has no space at all -- use ~", self.ch.line_of(m.start()))

    def _words(self) -> None:
        prose = re.sub(r"\\chapter\{[^}]*\}", "", self.ch.prose())
        for label, pattern in (("marketing", MARKETING), ("absolute", ABSOLUTES), ("weak-verb", WEAK_VERBS)):
            for m in re.finditer(rf"\b(?:{pattern})\b", prose, flags=re.I):
                off = m.start()
                ctx = re.sub(r"\s+", " ", prose[max(0, off - 60): off + 60]).strip()
                self.add("WARN", label, f"`{m.group()}` -- earned? ...{ctx}...", _line(prose, off))

    def _companion(self) -> None:
        other = DOC_NAMES["ingenieur" if self.ch.doc == "master" else "master"]
        for m in re.finditer(r"companion\s+(report|document|thesis|volume|work)", self.ch.text, flags=re.I):
            self.add("FAIL", "cross-doc", f"`{m.group()}` -- name it \\emph{{{other}}} (SKILL §4.1)",
                     self.ch.line_of(m.start()))
        for m in re.finditer(r"M\\'emoire (?:de Master|d'Ing\\'enieur)\}?'?s?\s*\S*\s*Chapter~?\s*\d", self.ch.text):
            self.add("WARN", "cross-doc", f"other document's chapter number hardcoded: `{m.group()}`",
                     self.ch.line_of(m.start()))

    def _acronyms(self) -> None:
        acr = acronyms()
        prose = self.ch.prose()
        for key, (short, long) in acr.items():
            hits = [_line(prose, m.start()) for m in re.finditer(rf"(?<![\w{{\\]){re.escape(short)}s?(?![\w}}]|-\d)", prose)]
            if hits:
                self.add("WARN", "acronym", f"`{short}` typed by hand {len(hits)}x (lines {', '.join(map(str, hits[:8]))}"
                         f"{', ...' if len(hits) > 8 else ''}) -- \\gls{{{key}}} (the first \\gls expands itself)", hits[0])
            if re.search(re.escape(long.split(" (")[0]), prose, flags=re.I):
                line = _line(prose, re.search(re.escape(long.split(" (")[0]), prose, flags=re.I).start())
                self.add("WARN", "acronym", f"long form `{long.split(' (')[0]}` spelled out -- \\gls{{{key}}}?", line)

        # \acrfull prints the long form without marking the entry used, so the next \gls expands it again.
        for m in re.finditer(r"\\(?:acrfull|acrfullpl|Acrfull|Acrfullpl)\{([^}]*)\}", self.ch.text):
            self.add("FAIL", "acronym", f"`\\acrfull{{{m.group(1)}}}` -- write \\gls{{{m.group(1)}}}: \\acrfull does not mark "
                     "the entry used, so the next \\gls prints the long form a second time", self.ch.line_of(m.start()))

    def _floats(self) -> None:
        sources = [(self.ch.text, None)] + [(p.read_text(encoding="utf-8"), p) for p in self.ch.inputs() if p.is_file()]
        for src, path in sources:
            for m in re.finditer(r"\\label\{((?:fig|tab):[^}]*)\}", src):
                key = m.group(1)
                if path is None:
                    float_line = self.ch.line_of(m.start())
                else:
                    float_line = next((i for i, l in enumerate(self.ch.lines, 1)
                                       if f"\\input{{{path.relative_to(THESIS).with_suffix('')}}}" in l), 0)
                refs = [self.ch.line_of(r.start()) for r in re.finditer(rf"\\ref\{{{re.escape(key)}\}}", self.ch.text)]
                if not refs:
                    self.add("FAIL", "float", f"{key} is never \\ref'd in this chapter", float_line)
                elif min(refs) > float_line:
                    self.add("WARN", "float", f"{key} first \\ref'd on line {min(refs)}, after the float (line {float_line})",
                             float_line)
                else:
                    self.add("PASS", "float", f"{key} referenced before it appears (line {min(refs)})", float_line)
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", self.ch.text):
            f = (THESIS / m.group(1)).resolve()
            line = self.ch.line_of(m.start())
            self.expect("figure", f.suffix.lower() in (".pdf", ".svg", ".eps"), f"{m.group(1)} is vector", line)
            self.expect("figure", f.is_file(), f"{m.group(1)} exists", line)

    def _paths(self) -> None:
        for m in re.finditer(r"\\texttt\{([^}]*)\}", self.ch.text):
            s = m.group(1).replace("\\_", "_")
            if not re.search(r"/|\.(?:py|csv|gbnf|md|json|yaml|jsonl)$", s) or " " in s:
                continue
            found = (REPO / s).exists() or any(REPO.glob(f"**/{Path(s).name}"))
            self.expect("path", found, f"`{s}` exists in the repo", self.ch.line_of(m.start()), warn=True)

    def _sections(self) -> None:
        secs = [x for x in self.ch.sections() if x[0] != "paragraph"]  # lead-ins are not sections
        out = ["| line | level | title | prose words |", "|---|---|---|---|"]
        bounds = [s[2] for s in secs] + [len(self.ch.lines) + 1]
        for (level, title, line), end in zip(secs, bounds[1:]):
            body = "\n".join(self.ch.lines[line: end - 1])
            body = re.sub(r"\\TODO\{[^}]*\}|\\label\{[^}]*\}", "", body)
            words = len(re.findall(r"[A-Za-z]{2,}", body))
            out.append(f"| {line} | {level} | {title} | {words} |")
            if level != "chapter" and words < 15 and not any(s[2] > line and s[2] < end for s in secs):
                self.add("WARN", "section", f"`{title}` has no prose yet", line)
        self.manual.append("### Section map\n\n" + "\n".join(out))

    def _internal(self) -> None:
        prose = self.ch.prose()
        for m in re.finditer(INTERNAL, prose):
            ctx = re.sub(r"\s+", " ", prose[max(0, m.start() - 50): m.end() + 50]).strip()
            self.add("FAIL", "internal", f"`{m.group()}` -- project-internal; the reader has no such document. "
                     f"...{ctx}...", _line(prose, m.start()))

    def _document(self) -> list[Chapter]:
        """This document's chapters, in reading order, that exist on disk."""
        names = MASTER if self.ch.doc == "master" else INGENIEUR
        by_path = {c.path: c for c in [self.ch, *self.siblings]}
        return [by_path[THESIS / n] for n in names if THESIS / n in by_path]

    def _codes(self) -> None:
        """Every code used here must be defined somewhere in this document, before its first use."""
        def key(code: str) -> str:
            return re.sub(r"~|\s", " ", code)

        defined: dict[str, tuple[int, int]] = {}
        first_use: dict[str, tuple[int, int]] = {}
        for idx, c in enumerate(self._document()):
            txt = c.text
            for m in re.finditer(CODES, txt):
                k, pos = key(m.group()), (idx, c.line_of(m.start()))
                first_use.setdefault(k, pos)
                line_start = txt.rfind("\n", 0, m.start()) + 1
                is_def = (txt[line_start:m.start()].strip() == "" and txt[m.end():m.end() + 3].strip().startswith("&")) \
                    or txt[max(0, m.start() - 8):m.start()].endswith("\\textbf{") \
                    or re.match(r"\s*(?:\(|:|---)", txt[m.end():m.end() + 5]) is not None
                if is_def:
                    defined.setdefault(k, pos)
        me = self._document().index(self.ch)
        names = [c.path.stem for c in self._document()]
        used_here: dict[str, list[int]] = {}
        for m in re.finditer(CODES, self.ch.prose()):
            used_here.setdefault(key(m.group()), []).append(_line(self.ch.prose(), m.start()))
        for k, lines in sorted(used_here.items()):
            where = f"{len(lines)}x (lines {', '.join(map(str, lines[:6]))}{', ...' if len(lines) > 6 else ''})"
            if k not in defined:
                self.add("FAIL", "code", f"`{k}` used {where} but never defined in this document -- define it once, "
                         "before this first use (table row, bold term, or a parenthesis), or replace it with a "
                         "descriptive name. A definition in a chapter not yet written still comes too late",
                         lines[0])
            elif defined[k] > (me, lines[0]) and first_use[k] < defined[k]:
                d = defined[k]
                self.add("WARN", "code", f"`{k}` used {where} before its definition in {names[d[0]]} l.{d[1]}",
                         lines[0])
        if used_here:
            self.manual.append("### Codes used in this chapter (self-containment agent: is each one needed, or "
                               "would a descriptive name read better?)\n\n| code | uses | defined at |\n|---|---|---|\n"
                               + "\n".join(f"| {k} | {len(v)} | "
                                           + (f"{names[defined[k][0]]} l.{defined[k][1]}" if k in defined else "**nowhere**")
                                           + " |" for k, v in sorted(used_here.items())))

    def _headings(self) -> None:
        for level, title, line in self.ch.sections():
            t = title.strip().rstrip(".")
            problems = []
            if re.search(CODES, t):
                problems.append("contains a code")
            if re.search(r"\d", _IDENT.sub("", re.sub(CODES, "", t))) and level != "chapter":
                problems.append("contains a number")
            if t.endswith("?"):
                problems.append("is a question")
            if re.search(HEADING_VERBS, t, flags=re.I):
                problems.append("reads as a sentence or a claim, not a noun phrase")
            if len(t.split()) > (7 if level == "paragraph" else 9):
                problems.append(f"{len(t.split())} words long")
            if problems:
                self.add("WARN", "heading", f"{level} `{title}` {', '.join(problems)}", line)
        # One capitalisation convention for chapter titles across the document.
        def style(t: str) -> str:
            words = [w for w in re.findall(r"[A-Za-z][\w'-]*", t)[1:] if w.lower() not in
                     {"and", "of", "the", "a", "an", "in", "on", "for", "to", "or", "with"}]
            return "title" if words and all(w[0].isupper() for w in words) else "sentence" if words else "one-word"
        titles = [(c.path.stem, t) for c in self._document() for lvl, t, _ in c.sections() if lvl == "chapter"]
        styles = {style(t) for _, t in titles} - {"one-word"}
        self.expect("heading", len(styles) <= 1, f"chapter titles use one capitalisation style: {titles}"
                    if len(styles) <= 1 else f"chapter titles mix title case and sentence case: "
                    + "; ".join(f"{n}: `{t}`" for n, t in titles if style(t) != "one-word"), warn=True)

    def _numbers(self) -> None:
        rows = ["| line | as written | trace |", "|---|---|---|"]
        claimed = {i.line for i in self.items if i.check == "claim" and i.status == "PASS"}
        untraced = 0
        for n in numbers(self.ch):
            if not significant(n):
                continue
            if n.line in claimed:
                rows.append(f"| {n.line} | {n.text} | recomputed by a claim on this line |")
                continue
            hits = trace(n)
            measured = [h for h in hits if h[1] == "measured"]
            if measured:
                tag = "measured: " + ", ".join(f"{loc}{' ' + c if c else ''}" for loc, _, c in measured[:2])
            elif hits:
                tag = "DECLARED ONLY: " + ", ".join(loc for loc, _, _ in hits[:2])
            else:
                tag, untraced = "**UNTRACED**", untraced + 1
            rows.append(f"| {n.line} | {n.text} | {tag} |")
        self.manual.append("### Number trace (a hit means the value exists in a source, not that it is the "
                           "right source -- the claims above are the strong checks)\n\n" + "\n".join(rows))
        self.add("WARN" if untraced else "PASS", "numbers",
                 f"{untraced} significant number(s) found in no source file -- see the number trace")

    # -- output -------------------------------------------------------------------------------
    def finish(self) -> int:
        self._numbers()  # last, so numbers already recomputed by a claim are not re-traced
        order = {"FAIL": 0, "WARN": 1, "PASS": 2}
        items = sorted(self.items, key=lambda i: (order[i.status], i.line or 0))
        count = {s: sum(1 for i in items if i.status == s) for s in order}
        rel = self.ch.path.relative_to(REPO)
        head = [f"# Pre-review report: {rel}", "",
                f"Generated by `tools/review/{self.name}.py`. {count['FAIL']} FAIL, {count['WARN']} WARN, "
                f"{count['PASS']} PASS.", "",
                "FAIL = the chapter disagrees with its sources or will break the build. WARN = a human or "
                "agent must judge it. The review agents take this whole file as input.", ""]
        body = ["| status | check | line | finding |", "|---|---|---|---|"]
        body += [f"| {i.status} | {i.check} | {i.line or ''} | {i.message.replace('|', '/')} |" for i in items]
        report = "\n".join(head + body + [""] + [m + "\n" for m in self.manual])
        REPORTS.mkdir(parents=True, exist_ok=True)
        out = REPORTS / f"{self.name}.md"
        out.write_text(report, encoding="utf-8")
        print(f"{rel}: {count['FAIL']} FAIL, {count['WARN']} WARN, {count['PASS']} PASS -> {out.relative_to(REPO) if out.is_relative_to(REPO) else out}")
        for i in items:
            if i.status == "FAIL":
                print(f"  FAIL {i.check:<12} {('l.' + str(i.line)) if i.line else '':<6} {i.message}")
        return 1 if count["FAIL"] else 0


MASTER = [f"master/{c}.tex" for c in ("ch1_introduction", "ch2_related_work", "ch3_method",
                                       "ch4_results", "ch5_discussion", "ch6_conclusion")]
INGENIEUR = [f"ingenieur/{c}.tex" for c in ("ch1_introduction", "ch2_state_of_the_art", "ch3_architecture",
                                             "ch4_implementation", "ch5_validation", "ch6_conclusion")]


def outline_check(r: Review, index: int, topics: dict[str, str]) -> None:
    """Every topic prd.md §3.1 lists for this chapter must head a \\section. `topics` maps a
    prd phrase to a regex over section titles."""
    outline = prd_outline(r.ch.doc)
    if not outline:
        r.add("WARN", "outline", "prd.md not found or §3.1 not parsed -- outline unchecked")
        return
    r.add("PASS", "outline", f"prd.md §3.1 item {index + 1}: {outline[index]}")
    titles = [t for lvl, t, _ in r.ch.sections() if lvl == "section"]
    for phrase, pattern in topics.items():
        hit = next((t for t in titles if re.search(pattern, t, flags=re.I)), None)
        r.expect("outline", hit is not None, f"prd topic `{phrase}` -> section `{hit}`" if hit
                 else f"prd topic `{phrase}` has no section")


def rq_check(r: Review, n: int) -> None:
    m = re.search(rf"\\textbf\{{RQ{n}[^}}]*\}}\s*(.*?)\\end\{{quote\}}", r.ch.text, flags=re.S)
    want = prd_rq(n)
    if not m or not want:
        r.add("FAIL", "rq", f"RQ{n} quote block not found" if not m else "prd.md RQ text not parsed")
        return
    r.expect("rq", norm(m.group(1)) == norm(want), f"RQ{n} matches prd.md §2 verbatim" if norm(m.group(1)) == norm(want)
             else f"RQ{n} differs from prd.md §2.\n chapter: {norm(m.group(1))}\n prd:     {norm(want)}",
             r.ch.line_of(m.start()))


def requirement_table_check(r: Review, label: str, target_col: int, source_col: int | None,
                            strict: bool = True) -> None:
    """`strict=False` for FR tables, whose second column is a verification method the chapter may
    reword freely; NFR targets are numbers and must match."""
    """Rows of the chapter's requirement table against prd Tables 11-12, cell by cell."""
    m = re.search(rf"\\label\{{{label}\}}(.*?)\\end\{{tabularx\}}", r.ch.text, flags=re.S)
    if not m:
        r.add("FAIL", "requirements", f"table {label} not found")
        return
    reqs = prd_requirements()
    wording = ["| line | id | chapter wording | prd wording |", "|---|---|---|---|"]
    for row in re.findall(r"^((?:N?FR)-\w+) & (.*?)\\\\\s*$", m.group(1), flags=re.M):
        rid, cells = row[0], [c.strip() for c in row[1].split(" & ")]
        line = r.ch.find(f"{rid} &")[0]
        want = reqs.get(rid)
        if not want:
            r.add("FAIL", "requirements", f"{rid} is not a requirement in prd.md", line)
            continue
        # Targets are compared on substance -- the numbers and the direction of the bound -- since
        # the chapter legitimately rewords "100% *by construction* -- reported as ..." to fit a cell.
        def gist(s: str) -> tuple:
            s = norm(s)
            return (sorted(re.findall(r"\d+(?:[.,]\d+)?", s)), "≤" in s, "≥" in s)
        ok = gist(cells[target_col - 1]) == gist(want[1])
        r.expect("requirements", ok, f"{rid} target `{cells[target_col - 1]}` vs prd `{want[1]}`", line, warn=not strict)
        if source_col is not None:
            src_ok = norm(cells[source_col - 1]) == norm(want[2])
            r.expect("requirements", src_ok, f"{rid} source `{cells[source_col - 1]}` vs prd `{want[2]}`", line, warn=True)
        wording.append(f"| {line} | {rid} | {cells[0][:90]} | {want[0][:90]} |")
    r.manual.append(f"### Requirement wording, {label} vs prd.md (argument agent: a paraphrase may not change the "
                    "requirement's scope)\n\n" + "\n".join(wording))


def main_order(doc: str) -> list[str]:
    """Chapter labels in the order main_*.tex inputs them (commented-out chapters included)."""
    text = (THESIS / f"main_{doc}.tex").read_text(encoding="utf-8")
    return re.findall(rf"\\input\{{{doc}/(ch\d_\w+)\}}", text)
