# Issue 20 -- verifier report on the whole-document review of the Ingénieur (Template B, seven chapters in two parts)

Reviewed: `agents/20-ingenieur-whole/reviewer.md` (all 18 findings: 1 MAJOR, 11 MINOR, 6 NIT) against the working tree at HEAD `398b35a` (no `thesis/` file modified; working tree clean). Rules: `docs/agents/thesis-chapter-review.md` §2 severities. Author decisions checked: issues 10, 13, 14, 18, 19 and `.scratch/sprint-pfe/STATE.md`.

## 1. Summary table

| ID | Sev reported | Verdict | Sev verified | Evidence | Fix judgement / corrected fix |
|---|---|---|---|---|---|
| MAJOR-1 | MAJOR | CONFIRMED | MAJOR | `thesis/ingenieur/ch3_state_of_the_art.tex:448-452` & `ch6_conclusion.tex:397-406`. G2 claims over MIRA that no system "holds a stop to a latency budget of its own". However, reflex latency misses its 150 ms budget by 395 ms (545/547 ms p95), and measured from keyword onset (965 ms median in `exp2_latency_budget.tex:26`) is slower than MIRA's 466 ms median from speech onset (`ch3:222, 244-245, 447-448`). Ch7 still claims the path "is held to" the budget. | Reviewer's fix confirmed and anchor-safe: (a) soften "held to" to "specified and measured against" in Ch7 and Ch3; (b) explain that what the reflex adds over MIRA is a restricted two-command trigger by a derived rule and a localized budget miss, not raw speed. `965` and `466` are both present in generated tables / earlier chapters, so `ingenieur_ch6.py` number inheritance passes. |
| MINOR-1 | MINOR | CONFIRMED | MINOR | `ch3_state_of_the_art.tex:337-343` and `ch3_architecture.tex:543-544, 555-557, 565-568`. Three sentences describing open components (openWakeWord, Silero VAD, whisper.cpp) are verbatim identical across Ch3 and Ch4. | Apply Fix A: keep Ch3's paragraph and its four anchors (`ingenieur_ch2.py:97-98`); in Ch4 replace the three restatements with concise cross-references to Section~\ref{sec:speech-components}. `ingenieur_ch3.py` has no anchors on these sentences. Anchor-safe. |
| MINOR-2 | MINOR | CONFIRMED | MINOR | `frontmatter/abstract.tex:26-27` (fr:68-69, ar:29); `ch5_validation.tex:420-421`. Abstracts attribute the 540 ms miss solely to "the spotter's delay... rather than in computation", whereas Ch6 §6.1 (`ch5_validation.tex:98-100`) and Ch7 (`ch6_conclusion.tex:253-254, 368-369`) attribute it jointly to spotter decision delay, 80 ms frame quantisation, and anchor error. | Correct as proposed across EN, FR, AR abstracts and Ch6 summary sentence. |
| MINOR-3 | MINOR | CONFIRMED | MINOR | `frontmatter/abstract.tex:19-20` (fr:60-61, ar:21-22). "a rejection becomes a hold" / "tout rejet se traduit par un maintien" / "ويتحوّل كل رفض إلى تثبيت". Table 4.2 (`tab:legality-matrix`) and `swarm/fsm.py` show that in LANDED, LANDING, and ABORTED, an illegal command is a logged no-op; it transitions to HOVER only in TAKING_OFF and FLYING. | Correct as proposed: "and a rejection never becomes motion: in flight it becomes a hold" (FR: "aucun rejet ne produit de mouvement : en vol, il se traduit par un maintien"; AR: "ولا يُنتج أيّ رفضٍ حركةً: ففي الطيران يتحوّل إلى تثبيت"). |
| MINOR-4 | MINOR | CONFIRMED | MINOR | `ch1_introduction.tex:139`; `ch5_validation.tex:119-120`; `gen/requirements_summary.tex:13`. NFR-14 specifies the sequence-number ordering rule, but verification in Ch6 / Table 6.3 only cites "78/78 decodes cancelled" (the optimization); the ordering rule was never triggered during trials and is verified by unit tests in Ch5 (`ch4_implementation.tex:259-261`). | Confirmed. Add sentence after `ch5_validation.tex:120` noting the ordering rule is verified by consumer unit tests. In `eval/tables.py` update Table 6.3 cell. |
| MINOR-5 | MINOR | CONFIRMED | MINOR | `ch6_conclusion.tex:361-366`. Stage allowances are ceilings, not additive partitions (percentiles do not sum). "allocations" and "account for the 622 ms shortfall" treat them as an additive decomposition. | Correct as written: change "allocations" to "allowances" and "Two stages account for the 622 ms shortfall" to "The shortfall lies in two stages: ...". Anchor-safe. |
| MINOR-6 | MINOR | CONFIRMED | MINOR | `ch3_state_of_the_art.tex:395-408`. RQ3 (noise robustness, safe degradation, formation quality) has no literature anchor or gap in Ch3 Research gaps or Synthesis. | Confirmed. One sentence added to the end of Synthesis referencing Contreras et al. and explaining RQ2/RQ3 measure these dimensions. `contreras2020` is already cited in Section 3.1, so `ingenieur_ch2.py` rule "Research gaps introduces no source the theme sections did not review" passes. |
| MINOR-7 | MINOR | CONFIRMED | MINOR | `ch2_background.tex:348-350` (List of Acronyms). GBNF and GGUF expand to include "GGML", but GGML is never defined in the List of Acronyms. | Confirmed. Add `\glsadd{ggml}` at `ch2_background.tex:348`, mirroring the Master fix (`master/ch1:110`). |
| MINOR-8 | MINOR | CONFIRMED | MINOR | `ch5_validation.tex:259-261`. The Ingénieur never specifies what "correct" means for a dispatched command, nor cites the Master's canonical comparator (`canon()`), despite the Master stating that the Ingénieur cites it (`master/ch3_method.tex:547-548`). | Confirmed. Add sentence to `ch5_validation.tex:259-261` citing the Master's canonical comparison. Anchor-safe. |
| MINOR-9 | MINOR | CONFIRMED | MINOR | `ch6_conclusion.tex:160-162`. Trajectory convergence is attributed to the potential field, whereas Ch5 states the formation PID term drives convergence (the field is purely repulsive under 1.5 m). | Confirmed. Rephrase to: "therefore evaluate the controller -- the formation law, the potential field and the flocking terms -- under idealised kinematics...". Preserves convergence medians anchored in `ingenieur_ch6.py:79-81`. |
| MINOR-10 | MINOR | CONFIRMED | MINOR | `ch6_conclusion.tex:286-291`. Suggesting a repulsive potential field as the replacement for the geometric clamp reverses the thesis argument that potential fields are soft mechanisms that can be outrun. | Confirmed. Rephrase to note collision avoidance must act on acceleration/velocity with kinematic feasibility constraints, since the existing potential field is a soft mechanism whose failure modes are known (`\cite{koren1991}`). Preserves `\cite{koren1991}` anchor. |
| MINOR-11 | MINOR | CONFIRMED (Master side) | MINOR | `master/ch2_background.tex:339-346`. Master restates speech pipeline details owned by the Ingénieur. | CONFIRMED on text, but OUT OF SCOPE for Ingénieur review. Master review closed in Issue 17. Author decision whether to apply optional one-sentence trim to Master. |
| MINOR-12 | MINOR | CONFIRMED | MINOR | `ch5_validation.tex:284-286`. The 10 dB error breakdown lists 19 intent + 30 slot + 12 parser + 20 splits = 81 failures, omitting the 1 perfect transcript that was misparsed (total 82). | Confirmed against `results/exp3_pi_analysis.md:97`. Append: ", and one utterance transcribed perfectly was misparsed." Anchor-safe. |
| NIT-1 | NIT | CONFIRMED | NIT | `ch2_background.tex:340`; `ch4_implementation.tex:216`. Missing `\emph{...}` around Mémoire de Master. | Correct as proposed. |
| NIT-2 | NIT | CONFIRMED | NIT | `ch3_state_of_the_art.tex:406-407`. Gaps ordering claim does not match Ch4 closer section order. | Correct as proposed: "stated below, each with the part of the design of Chapter~\ref{chap:architecture} that closes it,". |
| NIT-3 | NIT | CONFIRMED | NIT | `ch2_background.tex:345`. "a SLM" -> "an \gls{slm}". | Correct as proposed. |
| NIT-4 | NIT | CONFIRMED | NIT | `ch1_introduction.tex:183, 201`. "from end-of-speech" -> "from the end of speech". | Correct as proposed. |
| NIT-5 | NIT | CONFIRMED | NIT | `ch3_architecture.tex:458-460`. "the deployment constraint" in Ch4 -> "deployment constraints". | Correct as proposed. |
| NIT-6 | NIT | CONFIRMED | NIT | `ch1_introduction.tex:66-91`. Implicit out-of-scope in Ch1. | Confirmed. Add explicit scoping sentence after line 91: "Physical flight, vision input and languages other than English are outside the scope of both documents." |

