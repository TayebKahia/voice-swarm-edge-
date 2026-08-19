"""Tests for the Table 33 renderer in `eval/tables.py`.

Table 33 is the one table that carries the fourth model, and it is the one whose
numbers nothing else cross-checks: Tables 17/18/19 are re-derived from Surface B
and guarded by `eval/mcnemar.py`'s provenance assertion, but Table 33 reads
`surface_a.csv` and the per-model configs and is otherwise on its own. These tests
are that guard.
"""

from __future__ import annotations

import pytest

from eval.tables import _model_meta, markdown_to_latex, table17, table33

SPLITS = ("test_synth", "test_golden", "test_ood")


def _row(model, split, em, surface="A_fp16_finetuned"):
    return {"model": model, "surface": surface, "split": split,
            "n": "200", "exact_match": str(em), "best_val_em": ""}


@pytest.fixture
def meta():
    return _model_meta()


def test_every_config_declares_params_and_family(meta):
    """Table 33 needs both for every model; a config missing one must fail loudly."""
    assert len(meta) == 4, f"expected four configs, got {sorted(meta)}"
    for name, entry in meta.items():
        assert entry["params"] > 0, name
        assert entry["family"], name


def test_the_iso_parameter_pair_is_qwen_and_danube(meta):
    """The closest cross-family pair by parameter count is the control that was
    added for exactly this purpose. If a future config change makes some other
    pair closer, this test fails and the table's framing needs revisiting."""
    rows = [_row(m, "test_golden", 0.9) for m in meta]
    text = table33(rows)
    line = next(l for l in text.splitlines() if "Family, at matched size" in l)
    assert "qwen2.5-0.5b-instruct" in line
    assert "h2o-danube3-500m-chat" in line


def test_bracketing_claim_appears_only_when_true(meta):
    """'The largest model is not the best' is a claim about the data, so it must
    not be printed when the data does not support it."""
    ordered = sorted(meta, key=lambda m: meta[m]["params"])
    smallest, largest = ordered[0], ordered[-1]

    # Largest genuinely best -> the claim must be absent.
    rows = [_row(m, "test_golden", 0.50) for m in meta if m != largest]
    rows.append(_row(largest, "test_golden", 0.99))
    assert "largest model is not the best" not in table33(rows)

    # A smaller model beats it -> the claim must appear, naming that model.
    rows = [_row(m, "test_golden", 0.50) for m in meta if m != largest]
    rows.append(_row(largest, "test_golden", 0.60))
    rows = [r for r in rows if r["model"] != smallest]
    rows.append(_row(smallest, "test_golden", 0.95))
    text = table33(rows)
    assert "largest model is not the best" in text
    assert smallest in text


def test_zero_shot_rows_are_excluded(meta):
    """Surface A carries zero-shot rows at EM 0.0 alongside the fine-tuned ones.
    Averaging them in would halve every figure in the table."""
    rows = []
    for m in meta:
        rows.append(_row(m, "test_golden", 0.90))
        rows.append(_row(m, "test_golden", 0.0, surface="A_fp16_zeroshot"))
    text = table33(rows)
    assert "0.9000" in text
    assert "0.0000" not in text


def test_a_model_without_config_metadata_is_refused(meta):
    """A model in the CSV but not in train/configs/ must stop the render rather
    than be dropped silently -- a missing row in a comparison table is invisible."""
    rows = [_row("some-unregistered-model", "test_golden", 0.8)]
    with pytest.raises(SystemExit, match="no config metadata"):
        table33(rows)


def test_rows_are_ordered_by_parameter_count(meta):
    rows = [_row(m, "test_golden", 0.9) for m in meta]
    text = table33(rows)
    positions = [text.index(f"`{m}` |") for m in
                 sorted(meta, key=lambda x: meta[x]["params"])]
    assert positions == sorted(positions), "table is not ordered by parameter count"


def test_the_rendered_table_matches_the_committed_csv():
    """End-to-end: the table on disk is what the current CSV renders to."""
    import csv
    from pathlib import Path

    from eval.tables import RESULTS, SURFACE_A

    rendered = table33(list(csv.DictReader(SURFACE_A.open(encoding="utf-8"))))
    on_disk = (RESULTS / "table33_iso_parameter.md").read_text(encoding="utf-8")
    assert rendered == on_disk, "results/table33_iso_parameter.md is stale -- re-run eval/tables.py"


def _sb_row(split, slot="0.0"):
    """A Surface-B accuracy row as `results/surface_b.csv` carries it."""
    return {"model": "qwen2.5-0.5b-instruct", "quant": "Q4_K_M", "grammar": "on",
            "split": split, "n": "150", "exact_match": "0.7466666666666667",
            "intent_macro_f1": "0.855", "slot_micro_f1": slot,
            "safe_failure_rate": "0.158", "schema_validity": "1.0",
            "false_command_rate": "0.2533333333333333"}


def test_slot_f1_is_withheld_on_the_abstention_split():
    """`test_ood`'s gold is `{"intent":"unknown"}` on all 150 items -- zero gold slot
    pairs. So tp and fn are pinned at 0 and `slot_micro_f1` can only return 0.0 (the
    model emitted a slot) or nan (it did not); it cannot tell one spurious slot from
    thirty-one. Printing the arithmetically-correct 0.0 beside the 97.5 and 94.5 of
    the other splits reads as a collapse in slot filling that never happened, so the
    cell must be `--`. `false_command_rate` reports what actually happened there.
    """
    ood = next(l for l in table17([_sb_row("test_ood")]).splitlines()
               if l.startswith("|") and "`test_ood`" in l)
    cells = [c.strip() for c in ood.split("|")]
    assert cells[5] == "--", ood
    assert cells[6] == "74.7", f"EM must still be reported on this split: {ood}"


