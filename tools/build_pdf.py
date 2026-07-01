#!/usr/bin/env python3
"""
build_pdf.py -- compile docs/PRD.tex into a PDF.

Standard library only. No pip install required. Works on Windows, Linux, macOS.

Usage
-----
    python build_pdf.py                        # compile docs/PRD.tex -> build/PRD.pdf
    python build_pdf.py docs/PRD.tex           # explicit source
    python build_pdf.py --outdir out           # different output directory
    python build_pdf.py --engine pdflatex      # force a specific engine
    python build_pdf.py --list-engines         # show what is installed, then exit
    python build_pdf.py --clean                # delete aux files afterwards
    python build_pdf.py --open                 # open the PDF when done
    python build_pdf.py --no-check             # skip the structural pre-flight
    python build_pdf.py --strict               # refuse to compile if pre-flight fails

Pre-flight
----------
If `check_tex.py` sits next to this script it is run first, catching the errors
that actually break a table-heavy document (non-ASCII in text mode, unmatched
environments, wrong cell counts, column widths past \\textwidth, dangling refs).
Problems are reported but do not block the build unless --strict is given, since
LaTeX often produces a usable PDF anyway and its own log is more precise.

Why multiple passes
-------------------
The document uses \\tableofcontents, \\ref/\\label, longtable, and hyperref.
Each of those needs information written to the .aux/.toc file on pass N and read
back on pass N+1. One pass produces a PDF with "??" instead of cross-references
and a missing table of contents.

`latexmk` figures out the required number of passes on its own, so it is
preferred when available. Without it we run the engine three times, which is
sufficient for this document (pass 1 writes .aux/.toc, pass 2 resolves refs and
settles longtable column widths, pass 3 settles any page numbers that shifted).

Exit codes
----------
    0  PDF produced
    1  compilation failed (LaTeX errors printed)
    2  no TeX engine found
    3  source file not found
    4  pre-flight found problems and --strict was given
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

DEFAULT_SOURCE = Path("docs") / "PRD.tex"
DEFAULT_OUTDIR = Path("build")
N_PASSES = 3

# Engines in order of preference. latexmk is a wrapper, not an engine, and is
# handled separately -- it is tried first because it manages passes itself.
ENGINES = ["pdflatex", "lualatex", "xelatex", "tectonic"]

# Auxiliary extensions produced by this document, for --clean.
AUX_EXTS = [
    ".aux", ".log", ".out", ".toc", ".lof", ".lot", ".fls",
    ".fdb_latexmk", ".synctex.gz", ".bbl", ".blg", ".nav", ".snm", ".vrb",
    ".xdv", ".run.xml",
]

# Packages this document needs, mapped to the distribution package that ships
# them, so a "file not found" error can be turned into an actionable message.
PACKAGE_HINTS = {
    "microtype":  "texlive-latex-recommended",
    "lmodern":    "texlive-latex-recommended",
    "fancyhdr":   "texlive-latex-extra",
    "titlesec":   "texlive-latex-extra",
    "enumitem":   "texlive-latex-extra",
    "booktabs":   "texlive-latex-recommended",
    "longtable":  "texlive-latex-base",
    "ragged2e":   "texlive-latex-recommended",
    "tikz":       "texlive-pictures",
    "pgf":        "texlive-pictures",
    "listings":   "texlive-latex-recommended",
    "caption":    "texlive-latex-recommended",
    "hyperref":   "texlive-latex-base",
    "amssymb":    "texlive-latex-base",
    "geometry":   "texlive-latex-base",
    "xcolor":     "texlive-latex-recommended",
}

IS_WINDOWS = os.name == "nt"


# ----------------------------------------------------------------------------
# Small terminal helpers
# ----------------------------------------------------------------------------

def _supports_colour() -> bool:
    if not sys.stdout.isatty():
        return False
    if IS_WINDOWS and not os.environ.get("WT_SESSION") and not os.environ.get("TERM"):
        return False
    return True


_C = _supports_colour()


def _paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _C else text


def info(msg: str) -> None:
    print(f"{_paint('[build]', '36')} {msg}")


def ok(msg: str) -> None:
    print(f"{_paint('[ ok ]', '32')} {msg}")


def warn(msg: str) -> None:
    print(f"{_paint('[warn]', '33')} {msg}")


def fail(msg: str) -> None:
    # Flush stdout first: stderr is unbuffered, so without this the failure line
    # can appear *above* output that was logically printed before it.
    sys.stdout.flush()
    print(f"{_paint('[fail]', '31')} {msg}", file=sys.stderr)
    sys.stderr.flush()


# ----------------------------------------------------------------------------
# Engine discovery
# ----------------------------------------------------------------------------

def find_latexmk() -> str | None:
    return shutil.which("latexmk")


def find_engines() -> list[str]:
    return [e for e in ENGINES if shutil.which(e)]


def report_engines() -> None:
    lmk = find_latexmk()
    found = find_engines()
    print("latexmk :", lmk or "not found")
    print("engines :", ", ".join(found) if found else "none found")
    if not found:
        print()
        print(install_advice())


def install_advice() -> str:
    if IS_WINDOWS:
        return (
            "No TeX installation found on PATH.\n"
            "\n"
            "Install one of the following, then reopen your shell so PATH updates:\n"
            "  MiKTeX     https://miktex.org/download          (auto-installs missing packages)\n"
            "  TeX Live   https://tug.org/texlive/windows.html (complete, ~5 GB)\n"
            "\n"
            "Or, with a package manager:\n"
            "  winget install MiKTeX.MiKTeX\n"
            "  choco install miktex\n"
        )
    if sys.platform == "darwin":
        return (
            "No TeX installation found on PATH.\n"
            "\n"
            "  brew install --cask mactex-no-gui     # complete\n"
            "  brew install --cask basictex          # minimal, then use tlmgr\n"
        )
    return (
        "No TeX installation found on PATH.\n"
        "\n"
        "Debian / Ubuntu:\n"
        "  sudo apt install texlive-latex-recommended texlive-latex-extra \\\n"
        "                   texlive-pictures texlive-fonts-recommended latexmk\n"
        "\n"
        "Fedora:\n"
        "  sudo dnf install texlive-scheme-medium latexmk\n"
        "\n"
        "Arch:\n"
        "  sudo pacman -S texlive-latexrecommended texlive-latexextra texlive-pictures\n"
    )


# ----------------------------------------------------------------------------
# Command construction
# ----------------------------------------------------------------------------

def latexmk_cmd(engine: str, source: Path, outdir: Path) -> list[str]:
    engine_flag = {
        "pdflatex": "-pdf",
        "lualatex": "-pdflua",
        "xelatex":  "-pdfxe",
    }.get(engine, "-pdf")
    return [
        "latexmk",
        engine_flag,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-outdir={outdir}",
        str(source),
    ]


def engine_cmd(engine: str, source: Path, outdir: Path) -> list[str]:
    if engine == "tectonic":
        # tectonic resolves passes itself and downloads packages on demand.
        return [
            "tectonic",
            "--keep-logs",
            "--synctex=false",
            "--outdir", str(outdir),
            str(source),
        ]
    return [
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-output-directory", str(outdir),
        str(source),
    ]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a command with shell=False, capturing output as text."""
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


