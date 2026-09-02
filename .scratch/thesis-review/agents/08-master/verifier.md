# Issue 08 -- Master whole-document pass -- verifier report

## 1. Header

Checked at `b1b884b` (working tree: `.scratch/thesis-review/reports/master_ch2.md` modified, report
only; no `thesis/` file differs from HEAD). Scope: the reviewer's one MAJOR (M-1; there is no
BLOCKER), plus the two spot-checks the task names (abstract comparison §5, headline-number table §4).

Files read: `.scratch/thesis-review/agents/08-master/reviewer.md` (in full);
`.scratch/thesis-review/agents/09-master-ch6/verifier.md` (for shape);
`thesis/master/frontmatter/{abstract,frabstract,arabstract}.tex` (in full);
`thesis/master/ch6_conclusion.tex` l.1-50, 60-70, 78-95; `ch1_introduction.tex` l.20-40, 125-145;
`ch4_results.tex` l.12-17, 124-128, 158-206, 216-220, 346-351, 386-392; `ch3_method.tex` l.280-296;
`ch5_discussion.tex` l.36-50, 62-65, 80-83, 204-217, 286-290; `ch2_related_work.tex` l.28-34;
`results/table33_iso_parameter.md`, `results/mcnemar.csv` (family-control row),
`results/exp2_latency_budget.md` l.1-4, `thesis/generated/table33_iso_parameter.tex` l.19;
the Comments of `.scratch/thesis-review/issues/03-master-ch3.md` (l.90, 168-169, 216-222),
`04-master-ch4.md` (l.81), `09-master-ch6.md` (l.122-176); `tools/review/*.py` (grep);
`docs/agents/thesis-chapter-review.md` l.172-179; `git show ad09efb`, `afc692f`, `9362cd0`.

Review only: nothing edited except this file; no build run; no commit.

## 2. Summary

| ID | Sev (reviewer) | Verdict | Sev (verified) | Evidence | Fix judgement / corrected fix |
|---|---|---|---|---|---|
| M-1 | MAJOR | CONFIRMED | MAJOR (borders BLOCKER: Ch3:287-288 negates the claim in terms; kept MAJOR for consistency with issue 03 V20 and issue 04 A8, which rated the same claim MAJOR in Ch1 and Ch4) | abstract:19-20 "separates model family / from size"; frabstract:20 "sépare l'effet de la famille de modèles de celui de la taille"; arabstract:20 "فيفصل أثر عائلة النموذج عن أثر الحجم". Against: ch4:176-177 "measure a family difference at about 0.5~B parameters; they do not express it as a share of a size effect"; ch3:287-288 "It does not remove family from the size comparison"; ch6:87-88 "measures a family difference at fixed size and does not express it as a share of a size effect"; ch1:137-138 "measures a model-family difference at fixed size". Ch1 dropped the exact wording in `ad09efb` (issue 03 V20); issue 09's abstract fix (`afc692f`) edited the same sentence but only its "measured on the board" clause and left the fragment standing | Fix correct and complete as proposed. No new number, no hedge, not stronger than Ch1:137-138 / Ch6:87 (verbatim), no script anchor (no `tools/review/*.py` reads the frontmatter). FR and AR faithful. The three abstract lines are the only remaining occurrences of the claim in the Master |
| NEW-n | -- | none | -- | Spot-checks §5 (abstracts) and §4 (headline numbers) found no dropped or strengthened qualifier and no mismatched number | -- |

## 3. Reasoning per finding

### M-1 -- CONFIRMED, MAJOR

The text as it stands:

- `abstract.tex:18-20`: "Four models are fine-tuned under one recipe; three are quantised at two
  levels, their Q4\_K\_M artefacts are timed on the board, and the fourth, matched in size to one of
  them, separates model family / from size."
- `frabstract.tex:19-20`: "et le quatrième, de taille appariée à l'un / d'eux, sépare l'effet de la
  famille de modèles de celui de la taille."