---

## 2. Detailed Reasoning per Finding

### MAJOR-1 -- Gap G2 Latency Claim vs. Conceded Prior Art (MIRA)
- **Reviewer's point**: Gap G2 (`ch3:448-452`) concedes MIRA's preemption and claims only that "No reviewed system, therefore, holds a stop to a latency budget of its own. The first clause of the contribution closes this gap". However, the reflex path misses its 150 ms budget by 395 ms (545/547 ms p95), and measured from keyword onset (965 ms median in Table 6.1 / `exp2_latency_budget.tex:26`), it is slower than MIRA's 466 ms median from speech onset (`ch3:222, 244-245, 447-448`). Ch7 (`ch6_conclusion.tex:399-400`) still refers to "the latency budget of its own that the path is held to".
- **Verification**: Verified. A jury will ask what remains of G2's claim if MIRA is already faster and the 150 ms budget is missed. Ch3 already concedes preemption to MIRA and promises measurement, but the wording "holds a stop to a latency budget of its own" and Ch7's "the path is held to" overclaim.
- **Anchor check**:
  - `ingenieur_ch2.py:69-70` checks `closers = {"G2": ("sec:dual-path", "sec:latency-budget")}`. Both labels are retained.
  - `ingenieur_ch6.py:154-165` checks that no new measurement is introduced in Ch6. `965` is present in `thesis/generated/exp2_latency_budget.tex:26` and `466` is present in `ch3_state_of_the_art.tex:222, 244, 369, 447`. Neither is a new number.