# ----------------------------------------------------------------------------
# Log analysis
# ----------------------------------------------------------------------------

# `-file-line-error` makes LaTeX print errors as  path/file.tex:LINE: message
FILE_LINE_ERROR = re.compile(r"^(?P<file>[^\s:][^:]*):(?P<line>\d+):\s*(?P<msg>.+)$")
MISSING_FILE = re.compile(r"LaTeX Error: File [`'\"]?([^'\"`\s]+)['\"`]? not found")
MISSING_FONT = re.compile(r"Font \\?[\w/]+ not (?:loadable|found)")
OVERFULL = re.compile(r"^(Overfull|Underfull) \\(h|v)box")
UNDEFINED_REF = re.compile(r"(?:Reference|Citation) [`'\"]([^'\"`]+)['\"`] on page")


def read_log(log_path: Path) -> str:
    if not log_path.exists():
        return ""
    return log_path.read_text(encoding="utf-8", errors="replace")


def missing_packages(log: str) -> list[str]:
    names = []
    for m in MISSING_FILE.finditer(log):
        f = m.group(1)
        names.append(Path(f).stem if f.endswith((".sty", ".cls", ".def")) else f)
    # preserve order, drop duplicates
    return list(dict.fromkeys(names))


def error_lines(log: str, limit: int = 25) -> list[str]:
    out: list[str] = []
    for raw in log.splitlines():
        line = raw.rstrip()
        if FILE_LINE_ERROR.match(line) and (" Error" in line or "! " in line):
            out.append(line)
        elif line.startswith("! "):
            out.append(line)
        elif "LaTeX Error:" in line or "Emergency stop" in line:
            out.append(line)
        elif "Runaway argument" in line or "Missing $ inserted" in line:
            out.append(line)
        if len(out) >= limit:
            break
    return list(dict.fromkeys(out))


