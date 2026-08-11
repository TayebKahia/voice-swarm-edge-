"""Tests for the Table 33 renderer in `eval/tables.py`.

Table 33 is the one table that carries the fourth model, and it is the one whose
numbers nothing else cross-checks: Tables 17/18/19 are re-derived from Surface B
and guarded by `eval/mcnemar.py`'s provenance assertion, but Table 33 reads
`surface_a.csv` and the per-model configs and is otherwise on its own. These tests
are that guard.
"""

from __future__ import annotations

import pytest

from eval.tables import _model_meta, table33

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