def test_slot_f1_is_reported_on_the_splits_that_have_slots():
    """The guard is scoped to splits with no gold slots. It must not swallow a real
    measurement on `test_synth` or `test_golden`, where slot-F1 is the headline."""
    for split in ("test_synth", "test_golden"):
        line = next(l for l in table17([_sb_row(split, slot="0.961")]).splitlines()
                    if l.startswith("|") and f"`{split}`" in l)
        assert [c.strip() for c in line.split("|")][5] == "96.1", line


# --- LaTeX emission -------------------------------------------------------------

_MD = """### Table X: a title

Prose that becomes the caption, naming `results/surface_b.csv` and the *deployment
pipeline* and a **bold** phrase.

| Model | Quant | Split | EM |
| :--- | :--- | :--- | ---: |
| qwen2.5-0.5b-instruct | Q4_K_M | `test_ood` | -- |

A trailing note that qualifies the numbers.
"""


def test_latex_escapes_the_characters_that_would_break_the_build():
    """Artefact stems carry `_` (Q4_K_M, test_ood). Unescaped, each one opens math mode
    and the chapter stops compiling -- so this is a build-breaking class of bug, not a
    cosmetic one."""
    tex = markdown_to_latex(_MD, "tab:x")
    assert r"Q4\_K\_M" in tex
    assert r"\texttt{test\_ood}" in tex
    assert "Q4_K_M" not in tex.replace(r"Q4\_K\_M", "")


def test_latex_carries_the_caption_the_note_and_the_emphasis():
    tex = markdown_to_latex(_MD, "tab:x")
    assert r"\label{tab:x}" in tex
    assert r"\emph{deployment pipeline}" in tex
    assert r"\textbf{bold}" in tex
    assert "A trailing note that qualifies the numbers." in tex
    assert tex.count(r"\caption[") == 1


def test_latex_column_spec_follows_the_markdown_alignment():
    """`---:` is a right-aligned numeric column; `:---` is a left-aligned label."""
    assert r"\begin{tabular}{lllr}" in markdown_to_latex(_MD, "tab:x")


def test_latex_abbreviation_touches_labels_and_never_numbers():
    """Table 17 only fits the text block with `-instruct` dropped. The guard is that
    abbreviation is a label rewrite: no digit may move."""
    plain = markdown_to_latex(_MD, "tab:x")
    short = markdown_to_latex(_MD, "tab:x", abbreviate=True)
    assert "qwen2.5-0.5b-instruct" in plain and "qwen2.5-0.5b-instruct" not in short
    assert "qwen2.5-0.5b" in short
    assert [c for c in plain if c.isdigit()] == [c for c in short if c.isdigit()]


def test_latex_refuses_a_ragged_table_rather_than_emitting_broken_tex():
    """A cell-count mismatch is silent in markdown and fatal in LaTeX; fail at the
    renderer, where the message names the row."""
    ragged = _MD.replace("| `test_ood` | -- |", "| `test_ood` |")
    with pytest.raises(ValueError, match="row 0 has 3 cells"):
        markdown_to_latex(ragged, "tab:x")


def test_the_slot_f1_rule_reaches_the_latex_unchanged():
    """The point of rendering LaTeX from the markdown rather than from the CSV a second
    time: a presentation rule added to `table17` cannot be forgotten in the PDF."""
    tex = markdown_to_latex(table17([_sb_row("test_ood")]), "tab:model-comparison",
                            abbreviate=True)
    row = next(l for l in tex.splitlines()
               if l.rstrip().endswith(chr(92) * 2) and r"\texttt{test\_ood}" in l)
    assert " -- & " in row, row


def test_list_of_tables_gets_the_heading_and_the_number_is_not_doubled():
    """The LoT entry is the markdown heading minus its "Table N:" (LaTeX numbers the
    float itself); a heading-only table must not print as "Table 4.1: Table 16: ..."."""
    tex = markdown_to_latex("### Table 16: Short title\n\n| a | b |\n| :--- | ---: |\n| x | 1 |\n", "tab:x")
    assert r"\caption[Short title]{Short title}" in tex
    assert "Table 16" not in tex


def test_latency_budget_judges_each_measure_against_its_table_6_line():
    from eval.tables import latency_budget, markdown_to_latex

    rows = [
        {"measure": "e2e_t0", "condition": "branch_b", "n": "300", "p50": "2100.4", "p95": "3121.5",
         "p99": "3500", "budget_p95_ms": "2500", "verdict": "MISSES"},
        {"measure": "a_offset", "condition": "loaded", "n": "78", "p50": "140", "p95": "149.9",
         "p99": "200", "budget_p95_ms": "150", "verdict": "MEETS"},
        {"measure": "e2e_speech_start", "condition": "branch_b", "n": "300", "p50": "4000",
         "p95": "9000", "p99": "10000", "budget_p95_ms": "", "verdict": ""},
        {"measure": "queue", "condition": "branch_b", "n": "300", "p50": "1", "p95": "2",
         "p99": "3", "budget_p95_ms": "", "verdict": ""},
    ]
    text = latency_budget(rows)
    assert "| **E2E from end of speech (T0; NFR-2)** | 300 | 2,100 | 3,122 | 3,500 | 2,500 | MISSES |" in text
    assert "| **Branch A from keyword offset, loaded (NFR-1)** | 78 | 140 | 150 | 200 | 150 | MEETS |" in text
    assert "| E2E from start of speech | 300 | 4,000 | 9,000 | 10,000 | -- | -- |" in text
    assert "queue" not in text.split("| Stage")[1]      # diagnostic rows stay in the analysis
    assert r"\label{tab:latency-budget}" in markdown_to_latex(text, "tab:latency-budget")