def count_boxes(log: str) -> tuple[int, int]:
    over = under = 0
    for line in log.splitlines():
        m = OVERFULL.match(line)
        if m:
            if m.group(1) == "Overfull":
                over += 1
            else:
                under += 1
    return over, under


def undefined_refs(log: str) -> list[str]:
    return list(dict.fromkeys(UNDEFINED_REF.findall(log)))


def report_failure(log: str, proc_output: str, log_path: Path) -> None:
    print()
    fail("LaTeX did not produce a PDF.")

    pkgs = missing_packages(log or proc_output)
    if pkgs:
        print()
        print(_paint("Missing files / packages:", "1"))
        for p in pkgs:
            hint = PACKAGE_HINTS.get(p)
            suffix = f"   -> ships in {hint}" if hint else ""
            print(f"  - {p}{suffix}")
        print()
        if IS_WINDOWS:
            print("  MiKTeX installs missing packages on demand; if it did not, run:")
            print("    miktex packages install <name>")
        else:
            print("  TeX Live:  sudo tlmgr install <name>")
            print("  Debian  :  sudo apt install " + " ".join(
                sorted({PACKAGE_HINTS[p] for p in pkgs if p in PACKAGE_HINTS})
            ))

    errs = error_lines(log or proc_output)
    if errs:
        print()
        print(_paint("LaTeX errors:", "1"))
        for e in errs:
            print("  " + e)

    if not pkgs and not errs:
        tail = (log or proc_output).splitlines()[-40:]
        print()
        print(_paint("Last 40 lines of output:", "1"))
        for line in tail:
            print("  " + line.rstrip())

    if log_path.exists():
        print()
        print(f"Full log: {log_path}")


def report_warnings(log: str) -> None:
    over, under = count_boxes(log)
    refs = undefined_refs(log)
    if over:
        warn(f"{over} overfull hbox/vbox warning(s) -- content may extend past the margin.")
    if under:
        info(f"{under} underfull box warning(s) (cosmetic; usually safe to ignore).")
    if refs:
        warn("Undefined references (run again if this persists): " + ", ".join(refs[:8]))
    if MISSING_FONT.search(log):
        warn("A font could not be loaded; check the log.")


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------

def clean_aux(outdir: Path, stem: str) -> int:
    removed = 0
    for ext in AUX_EXTS:
        p = outdir / (stem + ext)
        if p.exists():
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def open_file(path: Path) -> None:
    try:
        if IS_WINDOWS:
            os.startfile(str(path))                                  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as exc:                                          # noqa: BLE001
        warn(f"Could not open the PDF automatically: {exc}")


