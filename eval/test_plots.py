"""Tests for Figure 2.

A figure cannot be asserted pixel by pixel, and trying to would test matplotlib
rather than this project. What is tested is the part that can be silently wrong and
would reach a thesis looking fine: which configurations are on the Pareto frontier,
and whether a configuration with no Pi measurement is dropped from the plot instead
of being declared missing.
"""

from __future__ import annotations

from eval.plots import SPLIT, figure2, pareto_frontier


def point(em: float, p95: float, rss: float = 512.0) -> dict:
    return {"model": f"m{em}", "quant": "Q4_K_M", "em": em, "p95_ms": p95,
            "rss_mb": rss, "throttled": 1.0, "n_latency": 60}


class TestParetoFrontier:
    def test_a_slower_and_less_accurate_point_is_dominated(self):
        fast_good, slow_bad = point(0.93, 1700), point(0.91, 3200)
        assert pareto_frontier([fast_good, slow_bad]) == [fast_good]

    def test_a_faster_but_worse_point_stays_on_the_frontier(self):
        # This is the whole reason the figure is a Pareto plot: smollm2 is worse and
        # cheaper, which is a trade-off, not a loss.
        cheap, accurate = point(0.76, 1610), point(0.935, 1772)
        assert pareto_frontier([cheap, accurate]) == [cheap, accurate]

    def test_the_frontier_is_ordered_by_latency(self):
        points = [point(0.935, 1772), point(0.76, 1610)]
        assert [p["p95_ms"] for p in pareto_frontier(points)] == [1610, 1772]

    def test_equal_points_are_both_kept_rather_than_arbitrarily_broken(self):
        first, second = point(0.9, 1500), point(0.9, 1500)
        assert len(pareto_frontier([first, second])) == 2

    def test_a_single_point_is_its_own_frontier(self):
        only = point(0.5, 900)
        assert pareto_frontier([only]) == [only]

    def test_the_measured_configurations_put_llama_off_the_frontier(self):
        # The real Exp-1 numbers: llama-3.2-1b is both slower and less accurate than
        # qwen2.5-0.5b, so it cannot be the deployed choice on these two axes.
        llama, qwen, smollm2 = point(0.91, 3238.57, 1669.86), \
            point(0.935, 1771.54, 693.72), point(0.76, 1610.21, 561.67)
        frontier = pareto_frontier([llama, qwen, smollm2])
        assert llama not in frontier
        assert frontier == [smollm2, qwen]


class TestFigure2:
    def test_writes_a_vector_and_a_raster_copy(self, tmp_path, monkeypatch):
        import eval.plots as module
        monkeypatch.setattr(module, "FIGURE2", tmp_path / "figure2_pareto")
        written = figure2()
        assert [p.suffix for p in written] == [".pdf", ".png"]
        assert all(p.is_file() and p.stat().st_size > 0 for p in written)

    def test_unmeasured_configurations_are_carried_not_dropped(self):
        # Six artefacts exist and three have Pi latency; the figure must know about
        # all six so it can say which three it cannot place.
        from eval.plots import _points
        plottable, unmeasured = _points()
        assert len(plottable) + len(unmeasured) == 6
        assert {p["quant"] for p in unmeasured} == {"Q8_0"}
        assert all("p95_ms" not in p for p in unmeasured)

    def test_plots_the_recorded_speech_split(self):
        assert SPLIT == "test_golden"