- **Fix**: Apply reviewer's parts (a), (b), and (c).

### MINOR-1 -- Duplication across Ch3 and Ch4
- **Verification**: Verified. `ch3_state_of_the_art.tex:337-344` and `ch3_architecture.tex:543-544, 555-557, 565-568` share verbatim sentences describing openWakeWord, Silero VAD, and whisper.cpp.
- **Anchor check**:
  - `ingenieur_ch2.py:97-98` anchors `("680{,}000 hours", "whisper")`, `("39 million", "whisper")`, `("80~ms frame", "oww")`, `("32~ms windows", "silero")` in Ch3.
  - `ingenieur_ch3.py` has no anchors on lines 540-575 of `ch3_architecture.tex`.
- **Fix**: Keep Ch3 intact (Fix A). In Ch4, replace the three restatements with concise references back to Section~\ref{sec:speech-components}. All script anchors are preserved.

### MINOR-2 & MINOR-3 -- Abstracts Wording
- **Verification**:
  - MINOR-2: Verified. The 540 ms miss is attributed in Ch6 §6.1 to decision delay + quantisation into 80 ms frames + anchor error. The abstracts' "in the spotter's delay... rather than in computation" oversimplifies.
  - MINOR-3: Verified. In `LANDED`, `LANDING`, and `ABORTED`, illegal commands do not transition to `HOVER` (they are no-ops). Only active flight states transition to `HOVER`.
- **Fix**: Apply the corrected wording across English, French, and Arabic abstracts.

### MINOR-4 -- Preemption Verification Scope
- **Verification**: Verified. Preemption has two components: cancellation of the in-flight language model decode (an optimization) and the sequence-number ordering rule (the correctness guarantee). Table 6.3 and Ch6 §6.1 only cite the 78/78 cancellations. Adding a note that the ordering rule is verified by unit tests in Ch5 clarifies the evidence.
- **Fix**: Add sentence to `ch5_validation.tex:120` and update `eval/tables.py` for Table 6.3.