def preflight(source: Path) -> int:
    """Run check_tex.py on the source, if it is present. Returns its exit code
    (0 = clean, 1 = problems, 2 = unavailable/not run)."""
    checker = Path(__file__).resolve().parent / "check_tex.py"
    if not checker.exists():
        return 2
    info("pre-flight (check_tex.py) ...")
    proc = subprocess.run(
        [sys.executable, str(checker), str(source)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", check=False,
    )
    for line in (proc.stdout or "").splitlines():
        if line.strip():
            print("       " + line)
    return proc.returncode


def build(source: Path, outdir: Path, engine: str | None,
          use_latexmk: bool, verbose: bool, check: bool = True,
          strict: bool = False) -> int:
    project = Path.cwd()

    if not source.exists():
        fail(f"Source not found: {source}")
        return 3

    if check:
        rc = preflight(source)
        if rc == 1:
            print()
            if strict:
                fail("Pre-flight found problems and --strict is set; not compiling.")
                return 4
            warn("Pre-flight found problems (listed above). Compiling anyway -- "
                 "use --strict to stop here, --no-check to skip the check.")
            print()

    outdir.mkdir(parents=True, exist_ok=True)
    stem = source.stem
    log_path = outdir / f"{stem}.log"
    pdf_path = outdir / f"{stem}.pdf"

    # A stale PDF must not be mistaken for a fresh one.
    if pdf_path.exists():
        try:
            pdf_path.unlink()
        except OSError:
            fail(f"{pdf_path} is locked -- close it in your PDF viewer and retry.")
            return 1

    available = find_engines()
    if not available:
        fail("No TeX engine found.")
        print()
        print(install_advice())
        return 2

    if engine:
        if engine not in available:
            fail(f"Requested engine '{engine}' is not on PATH. Available: {', '.join(available)}")
            return 2
    else:
        engine = available[0]

    lmk = find_latexmk() if use_latexmk else None

    info(f"source : {source}")
    info(f"outdir : {outdir}")
    info(f"engine : {engine}" + ("  (driven by latexmk)" if lmk else ""))

    last_output = ""

    if lmk:
        cmd = latexmk_cmd(engine, source, outdir)
        if verbose:
            info("$ " + " ".join(cmd))
        proc = run(cmd, project)
        last_output = proc.stdout or ""
        if verbose:
            print(last_output)
    else:
        passes = 1 if engine == "tectonic" else N_PASSES
        if passes > 1:
            info(f"latexmk not found -- running {engine} {passes} times manually.")
        for i in range(1, passes + 1):
            cmd = engine_cmd(engine, source, outdir)
            if verbose:
                info("$ " + " ".join(cmd))
            else:
                info(f"pass {i}/{passes} ...")
            proc = run(cmd, project)
            last_output = proc.stdout or ""
            if verbose:
                print(last_output)
            # halt-on-error means a non-zero code on pass 1 is fatal; there is
            # no point running passes 2 and 3 against a broken document.
            if proc.returncode != 0 and not pdf_path.exists():
                break

    log = read_log(log_path)

    if not pdf_path.exists():
        report_failure(log, last_output, log_path)
        return 1

    report_warnings(log)

    size_kb = pdf_path.stat().st_size / 1024
    pages = None
    m = re.search(r"Output written on .*?\((\d+) pages?", log)
    if m:
        pages = int(m.group(1))

    print()
    detail = f"{size_kb:,.0f} KB" + (f", {pages} pages" if pages else "")
    ok(f"{pdf_path}  ({detail})")
    return 0


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="build_pdf.py",
        description="Compile the PRD LaTeX source into a PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python build_pdf.py\n"
            "  python build_pdf.py --engine pdflatex --clean\n"
            "  python build_pdf.py docs/PRD.tex --outdir dist --open\n"
        ),
    )
    ap.add_argument("source", nargs="?", default=str(DEFAULT_SOURCE),
                    help=f"path to the .tex file (default: {DEFAULT_SOURCE})")
    ap.add_argument("-o", "--outdir", default=str(DEFAULT_OUTDIR),
                    help=f"output directory (default: {DEFAULT_OUTDIR})")
    ap.add_argument("-e", "--engine", choices=ENGINES, default=None,
                    help="force a TeX engine (default: first available)")
    ap.add_argument("--no-latexmk", action="store_true",
                    help="ignore latexmk and drive the engine directly")
    ap.add_argument("--clean", action="store_true",
                    help="remove .aux/.log/.toc/... after a successful build")
    ap.add_argument("--open", dest="open_pdf", action="store_true",
                    help="open the PDF in the default viewer when done")
    ap.add_argument("--no-check", dest="check", action="store_false",
                    help="skip the check_tex.py structural pre-flight")
    ap.add_argument("--strict", action="store_true",
                    help="refuse to compile if the pre-flight reports problems")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="stream full engine output")
    ap.add_argument("--list-engines", action="store_true",
                    help="report which TeX tools are installed, then exit")
    args = ap.parse_args(argv)

    if args.list_engines:
        report_engines()
        return 0

    # Run relative to the script's directory so `python build_pdf.py` works
    # regardless of the shell's current directory.
    script_dir = Path(__file__).resolve().parent
    if Path.cwd() != script_dir:
        os.chdir(script_dir)

    source = Path(args.source)
    outdir = Path(args.outdir)

    rc = build(
        source=source,
        outdir=outdir,
        engine=args.engine,
        use_latexmk=not args.no_latexmk,
        verbose=args.verbose,
        check=args.check,
        strict=args.strict,
    )

    if rc == 0 and args.clean:
        n = clean_aux(outdir, source.stem)
        info(f"removed {n} auxiliary file(s)")

    if rc == 0 and args.open_pdf:
        open_file(outdir / f"{source.stem}.pdf")

    return rc


if __name__ == "__main__":
    sys.exit(main())
