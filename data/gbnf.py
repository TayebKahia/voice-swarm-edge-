"""A GBNF interpreter, so Layer 1 can be *executed* rather than restated.

Session 02A's gate is FR-1: **every generated label is accepted by
`schema/cmd.gbnf`**. Checking that needs an acceptor for the grammar. There are
only three ways to get one, and two of them are wrong:

1. Re-express the grammar as a regex in `data/`. This is the trap `README.md:56`
   names --- duplicating any part of `schema/` elsewhere "produces a silent
   accuracy collapse with no error message". The copy drifts, the gate keeps
   passing, and nobody finds out until Exp-1.
2. Import the regex mirror that already lives in `schema/test_grammar.py`. That
   mirror is a *test fixture* for Layer 1, deliberately hand-written to be an
   independent check of the same spec. Using it as the generator's acceptor
   collapses the two into one, and a shared mistake becomes invisible.
3. **Parse `schema/cmd.gbnf` itself and match against it.** No second statement
   of the grammar exists, so there is nothing to drift. This module.

`schema/` is frozen, so this lives in `data/`. It reads the frozen file; it does
not know anything about commands.

The supported subset is exactly what `cmd.gbnf` uses: rule definitions,
alternation, concatenation, grouping, string literals, character classes, and
the postfix repetitions `?`, `*`, `+`, plus `{m,n}` (unused by v1.0, but the
S3 spike recommends `idlist ::= [0-4] ( "," [0-4] ){0,4}` for a future v1.1, and
an acceptor that cannot read the amendment would be useless the day it lands).

Where `llama.cpp` is built, `data/check_grammar.py` cross-checks this
interpreter against `llama-gbnf-validator` --- the real decoder-side parser ---
so the gate rests on the shipping implementation and not only on this one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "GrammarError",
    "Grammar",
    "load_grammar",
]


class GrammarError(ValueError):
    """The grammar text is malformed, or uses a construct outside the subset."""


# --- syntax tree -----------------------------------------------------------


@dataclass(frozen=True)
class _Lit:
    text: str


@dataclass(frozen=True)
class _Ref:
    name: str


@dataclass(frozen=True)
class _Class:
    ranges: tuple[tuple[str, str], ...]
    negated: bool


@dataclass(frozen=True)
class _Seq:
    items: tuple[object, ...]


@dataclass(frozen=True)
class _Alt:
    options: tuple[object, ...]


@dataclass(frozen=True)
class _Rep:
    node: object
    low: int
    high: int | None  # None = unbounded


# --- lexer -----------------------------------------------------------------

_COMMENT = re.compile(r"#[^\n]*")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")
_REPEAT = re.compile(r"\{\s*(\d+)\s*(?:,\s*(\d*)\s*)?\}")

_ESCAPES = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    '"': '"',
    "'": "'",
    "\\": "\\",
    "[": "[",
    "]": "]",
}


def _read_escape(text: str, i: int) -> tuple[str, int]:
    """Decode one backslash escape starting at `text[i] == '\\'`."""
    if i + 1 >= len(text):
        raise GrammarError("grammar ends inside an escape sequence")
    code = text[i + 1]
    if code == "x":
        hex_digits = text[i + 2 : i + 4]
        if len(hex_digits) != 2:
            raise GrammarError(f"truncated \\x escape at offset {i}")
        return chr(int(hex_digits, 16)), i + 4
    if code == "u":
        hex_digits = text[i + 2 : i + 6]
        if len(hex_digits) != 4:
            raise GrammarError(f"truncated \\u escape at offset {i}")
        return chr(int(hex_digits, 16)), i + 6
    if code in _ESCAPES:
        return _ESCAPES[code], i + 2
    raise GrammarError(f"unsupported escape \\{code} at offset {i}")


def _read_literal(text: str, i: int) -> tuple[_Lit, int]:
    """Read a double-quoted literal. `i` points at the opening quote."""
    out: list[str] = []
    i += 1
    while True:
        if i >= len(text):
            raise GrammarError("unterminated string literal")
        ch = text[i]
        if ch == '"':
            return _Lit("".join(out)), i + 1
        if ch == "\\":
            decoded, i = _read_escape(text, i)
            out.append(decoded)
            continue
        out.append(ch)
        i += 1


def _read_class(text: str, i: int) -> tuple[_Class, int]:
    """Read a `[...]` character class. `i` points at the opening bracket."""
    i += 1
    negated = False
    if i < len(text) and text[i] == "^":
        negated = True
        i += 1
    ranges: list[tuple[str, str]] = []
    first = True
    while True:
        if i >= len(text):
            raise GrammarError("unterminated character class")
        ch = text[i]
        if ch == "]" and not first:
            return _Class(tuple(ranges), negated), i + 1
        first = False
        if ch == "\\":
            low, i = _read_escape(text, i)
        else:
            low = ch
            i += 1
        # A `-` that is not the last character opens a range.
        if i < len(text) and text[i] == "-" and i + 1 < len(text) and text[i + 1] != "]":
            i += 1
            if text[i] == "\\":
                high, i = _read_escape(text, i)
            else:
                high = text[i]
                i += 1
            ranges.append((low, high))
        else:
            ranges.append((low, low))


# --- parser ----------------------------------------------------------------


def _split_rules(source: str) -> list[tuple[str, str]]:
    """Split grammar text into `(name, body)` pairs.

    A line without `::=` continues the previous rule, so both the single-line
    layout `cmd.gbnf` uses today and a future wrapped layout parse the same.
    (Spike S3 found that `llama.cpp` itself rejects wrapped productions whose
    continuation lacks a leading operator; this reader is the more permissive
    of the two on purpose, and the cross-check in `check_grammar.py` is what
    catches anything `llama.cpp` would refuse.)
    """
    rules: list[tuple[str, list[str]]] = []
    for raw_line in source.splitlines():
        line = _COMMENT.sub("", raw_line).strip()
        if not line:
            continue
        if "::=" in line:
            name, _, body = line.partition("::=")
            name = name.strip()
            if not _IDENT.fullmatch(name):
                raise GrammarError(f"invalid rule name {name!r}")
            rules.append((name, [body.strip()]))
        else:
            if not rules:
                raise GrammarError(f"continuation line before any rule: {line!r}")
            rules[-1][1].append(line)
    return [(name, " ".join(parts)) for name, parts in rules]


class _BodyParser:
    """Recursive-descent parser for a single rule body."""

    def __init__(self, body: str, rule_name: str) -> None:
        self.body = body
        self.rule_name = rule_name
        self.i = 0

    def _skip_ws(self) -> None:
        while self.i < len(self.body) and self.body[self.i].isspace():
            self.i += 1

    def parse(self) -> object:
        node = self._alternation()
        self._skip_ws()
        if self.i != len(self.body):
            raise GrammarError(
                f"rule {self.rule_name!r}: unexpected {self.body[self.i]!r} "
                f"at offset {self.i} of {self.body!r}"
            )
        return node

    def _alternation(self) -> object:
        options = [self._sequence()]
        while True:
            self._skip_ws()
            if self.i < len(self.body) and self.body[self.i] == "|":
                self.i += 1
                options.append(self._sequence())
            else:
                break
        return options[0] if len(options) == 1 else _Alt(tuple(options))

    def _sequence(self) -> object:
        items: list[object] = []
        while True:
            self._skip_ws()
            if self.i >= len(self.body) or self.body[self.i] in "|)":
                break
            items.append(self._repetition())
        if not items:
            raise GrammarError(f"rule {self.rule_name!r}: empty alternative in {self.body!r}")
        return items[0] if len(items) == 1 else _Seq(tuple(items))

    def _repetition(self) -> object:
        node = self._atom()
        while True:
            self._skip_ws()
            if self.i >= len(self.body):
                return node
            ch = self.body[self.i]
            if ch == "?":
                self.i += 1
                node = _Rep(node, 0, 1)
            elif ch == "*":
                self.i += 1
                node = _Rep(node, 0, None)
            elif ch == "+":
                self.i += 1
                node = _Rep(node, 1, None)
            elif ch == "{":
                match = _REPEAT.match(self.body, self.i)
                if match is None:
                    raise GrammarError(
                        f"rule {self.rule_name!r}: malformed repetition at offset {self.i}"
                    )
                low = int(match.group(1))
                raw_high = match.group(2)
                if raw_high is None:
                    high: int | None = low
                elif raw_high == "":
                    high = None
                else:
                    high = int(raw_high)
                self.i = match.end()
                node = _Rep(node, low, high)
            else:
                return node

    def _atom(self) -> object:
        self._skip_ws()
        if self.i >= len(self.body):
            raise GrammarError(f"rule {self.rule_name!r}: expression ends early")
        ch = self.body[self.i]
        if ch == '"':
            node, self.i = _read_literal(self.body, self.i)
            return node
        if ch == "[":
            node, self.i = _read_class(self.body, self.i)
            return node
        if ch == "(":
            self.i += 1
            inner = self._alternation()
            self._skip_ws()
            if self.i >= len(self.body) or self.body[self.i] != ")":
                raise GrammarError(f"rule {self.rule_name!r}: unclosed group")
            self.i += 1
            return inner
        match = _IDENT.match(self.body, self.i)
        if match is None:
            raise GrammarError(
                f"rule {self.rule_name!r}: unexpected {ch!r} at offset {self.i}"
            )
        self.i = match.end()
        return _Ref(match.group(0))


# --- matcher ---------------------------------------------------------------


class Grammar:
    """A parsed GBNF grammar that can accept or reject a whole string.

    `accepts()` is exact: it computes the set of positions the root rule can
    reach from offset 0 and asks whether the end of the string is among them.
    Matching a *complete* string is what the gate needs --- a prefix match would
    pass a truncated label, which is precisely the failure mode spike S3 saw on
    hardware when an unbounded `idlist` ran past `-n`.
    """

    def __init__(self, rules: dict[str, object], root: str = "root") -> None:
        if root not in rules:
            raise GrammarError(f"grammar has no {root!r} rule")
        self.rules = rules
        self.root = root
        missing = {
            ref
            for node in rules.values()
            for ref in _referenced(node)
            if ref not in rules
        }
        if missing:
            raise GrammarError(f"undefined rules referenced: {sorted(missing)}")

    @classmethod
    def parse(cls, source: str, root: str = "root") -> Grammar:
        rules: dict[str, object] = {}
        for name, body in _split_rules(source):
            if name in rules:
                raise GrammarError(f"rule {name!r} defined twice")
            rules[name] = _BodyParser(body, name).parse()
        return cls(rules, root)

    @classmethod
    def from_file(cls, path: str | Path, root: str = "root") -> Grammar:
        return cls.parse(Path(path).read_text(encoding="utf-8"), root)

    def accepts(self, text: str) -> bool:
        memo: dict[tuple[int, int], frozenset[int]] = {}
        return len(text) in self._match(self.rules[self.root], text, 0, memo)

    def _match(
        self,
        node: object,
        text: str,
        pos: int,
        memo: dict[tuple[int, int], frozenset[int]],
    ) -> frozenset[int]:
        key = (id(node), pos)
        cached = memo.get(key)
        if cached is not None:
            return cached
        # Guard against left recursion rather than overflowing the stack on it.
        memo[key] = frozenset()
        result = self._match_uncached(node, text, pos, memo)
        memo[key] = result
        return result

    def _match_uncached(
        self,
        node: object,
        text: str,
        pos: int,
        memo: dict[tuple[int, int], frozenset[int]],
    ) -> frozenset[int]:
        if isinstance(node, _Lit):
            end = pos + len(node.text)
            return frozenset({end}) if text.startswith(node.text, pos) else frozenset()

        if isinstance(node, _Class):
            if pos >= len(text):
                return frozenset()
            ch = text[pos]
            inside = any(low <= ch <= high for low, high in node.ranges)
            return frozenset({pos + 1}) if inside != node.negated else frozenset()

        if isinstance(node, _Ref):
            return self._match(self.rules[node.name], text, pos, memo)

        if isinstance(node, _Alt):
            ends: set[int] = set()
            for option in node.options:
                ends |= self._match(option, text, pos, memo)
            return frozenset(ends)

        if isinstance(node, _Seq):
            frontier = {pos}
            for item in node.items:
                nxt: set[int] = set()
                for p in frontier:
                    nxt |= self._match(item, text, p, memo)
                if not nxt:
                    return frozenset()
                frontier = nxt
            return frozenset(frontier)

        if isinstance(node, _Rep):
            ends: set[int] = set()
            if node.low == 0:
                ends.add(pos)
            frontier = {pos}
            count = 0
            while frontier and (node.high is None or count < node.high):
                count += 1
                nxt: set[int] = set()
                for p in frontier:
                    for q in self._match(node.node, text, p, memo):
                        if q == p:
                            raise GrammarError(
                                "repetition over a rule that matches the empty "
                                "string is outside the supported subset"
                            )
                        nxt.add(q)
                if not nxt:
                    break
                if count >= node.low:
                    ends |= nxt
                frontier = nxt
            return frozenset(ends)

        raise GrammarError(f"unsupported node {node!r}")


def _referenced(node: object) -> set[str]:
    if isinstance(node, _Ref):
        return {node.name}
    if isinstance(node, (_Alt,)):
        return set().union(*(_referenced(o) for o in node.options))
    if isinstance(node, (_Seq,)):
        return set().union(*(_referenced(o) for o in node.items)) if node.items else set()
    if isinstance(node, _Rep):
        return _referenced(node.node)
    return set()


def load_grammar(path: str | Path | None = None) -> Grammar:
    """Load the project grammar, defaulting to the frozen `schema/cmd.gbnf`."""
    if path is None:
        from schema.schema import GRAMMAR_PATH

        path = GRAMMAR_PATH
    return Grammar.from_file(path)
