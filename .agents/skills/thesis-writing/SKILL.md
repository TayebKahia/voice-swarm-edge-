---
name: thesis-writing
description: >-
  Guidelines, academic tone, chapter formulas, LaTeX conventions, and quality
  checklists for drafting, structuring, and reviewing academic Master's and
  Engineering (PFE) thesis chapters. Use whenever writing, editing, or auditing
  files under thesis/ or when asked to work on the thesis.
---

# Academic Thesis Writing Skill

This skill governs the structure, scholarly tone, methodology, and LaTeX standards for the **Master's Thesis** (`thesis/master/`) and the companion **Mémoire d'Ingénieur** (`thesis/ingenieur/`).

Any agent working on the thesis must inspect and adhere to these guidelines to ensure the final manuscript meets top-tier academic and engineering defense standards.

`prd.md` (untracked, the project's living contract) is the authoritative source for chapter
outlines (§3.1), material ownership across the two documents (Table 3, the write-once rule), and
the closed citation set (`thesis/bibliography.tex`). This skill operationalises that contract into
writing craft. If the two ever disagree, `prd.md` wins, and this file must be updated to match —
not the other way around.

---

## 1. Core Principles & Mindset

1. **A Thesis is a Scientific Argument, Not a Diary:**
   - Never write chronologically (*"First we tried X, then we encountered an error, then we wrote script Y..."*).
   - Every chapter, section, and paragraph exists to support or test a specific thesis proposition or **Research Question (RQ)**.
2. **Dual-Track Division of Concerns:**
   - **Master's Thesis (`thesis/master/`):** Focuses on scientific inquiry, RQ1 (accuracy–efficiency Pareto trade-off across 0.36–1.2B models on edge hardware), formal constrained decoding (C1), dataset pipeline & leakage prevention (C2), and quantitative benchmarking with ablation studies (C3).
   - **Mémoire d'Ingénieur (`thesis/ingenieur/`):** Focuses on engineering architecture, dual-path runtime (keyword spotter preemption for safety), real-time edge deployment, acoustic robustness, and the live robotic demonstration.
3. **Reproducibility by Construction:**
   - Any external researcher must be able to replicate the exact results from the descriptions, formal schemas, hyperparameters, and protocols provided.

---

## 2. Academic Tone & Writing Standards

### The "Assertion–Evidence–Impact" Paragraph Structure
Every technical paragraph must follow this 3-step rhythm:
1. **Assertion (Topic sentence):** State the claim or finding directly.
2. **Evidence:** Provide hard data, citations (`\cite{...}`), equations, or figure references (`Figure~\ref{...}`).
3. **Impact:** Explain the technical, safety, or architectural consequence of that evidence.

### Precision Over Emotion (Anti-Fluff Rules)
- **Zero marketing adjectives:** Eliminate words like *groundbreaking*, *revolutionary*, *game-changing*, *obviously*, *state-of-the-art* (unless citing a benchmark's formal name), *huge*, *seamless*.
- **Quantitative specificity:** Replace vague qualifiers with exact numbers, hardware specs, and margins:
  - ❌ *"The model achieved high throughput on the Raspberry Pi."*
  - ✔️ *"Qwen2.5-0.5B at Q4\_K\_M reached 20.97~tok/s on 3 threads of a Raspberry Pi 5, exceeding the 20~tok/s floor by 4.9\%."*
- **Scholarly verb choices:**
  - Prefer: *demonstrates, exhibits, bounds, mitigates, constrains, isolates, establishes, yields, degrades*.
  - Avoid: *shows, gets, fixes, deals with, handles*.
- **No unearned absolutes:** Never write *guarantees, proves, ensures, always,* or *impossible*
  unless the evidence is a mathematical proof. State the observed result and the mechanism behind
  it as two separate clauses:
  - ❌ *"The clamp guarantees collision-free flight."*
  - ✔️ *"Zero collisions were observed across 150 trials, backed by a geometric separation clamp."*
  This exact phrasing is locked project-wide for NFR-12 and generalises to every safety or
  correctness claim in either document.

---

## 3. Chapter-by-Chapter Blueprint

**Before writing, confirm the section list against `prd.md` §3.1 (the frozen outline) and the
existing scaffold for that chapter.** The two documents do not share one blueprint — their
chapter counts, topics, and closing structure differ. Never add, merge, or reorder chapters beyond
what `prd.md` §3.1 specifies; if a chapter seems to need splitting or combining, change `prd.md`
first, then the scaffold, then the prose — never the prose alone.

### Mémoire de Master — six chapters (`thesis/master/`)

1. **Introduction** — the edge-inference problem; why structured output matters for robot
   control; formal Research Questions in a quote block; Contributions (C1–C3) as bullets; a short
   document-outline paragraph.
2. **Related work** — four themes, each its own section, per the existing scaffold: edge LLM
   inference and single-board-computer benchmarking; quantisation; constrained decoding (**GBNF
   only** — this project's actual stack; do not introduce a tool this project never used, e.g.
   Outlines); spoken-language understanding for robotics. Close with a single Positioning section
   stating the gap this thesis fills — do not scatter a gap statement into every subsection. Use a
   three-part shape for that section: **Synthesis** (where the intersection of these four themes
   currently stands), **Gap** (what the literature actually reviewed does not address — verify
   this against the papers once they are read; do not reuse an unverified example as if it were
   established), **Delta** (how C1–C3 specifically close that gap).
3. **Method** — command schema and grammar (formal spec), label-first dataset construction, the
   LoRA recipe, the quantisation procedure, the evaluation protocol and definitions of record.
4. **Results** — Exp-0, Exp-1, the quantisation delta, the grammar ablation; the statistical
   analysis and the selection rule applied. Metrics are whatever the harness behind the cited CSV
   actually reports — currently exact match, intent/slot F1, schema validity, false-command rate,
   safe-failure rate, and throughput in tok/s. Never cite a metric the Master's own harness does
   not compute (e.g. time-to-first-token belongs to the Ingénieur's preemption validation, §5
   below — see Table 3, write-once).
5. **Discussion and limitations** — the accuracy–efficiency trade-off as a Pareto frontier;
   failure-mode analysis; threats to internal and external validity. Honest and hedged is the
   right register here; do not pre-empt Chapter 6's verdict.
6. **Conclusion and future work** — a direct, unhedged answer to RQ1 against the measured
   results; a short statement of what the comparison establishes; prioritised next steps. No new
   caveats belong here — a limitation surfacing while drafting this chapter belongs in Chapter 5,
   not here.

### Mémoire d'Ingénieur — six chapters (`thesis/ingenieur/`)

1. **Introduction** — operational context, engineering requirements, the safety problem.
2. **State of the art** — voice-controlled UAV systems; positioning against Lim et al.
   (`\cite{lim2025}`). This is the *only* document that discusses voice-UAV literature (Table 3).
3. **Architecture and design** — the dual-path decomposition, the Branch A membership rule, the
   three validation layers, the latency budget, resource allocation.
4. **Implementation** — audio chain, runtime, command bus, state machine, swarm controller, both
   simulation backends.
5. **Validation** — Exp-2, Exp-3, Exp-4 with the statistical analysis. Pipeline-latency metrics,
   including time-to-first-token / preemption latency (spike S7), belong here — not in the
   Master's Results chapter.
6. **Demonstration, limitations, future work, conclusion** — one combined chapter, per `prd.md`
   §3.1. Do not split this the way the Master's was split unless `prd.md` changes again.

---

## 4. LaTeX Standards & Best Practices

1. **Citations:**
   - Always use `\cite{key}` for references. Never write author names without a citation key.
   - Use non-breaking spaces before citations and cross-references: `Figure~\ref{fig:arch}`, `Table~\ref{tab:results}`, `Model~\cite{sbc2025}`.
   - **Closed set only:** cite exclusively from the 18 keys already in `thesis/bibliography.tex`.
     If a claim needs a source that is not there, say so in prose (or mark a `\TODO{}`) instead of
     inventing a `\bibitem`. Do not name-drop a tool, model, or method this project never actually
     used just because it is common in the field.
   - **When referring to the companion document,** always say "the \emph{Mémoire d'Ingénieur}" (or
     "\emph{Mémoire de Master}") — never a paraphrase like "the companion report." Naming a
     specific chapter number across documents is fragile: the two are compiled separately with no
     shared `\ref`, so a hardcoded number goes stale the moment either outline changes (as Master's
     just did). If a chapter number must be given, re-check it against `prd.md` §3.1 at the moment
     of writing rather than trusting an earlier draft.
2. **Figures & Visuals:**
   - **Vector Graphics Only:** Figures must be vector PDF, SVG, or native TikZ. Never use raster formats (PNG, JPG) for architectural diagrams or plots.
   - **Self-Contained Captions:** Captions must fully explain what the figure shows, including legends, axes, and key takeaways, so the figure can be understood independently of the text.
   - **In-Text Reference:** Every figure and table *must* be referenced and analyzed in the main body text (`As illustrated in Figure~\ref{fig:...}`).
3. **Typography & Math:**
   - Units: Use `~` for units: `20~tok/s`, `1{,}100~ms`, `0.5~B parameters`.
   - Math Mode: Distinguish between variables ($N$, $k$) and text abbreviations within math (`\text{tok/s}`).
   - Schema / Code listings: Use clean, formatted code environments (e.g., `listings` with appropriate font sizing).

### Tooling & Automation

4. **The `\TODO{}` macro:** neither thesis has a `main.tex`/preamble yet, so this macro is not
   defined anywhere. Whoever creates `thesis/master/main.tex` (or `ingenieur/main.tex`) must add,
   near the other preamble commands:
   ```latex
   \newcommand{\TODO}[1]{\textbf{\color{red}[TODO: #1]}}
   ```
   before any chapter using `\TODO{}` is `\input`. Until that preamble exists, a chapter that uses
   `\TODO{}` will not compile stand-alone — note this rather than silently dropping the marker.
5. **Validate before calling a chapter done:** run `python tools/check_tex.py <file>` — it catches
   dangling `\ref`/`\cite`, wrong table cell counts, over-wide columns, and non-ASCII characters
   without needing a TeX install. It checks labels/bibitems *within the file it is given*, so
   running it against one chapter scaffold in isolation will false-positive on every cross-chapter
   `\ref` and on citations (the bibliography lives in `thesis/bibliography.tex`, a sibling file) —
   it is only conclusive once run against the assembled `main.tex`, which does not exist yet for
   either thesis. `tools/build_pdf.py` compiles a document end to end once one does; today it only
   targets `docs/project/PRD.tex`.
6. **Never hand-type a number that a script could produce.** `eval/tables.py` already renders
   Tables 17–18 straight from `results/surface_b.csv` and the Kaggle CSV with the explicit
   discipline "no number is typed by hand." When a results table or figure has a generating
   script, regenerate from it; when it doesn't yet, that is a gap to flag, not license to
   hand-copy a number from a CSV into a `tabular`.

---

## 5. Pre-Flight Quality Checklist

Before finalizing any section or chapter, the agent must verify:
- [ ] Are all claims backed by quantitative data, mathematical definitions, or literature citations?
- [ ] Is the paragraph rhythm following *Assertion $\to$ Evidence $\to$ Impact*?
- [ ] Are all acronyms defined on first use?
- [ ] Are all figures vector graphics with self-contained captions?
- [ ] Does every figure and table have an explicit in-text reference and discussion?
- [ ] Are all speculative or promotional adjectives removed?
- [ ] Is there a clear connection back to the document's central Research Question(s)?
- [ ] Does every citation key exist in `thesis/bibliography.tex`? (No fabricated `\bibitem`s.)
- [ ] Does every number trace to a named `results/*.csv` row, a `spikes/reports/*` file, or
      `STATE.md`? If not, is it marked with a visible `\TODO{}` instead of a plausible figure?
- [ ] Does this chapter's section list match `prd.md` §3.1 exactly — no chapters added, merged,
      or reordered without updating `prd.md` first?
- [ ] Has `python tools/check_tex.py <file>` been run on it — and, if run against a lone chapter
      rather than the assembled `main.tex`, are its cross-file `\ref`/`\cite` findings discounted
      as expected false positives rather than "fixed" by deleting a valid reference?
- [ ] Was every table or figure generated by a script reading `results/*.csv` (e.g.
      `eval/tables.py`) rather than hand-typed from a CSV someone read once?
- [ ] Is every reference to the other document phrased as "the \emph{Mémoire d'Ingénieur}" /
      "\emph{Mémoire de Master}," with no hardcoded chapter number left unverified against the
      other document's current outline?
