"""Measurement. Reads data/ and gguf/, writes results/.

    bench.py                 runs Exp-0 through Exp-4; one CSV per experiment
    norm.py                  canonicalisation shared by every accuracy metric
    stats.py                 McNemar + Bonferroni, ANOVA + Tukey HSD, percentiles
    plots.py                 every figure, regenerated from results/
    test_template_parity.py  compares token IDs between HF and llama.cpp

Two rules that the numbers depend on:

Six configurations are compared, so the comparison must be identical for all
six. Anything config-specific belongs in a config file, not in this code.

Greedy decoding with a fixed grammar is deterministic, so accuracy n is the
number of test items, while latency n is 200 timed runs. Different metrics carry
different n, and stats.py must not assume otherwise.
"""