- `arabstract.tex:19-20`: "أما الرابع، / المماثل في الحجم لأحدها، فيفصل أثر عائلة النموذج عن أثر الحجم."
  ("as for the fourth, matched in size to one of them, it separates the effect of model family from
  the effect of size").

What the chapters say:

- `ch4_results.tex:174-177`: "The 15.0~pp span from SmolLM2-360M at 0.775 to Llama-3.2-1B at 0.925
  covers the full 3.4$\times$ range of size, but its endpoints also differ in family, and no family
  appears at two sizes. These data therefore measure a family difference at about 0.5~B parameters;
  they do not express it as a share of a size effect."
- `ch3_method.tex:286-289`: "Holding scale approximately fixed across that pair measures a family
  difference at one size. It does not remove family from the size comparison, whose endpoints,
  SmolLM2-360M and Llama-3.2-1B, are two further families."
- `ch6_conclusion.tex:86-88`: "Among the three deployed models, size and family vary together, so the
  comparison measures a family difference at fixed size and does not express it as a share of a size
  effect."
- `ch1_introduction.tex:137-138`: "a parameter-matched control that measures a model-family
  difference at fixed size".

Attempted disproof 1: "matched in size to one of them" already restricts the sentence to one pair,
so "separates model family from size" is shorthand for "holds size fixed while family varies".
This fails. "Separates A from B" asserts that the two effects have been decomposed, which is the
reading Ch3:287-288 ("does not remove family from the size comparison") and Ch4:177 ("do not
express it as a share of a size effect") deny in terms. The document itself judged that shorthand
insufficient twice: issue 03 V20 (Comments l.90: "one pair estimates family at ~0.5 B; the size
span's endpoints are two other families") and issue 04 A8 (Comments l.81: "drop the ratio and
'separates them'").

Attempted disproof 2: the abstract was drafted from Ch6 (commit `9362cd0`: "Drafted from Ch6, not
Ch1"), so the sentence could inherit a Ch6 claim that has since changed. This fails. The Ch6 family
paragraph said "measures a family difference at fixed size and does not express it as a share of a
size effect" before and after issue 09 (issue 09 verifier l.102-103 quotes l.79-80 in that form),
and the method paragraph of the abstract derives from Ch3 (reviewer §5, A4-A6), not Ch6. The
wording was written fresh into the abstract on 2026-08-31 (`9362cd0:frontmatter/abstract.tex:19`
"and measured on the board, and the fourth, matched in size to one of them, separates model
family"), five days after `ad09efb` (2026-08-26) had removed it from Ch1.

Attempted disproof 3: issue 09's NEW-1 re-derived the abstracts, so the sentence has already been
reviewed and accepted. This fails. `git show afc692f -- abstract.tex` changes l.18-19 from "three
are quantised at two levels / and measured on the board, and the fourth, matched in size to one of
them, separates model family" to "three are quantised at two levels, / their Q4\_K\_M artefacts are
timed on the board, and the fourth, matched in size to one of them, separates model family": the
edit touched the "measured on the board" clause only (issue 09 Comments l.157-159 say exactly
that) and the "separates" fragment passed through untouched. Issue 09's NEW-1 concerned M1-M3 of
§6.1 (l.151-155), and its verifier's abstract check (issue 09 verifier l.139-149) lists only those
three. The reviewer's account of how the overclaim survived is accurate.

Confirmation of the Ch1 history the reviewer relies on: `git show ad09efb --
thesis/master/ch1_introduction.tex` contains

```
-separates model family from model size, the quantisation delta, and the grammar ablation, with
+measures a model-family difference at fixed size, the quantisation delta, and the grammar ablation, with
```

and issue 03 Comments l.168-169 record it: "Ch1 l.136-137 'a parameter-matched control that
separates model family from model size' -> 'measures a model-family difference at fixed size' (V20
consistency; no other session on Ch1)". The reviewer cites "l.416-417 of the Comments"; the line
numbers in the file as it stands are 168-169 (l.405-425 of the file are empty). The content is as
quoted.

Severity. Template A (docs/agents/thesis-chapter-review.md l.174-176) puts "overclaim" at MAJOR and
"contradiction with another chapter" at BLOCKER. The abstract's sentence is an overclaim of a
result the chapters state more narrowly, and Ch3:287-288 negates it in so many words, so a BLOCKER
reading is available. I keep MAJOR because the identical claim was rated MAJOR when it stood in Ch1
(V20) and Ch4 (A8), and because the claim names no number that the evidence refutes. It must be
fixed before submission either way; the abstract is the sentence a jury reads first.

Completeness of the fix (task step 4). `grep -rn -i "separat|family from size|sépare|famille|الحجم|عائلة|fixed size|taille fix" thesis/master/` (excluding `tables/`) returns:

- the three abstract lines above (the defect);
- the correct wording at ch1:138, ch3:289 ("whether a family difference at fixed size is of the same
  order"), ch6:87;
- "separate(s)" in unrelated senses: ch6:71 "does not separate that cost from zero"; ch4:188 and
  ch5:204 "Three (further) differences separate H2O-Danube3-500M from"; ch3:362, ch4:191, ch5:206
  "separate session"; ch4:269, 282, 285-286 (statistical separation of models); ch3:411, 418, 450,
  464, 524, 531; ch2:123, 137; ch3:216; ch5:44, 135-136, 170, 175, 185;
- "famille"/"عائلة" otherwise only for template families (frabstract:17, arabstract:18).

Ch2's only sentence on the control (ch2:30-32, "The fourth, a parameter-matched control, is
reported at fp16 only") makes no family/size claim. So the three abstract lines are the only
remaining occurrences, and the reviewer's fix, applied to all three, closes the finding.

## 4. Fix checks

| ID | new number? | hedging word? | stronger than source? | script anchor touched? | FR/AR faithful? |
|---|---|---|---|---|---|
| M-1 | No: the EN/FR/AR replacements contain no digit ("measures a model-family difference at fixed size" / "mesure une différence entre familles de modèles à taille fixée" / "فيقيس فرقًا بين عائلات النماذج عند حجم ثابت") | No: none of may/might/could/perhaps/possibly/likely/suggest/appear/seem or inflections (checked against the regex `master_ch6.py:140`); FR "mesure" and AR "يقيس" are plain indicatives; no "pourrait/semble/peut" and no "قد/ربما/يبدو" | No: the EN is Ch1:137-138 verbatim ("measures a model-family difference at fixed size") and matches Ch6:87 ("measures a family difference at fixed size"). Ch4:176 says "at about 0.5~B parameters" and ch4:166-167 "approximately fixed"; "fixed size" is the wording Ch1 and Ch6 already use for it, and the abstract's own "matched in size to one of them" carries the approximation | No: `grep -rn -i "frontmatter\|abstract\|separates\|matched in size\|model-family\|fixed size" tools/review/*.py` finds nothing (the only "abstract" hit is `selftest.py`'s unrelated file table, and `lib.py` has none). No script reads the three abstract files; `master_ch1.py`'s anchors (l.15-64) do not include the Ch1 outline wording, and the fix does not change Ch1 | FR: "et le quatrième, de taille appariée à l'un d'eux, mesure une différence entre familles de modèles à taille fixée" keeps the existing head ("le quatrième, de taille appariée à l'un d'eux") and replaces only the verb phrase; "une différence entre familles de modèles" = "a model-family difference", "à taille fixée" = "at fixed size". Faithful. AR: "أما الرابع، المماثل في الحجم لأحدها، فيقيس فرقًا بين عائلات النماذج عند حجم ثابت" keeps the existing head ("أما الرابع، المماثل في الحجم لأحدها،") and the "أما ... فـ" construction; "يقيس فرقًا بين عائلات النماذج" = "measures a difference between model families", "عند حجم ثابت" = "at a fixed size". No number in source or target; no negation in source or target (the English fix has none either); the qualifier structure (matched in size -> at fixed size) matches. Faithful on the checks in scope; native-speaker check out of scope |

One typesetting note, not a check failure: `abstract.tex:19` is already an overlong source line
(the NEW-1 edit appended to it). Rewrapping l.19-20 when applying the fix is safe, since nothing
anchors on the abstracts.

## 5. Spot-check results

### 5.1 Abstracts against each other and against Ch6 §6.1 (ch6:17-44)

Numbers, in order of appearance, read from the files:

| Abstract | Numbers (file:line) |
|---|---|
| EN `abstract.tex` | 0.36--1.2~B (l.11); 200 (l.17); 0.935 (l.25); 17.5 (l.25); 2{,}500 (l.28); 622 (l.28); 3{,}122 (l.29) |
| FR `frabstract.tex` | 0,36 à 1,2 (l.9-10); 200 (l.18); 0,935 (l.26); 17,5 (l.27); 622 (l.30); 2\,500 (l.31); 3\,122 (l.32) |
| AR `arabstract.tex` | 0.36, 1.2 (l.11); 200 (l.18); 0.935 (l.27); 17.5 (l.29); 2{,}500 (l.32); 622 (l.32); 3{,}122 (l.33) |

Identical sets in the three languages (the FR sentence orders 622 before 2 500; same values). Every
one appears in Ch6 §6.1 with the same value: 0.36--1.2 (ch6:21), 0.935 (ch6:23), 17.5 (ch6:26),
2{,}500 and 622 (ch6:32-33), 3{,}122 (ch6:33); 200 is Ch3's golden-set size (ch3:160, 201). Numbers
in §6.1 that no abstract quotes: 894, 1{,}072 (l.25), 0.760 (l.26), 1.24~B, 0.910, 2{,}282
(l.28-29), 25\% (l.33), 0.68 and 2.5~GiB (l.34), 0.0000--0.1579, 0.70, 0.1867--0.3933, 0.05
(l.39-40). Omissions, not changes.

The six qualifiers:

| Qualifier (Ch6 §6.1) | Attached to | EN | FR | AR | Verdict |
|---|---|---|---|---|---|
| "significant" (ch6:26 "a gap significant at the corrected $\alpha$") | 17.5~pp | l.25 "a significant difference" | l.27-28 "une différence significative" | l.29 "وهو فرق دالّ إحصائيًا" | present x3 |
| "not established" (ch6:28 "a difference ... that the test does not establish") | Llama's 0.910 (number not in the abstracts) | l.26 "its lower accuracy on the golden set is not statistically established" | l.28-29 "sa précision inférieure sur le jeu de référence n'est pas statistiquement établie" | l.30 "ودقته الأدنى على المجموعة المرجعية غير مُثبتة إحصائيًا" | present x3, with "on the golden set" kept x3 |
| "exploratory" (ch6:83, in §6.2, not §6.1) | 6.5~pp, $p = 0.0023$ | absent | absent | absent | legitimately absent: neither number is in any abstract |
| "re-baselined" (ch6:31, 33) | 622, 3{,}122 | l.27 "re-baselined constraints", l.28 "re-baselined to the measured 3{,}122~ms" | l.29-30 "contraintes redéfinies d'après les mesures", l.31-32 "redéfini à la valeur mesurée de 3\,122~ms" | l.31 "قيود أُعيد ضبطها على القيم المقيسة", l.33 "ويُعاد ضبط هذه الميزانية على القيمة المقيسة" | present x3 (FR/AR render it descriptively, as `9362cd0`'s message records, so it cannot read as "met") |
| "language-model process only" (ch6:34) | 0.68~GiB | absent | absent | absent | legitimately absent: 0.68 is in no abstract |
| "reference text" (ch6:23 "scored on reference text") | 0.935 | l.25 "scored on reference text" | l.26-27 "évaluée sur le texte de référence des commandes" | l.27-28 "محسوبةً على النص المرجعي للأوامر" | present x3 |

Also present x3 and matching ch6:20-23: "Among the three models timed on the board" (EN l.23; FR
l.24 "Parmi les trois modèles chronométrés sur la carte"; AR l.24 "من بين النماذج الثلاثة التي قيس
زمنها على الجهاز") and "the trade-off at Q4\_K\_M" (EN l.23; FR l.24; AR l.24); and ch6:40-42's "one
tendency" sentence (EN l.30; FR l.33 "une même tendance"; AR l.34 "نزعةً واحدة"). The abstracts'
"emits a well-formed command rather than declining" renders Ch6's "rather than \texttt{unknown}"
without the token name; same claim.

No NEW finding from this spot-check. The reviewer's §5 is right in every row I checked, and A5
(M-1) is the only row where an abstract outruns the chapters.

### 5.2 Headline-number occurrences (reviewer §4)

Greps over `thesis/master/ch*.tex frontmatter/*.tex`:

| Value | Pattern | Found | Reviewer's list | Qualifier at every occurrence |
|---|---|---|---|---|
| 0.935 | `0\.935\|0,935` | ch4:78, 172, 371, 374; ch5:43, 59, 289; ch6:23, 66, 81; abstract:25; frabstract:26; arabstract:27 | same, minus ch4:172 | ch4:172 is the family-control sentence, listed by the reviewer under the 6.5~pp row (ch4:171-173); it carries "exact McNemar $p = 0.0023$, an exploratory test" in the sentence and "reported on the reference surface only" at ch4:193. Harmless omission from the 0.935 row; the value is identical. Elsewhere: ch4:14-16 declares every accuracy figure of §4.2-§4.6 "measured on reference text"; ch4:388 "The selection is made against reference-text accuracy" sits in §4.7 with ch4:371, 374; ch5:43 "At FP16", ch5:289 "on reference text"; ch6:23 "scored on reference text", ch6:81 "on the reference surface"; ch6:66 is in the same chapter, same split, after l.23. Abstracts x3 carry the qualifier |
| 622 | `622` | ch4:350, 391; ch5:64; ch6:33; abstract:28; frabstract:30; arabstract:32 | same | ch4:350 "(25\%) above the budget", owner named at ch4:348; ch4:391 "as specified"; ch5:63-64 "re-baselined constraints ... as specified"; ch6:32-33 "as specified ... re-baselined"; abstracts x3 "re-baselined". "(25\%)" at ch4:350, ch5:64, ch6:33 only; the abstracts omit it (omission) |
| 3{,}122 | `3{,}122\|3,122\|3122\|3\\,122` | ch4:349, 361; ch6:33; abstract:29; frabstract:32; arabstract:33 | same (plus ch3:480 for $n = 226$ only, which the grep for `226` confirms: ch3:480, ch4:349) | ch4:349 with $n = 226$ and the owner; ch4:361, ch6:33 and abstracts x3 "re-baselined to the measured". The thermal state is absent at ch4:349 and supplied at ch5:81-82 ("that figure was measured on the cooled board") and `results/exp2_latency_budget.md:3` ("Raspberry Pi 5, cooled, governor `performance`"): this is the reviewer's MIN-1, and MINOR is the right level, since the qualifier of record ("re-baselined") is intact everywhere and the missing item is a document-wide reporting promise (ch1:35-37), not a qualifier the source chapter attaches to this number |
| 0.68 | `0\.68\b\|0,68` | ch4:126; ch6:34 | same | ch4:126 "Peak resident memory of the language-model process"; ch6:34 "for the language-model process only". Not in any abstract |
| 6.5 | `6\.5\b\|6,5` | ch4:171; ch5:40, 209; ch6:80 | same, plus the table33 note (`generated/table33_iso_parameter.tex:19`, which is `\input` at ch4:169) | ch4:171-173 "exploratory test", `test\_golden`, with ch4:193 "reference surface only"; the table note itself says "exact McNemar p = 0.0023" and "under an identical three-epoch budget, not one of capability" but not "exploratory": that word is in the sentence introducing the table (ch4:173), which meets the reviewer's "immediate sentence/paragraph" rule; ch5:40 "at FP16" with the convergence caveat at ch5:44-47 and the declared differences and "exploratory exact McNemar test" at ch5:209-216; ch6:80-88 carries all of them. Not in any abstract |

No number differs between occurrences, and no occurrence drops or strengthens the qualifier its
source attaches. No NEW finding from this spot-check.

## 6. For other issues

- Nothing for issue 10 from this verification: M-1 lives in the Master frontmatter only, and the
  Ingénieur has no abstract yet to inherit it. When the Ingénieur abstracts are drafted (B12, its
  side), the same rule applies: the method paragraph must be checked against the chapters it
  derives from, not only the verdict paragraph against Ch6. Issue 09's NEW-1 and this M-1 are the
  same failure mode twice (a fixed claim surviving in a summary that was re-derived only in part).
- Issue 08 reviewer's line citation "Comments of issue 03, l.416-417" should read l.168-169; the
  file has no text at l.405-425. Cosmetic.
- MIN-1 (thermal state for the three Ingénieur-sourced timing figures in Ch4) is correctly MINOR;
  the fix the reviewer proposes relies on `results/exp2_latency_budget.md:3`, which does say
  "cooled". Not re-verified beyond that.
