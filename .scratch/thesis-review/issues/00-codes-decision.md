# Issue 00: codes-decision

Status: resolved
Blocks: 01-08

## The question

The Master uses Exp-0 ... Exp-4 about 65 times and defines none of them; NFR-/FR- identifiers
appear about 100 times across both documents. Before any chapter is revised, decide one policy
per family, so every chapter is fixed the same way.

| Family | Option A: keep, define once | Option B: replace with names |
|---|---|---|
| RQ1-RQ3 | Stated in each Ch1 quote block (already) | -- (standard thesis practice; keep) |
| C1-C4 | Bold list in each Ch1 (already) | "the grammar-constrained schema", ... |
| Exp-0 ... Exp-4 | One experiments table in the Method chapter; each document codes only its own experiments | "the speaker-sensitivity experiment", "the multi-model benchmark", ...; the other document's experiments named in words |
| NFR-/FR- | Requirement tables (already in Master Ch3, Ingénieur Ch1) | Master: named criteria ("the 0.85 exact-match threshold"); Ingénieur keeps IDs |
| Surface A/B, Branch A/B | Bold definition at first use | "the reference surface" / "the deployed surface"; "the reflex path" / "the parse path" |

Recommendation: keep RQ and C (standard, already defined). Replace Exp-N with names in prose.
Keep requirement IDs in the Ingénieur (a requirements table with IDs is standard engineering
practice) but use named criteria in the Master, where IDs read as project bookkeeping.

## Answer
Decided 2026-09-23: the recommendation, as written.

| Family | Policy | Thesis-facing name |
|---|---|---|
| RQ1-RQ3 | Keep. Defined in each Ch1 quote block. | -- |
| C1-C4 | Keep. Defined in the bold list in each Ch1; a use before that list (e.g. Master Ch1 l.57) names the contribution in words or points forward ("the first contribution, below"). | -- |
| Exp-0 | Replace in prose. | the speaker-sensitivity experiment |
| Exp-1 | Replace in prose. | the multi-model benchmark |
| Exp-2 | Replace in prose. | the latency experiment |
| Exp-3 | Replace in prose. | the acoustic-robustness experiment |
| Exp-4 | Replace in prose. | the formation-control experiment |
| NFR-/FR- | Ingénieur keeps the IDs (defined in its requirement tables). Master uses named criteria ("the 0.85 exact-match threshold"). | -- |
| Surface A/B, Branch A/B | Replace. | the reference surface / the deployed surface; the reflex path / the parse path |

The names follow the Master Ch4 section titles where one exists, so the prose and the headings
agree. The other document's experiments are named in words, never coded. Every chapter issue
(01-08) applies this table; a chapter review that finds a code in prose reports it as D11.

### 2026-09-24 -- amended for the Ingenieur (issue 06, author's decision)

Reading the built Ingenieur PDF, the author found that requirement IDs were met in the prose before
the tables that define them, that the experiment names were never described, and that "C4" meant
nothing to a reader with no C1-C3 in the document. Two rows of the table above change for the
Ingenieur:

| Family | Policy, as amended |
|---|---|
| NFR-/FR- | **Both documents use named criteria.** The Ingenieur's tables name each criterion as the Master's `tab:requirements` does; a criterion in both documents has one name (End-to-end latency, Clean-audio recognition, Recognition in noise), and `ingenieur_ch1.py` checks that. |
| C1-C4 | The Master keeps C1-C3. The Ingenieur has one contribution and names it ("the contribution of this document"), with no number. |
| Exp-N | Unchanged (names), plus: each experiment is described in one sentence where it is first named. |
