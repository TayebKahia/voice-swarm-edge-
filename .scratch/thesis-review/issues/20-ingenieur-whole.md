# Issue 20: whole-document pass, Ingénieur (seven chapters, two parts)

Status: open
Blocked by: 10 (resolved, on the six-chapter Ingénieur), 18, 19
Documents: thesis/main_ingenieur.tex

## What

Template B of `docs/agents/thesis-chapter-review.md`, repeated on the restructured Ingénieur.
Issue 10 ran it on 2026-09-24 against the six-chapter, 77-page document. Since then (26 Sep):
prd.md §3.1 rewritten to seven chapters in two parts (Part I Background and state of the art;
Part II Contribution; the closing chapter outside the parts), as the Master has had since 26 Sep;
a new Background (Ch2, issue 18); the State of the art rebuilt with four comparison tables and
Research gaps G1-G3 (Ch3, issue 19); the speech-component justification moved from the old Ch2 to
Architecture (Ch4, sec:component-choices); Ch1's structure paragraph rewritten for the parts;
Ch7's ref to the gap re-pointed. The three abstracts are unchanged since 24 Sep. 91 pages.

What this pass must see that the chapter reviews could not: the golden thread now runs
Ch1 (RQ2, RQ3, C4) -> Ch3 §3.5 (G1-G3) -> Ch4 (designed) -> Ch5 (built) -> Ch6 (measured) ->
Ch7 (answered); Background definitions used with one meaning by Ch3-Ch7; the abstracts against the
new chapter set; the List of Acronyms after the Background's new `\gls` uses (JSON, UDP, LoRA,
GGUF, GBNF now first used in Ch2); every printed bibliography entry cited; write-once against the
Master as it stands (Background vs Background especially). Known and left as deposited (STATE.md,
24 Sep): Ch5's "not built" statements about the demonstration chain, which cba9c1e has since built;
the pass reports them but they are the author's decision.

## Agents

One reviewer + verifier, as in issues 10 and 17. Not split by dimension.

## Comments