### MINOR-5 -- Ch7 Shortfall Wording
- **Verification**: Verified. 751 - 250 = 501 ms; 1449 - 1200 = 249 ms; 501 + 249 = 750 ms != 622 ms. Decode was also 185 ms under allowance. Percentiles do not add linearly. Saying two stages "account for the 622 ms shortfall" is inaccurate.
- **Fix**: Change "allocations" to "allowances" and "account for" to "The shortfall lies in two stages: ...".

### MINOR-6 -- RQ3 Literature Synthesis
- **Verification**: Verified. RQ3 has no literature motivation in Ch3. Contreras et al. 2020 (`contreras2020`) evaluated ASR under propeller noise. Adding one sentence at the end of Synthesis provides the anchor without introducing a new citation.
- **Anchor check**: `contreras2020` is cited in Section 3.1, so `new = cites(gaps) - cites(themes_text)` in `ingenieur_ch2.py` remains empty.

### MINOR-7 -- GGML Acronym
- **Verification**: Verified. GGML is printed inside GBNF and GGUF definitions but not defined itself.
- **Fix**: Add `\glsadd{ggml}` in `ch2_background.tex:348`.

### MINOR-8 -- CRR Comparator Cross-Reference
- **Verification**: Verified. The Master explicitly claims that the Ingénieur cites its comparator and canonical form (`master/ch3_method.tex:547-548`). The Ingénieur lacked this cross-reference.
- **Fix**: Add sentence to `ch5_validation.tex:259-261`.

### MINOR-9 & MINOR-10 -- Ch7 Control Mechanisms
- **Verification**:
  - MINOR-9: Verified. Convergence is driven by the formation PID law tracking assigned slots, not the potential field (which only repels < 1.5 m).
  - MINOR-10: Verified. Proposing a potential field as a replacement for the hard clamp reverses the thesis argument that potential fields are soft mechanisms that can be outrun.
- **Fix**: Rephrase both passages in Ch7 while preserving the `\cite{koren1991}` anchor and convergence medians.

### MINOR-11 -- Master Background Redundancy
- **Verification**: Verified. Master Ch2 lines 339-346 restates speech pipeline details. However, Master review was completed in Issue 17. Judged: leave as author's optional choice; do not alter Master during the Ingénieur review.

### MINOR-12 -- 10 dB Failure Count
- **Verification**: Verified. 19 + 30 + 12 + 20 = 81 != 82. One utterance transcribed perfectly was misparsed (`results/exp3_pi_analysis.md:97`).
- **Fix**: Append ", and one utterance transcribed perfectly was misparsed." to `ch5_validation.tex:286`.

### NITs 1 to 6
- All 6 NITs verified and confirmed.

---

## 3. Resolution of Reviewer's UNVERIFIED Items

1. **Arabic abstract wording**: The proposed Arabic fixes for MINOR-2 and MINOR-3 were checked against grammatical usage:
   - MINOR-2: "في تأخير قرار الكاشف وتقطيع الأطر وخطأ التوقيت، لا في حساب اللوحة"
   - MINOR-3: "ولا يُنتج أيّ رفضٍ حركةً: ففي الطيران يتحوّل إلى تثبيت."
2. **Silence claim in MINOR-6**: Checked against Tables 3.1–3.4. None of the reviewed systems reports failure direction or formation quality under noise.
3. **Speed slot on `move` command (ch7:192)**: Checked `schema/schema.py:160` and `ENVELOPE["speed"] = (0.2, 2.0)`. `Move` does have a `speed` slot bounded at 2.0 m/s. The text is correct as written.
4. **Script pass check**: All proposed edits were verified against script anchors in `tools/review/ingenieur_ch*.py`. All anchors survive intact.

---

## 4. Final Verdict

**VERDICT: ALL FINDINGS CONFIRMED (1 MAJOR, 10 MINOR on Ingénieur text, 1 MINOR on Master deferred, 6 NITs).**
Ready for author approval and patch application.
