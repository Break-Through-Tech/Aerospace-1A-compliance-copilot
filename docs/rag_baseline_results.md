# Non-agentic RAG baseline: results

Results of the Output Contract v1 requirement review (issues #13–#15) on the Starhawk SRS, from two full runs on 2026-11-28. This is the baseline the tool-calling agent (#17–#21) will be compared against.

## Setup

- **Input:** the Starhawk Mission Computer SRS, 54 numbered requirements (`SFMC-REQ-001` to `SFMC-REQ-054`).
- **What the LLM receives for each requirement:**
  - the full SRS;
  - the 5 most relevant NASA-HDBK-2203 §5.09 passages (sections 1 and 3);
  - the six core NPR 7150.2D §4.1 clauses (SWE-050, 051, 184, 053, 054, 055), ranked by relevance.
- **Search:** Qwen3-Embedding-0.6B embeddings in ChromaDB (cosine similarity).
- **Model:** `gpt-4.1-mini-2025-04-14` (OpenAI), temperature 0, seed 42. Model fingerprint `fp_000a92d97a` in both runs.
- **Checks on every answer:**
  - it must validate against `RequirementReview` (Pydantic);
  - it must pass the grounding check: citations must come from the passages sent, and SRS quotes must appear word for word.

  A failed answer is retried up to 3 times. After that, the requirement is recorded as `UNDETERMINED` ("Not assessed").
- **Runs:** `rag_baseline_v1` and `rag_baseline_v1_rerun` (the same settings, with the answer cache off for the rerun), saved in `notebooks/results/`. Each took about 7 minutes and about 390,000 prompt tokens.

## Results

### Precision and recall

Scored against the advisor's 7 calibration requirement cases in the Data Card. A requirement counts as **flagged** when our review marks it `NEEDS_REVIEW`.

| Metric | Result |
|---|---|
| Precision | **100%**: 5 of 5 requirements we flagged were also flagged by the advisor |
| Recall | **83%**: 5 of the 6 advisor-flagged requirements were caught |
| Same issue code as the advisor, when both flagged | 4 of 5 |
| Not assessed | 0 of 7 |

| Requirement | Advisor | Ours (run v1) |
|---|---|---|
| SFMC-REQ-002 | ACCEPTABLE | ACCEPTABLE ✅ |
| SFMC-REQ-006 | NEEDS_REVIEW (VAGUE_CRITERION) | NEEDS_REVIEW (VAGUE_CRITERION + 1 more) ✅ |
| SFMC-REQ-010 | NEEDS_REVIEW (UNSPECIFIED_RESPONSE) | NEEDS_REVIEW (UNSPECIFIED_RESPONSE) ✅ |
| SFMC-REQ-021 | NEEDS_REVIEW (VAGUE_CRITERION) | NEEDS_REVIEW (VAGUE_CRITERION + 2 more) ✅ |
| SFMC-REQ-035 | NEEDS_REVIEW (SAFETY_INTERACTION) | NEEDS_REVIEW (UNDEFINED_TERM + 1 more): right verdict, different issue |
| SFMC-REQ-037 | NEEDS_REVIEW (VAGUE_CRITERION) | NEEDS_REVIEW (VAGUE_CRITERION + 1 more) ✅ |
| SFMC-REQ-043 | NEEDS_REVIEW (ESCAPE_CLAUSE) | ACCEPTABLE ❌ missed |

### Citation groundedness

This is the share of schema-valid answers whose citations were all grounded:
- **87%** in run v1 (52 of 60);
- **91%** in the rerun (53 of 58).

Ungrounded answers are never saved as results: they are retried, and recorded as "Not assessed" if every attempt fails.

### Run-to-run consistency

The same settings were run twice:
- **Search results:** identical in both runs, 0 differences.
- **Decisions changed:** 12 of 54.
  - **8** kept the same verdict but named different issue codes.
  - **4** linked a different SWE.
  - **1** (REQ-034) was "Not assessed" in v1 but NEEDS_REVIEW in the rerun.
- **Word for word:** only 1 answer was identical, because the explanations are usually reworded.

**The verdict was the same for all 52 requirements assessed in both runs (100%).** The variation comes from the model itself: the fingerprint shows the provider's setup didn't change.

### What the reviews found (run v1)

- **Software requirements:** 52. The other 2 (REQ-030, REQ-034) are "Not assessed".
- **Quality:** 36 ACCEPTABLE, 16 NEEDS_REVIEW, 2 not assessed.
- **Most common issue codes:** UNDEFINED_TERM (10), ALLOCATION_UNCLEAR (6), VAGUE_CRITERION (6), MISSING_ACCEPTANCE_CRITERIA (4).
- **SWE links:** only **4 requirements** are linked to an NPR provision (REQ-004 and REQ-012 to SWE-051, REQ-014 to SWE-184, REQ-045 to SWE-050).

## Failure cases

1. **A missed escape clause.** REQ-043 ("whenever possible") was marked ACCEPTABLE. The model never used the issue codes `ESCAPE_CLAUSE` or `SAFETY_INTERACTION` in either run, even though the advisor expects them. The prompt lists the issue codes by name only, with no definitions.
2. **The right verdict with a different problem named.** For REQ-035 we flagged the requirement but called it UNDEFINED_TERM, where the advisor named SAFETY_INTERACTION.
3. **Requirements not assessed.** REQ-030 failed every attempt in both runs, because the model added a word to an SRS quote ("Definition of **a** critical fault"), even after being told the quote wasn't found. REQ-034 failed in v1 but passed in the rerun.
4. **Few SWE links.** Only 4 of the 54 requirements get a link. REQ-015 isn't linked to SWE-184, although the advisor's sample report links it.
5. **Unstable details.** Between runs, the issue codes changed for 8 requirements and the SWE links for 4.

## Limitations

- **Small answer key.** Only 7 requirement cases have answers, and just 1 is ACCEPTABLE. One case moves precision or recall by about 15 points.
- **Holdout not scored.** The 26 HOLDOUT cases have no answers in the Data Card.
- **Only requirement quality was evaluated.** The relationship, document and SWE-coverage cases need the full report (#25).
- **One SRS.** Results may not carry over to other documents.
- **Not fully repeatable.** The model isn't fully deterministic, even at temperature 0 with a fixed seed.
- **Grounding isn't support.** The grounding check confirms that a citation exists in the sources sent, not that it supports the finding.
- **Hardware.** The search uses full precision (fp32), so Colab's GPU and a CPU return identical top-5 lists (#24).

## Recommendations for the next milestone

1. **Fix the last grounding failures.** REQ-030 fails because the model keeps adding a word to the quote. Try showing it the exact SRS line in the retry feedback.
2. **Define the issue codes in the prompt.** Use one plain sentence for each, so the model can use ESCAPE_CLAUSE and SAFETY_INTERACTION. Re-measure afterwards, without ever using the calibration answers in the prompt.
3. **Ask the advisor to score our answers on the 26 holdout cases,** for a more trustworthy result.
4. **Investigate why SWE links are rare.** Check whether the prompt is too strict, or whether the requirements really rarely support an NPR link.
5. **Generate `report.json` (#25),** so the relationship, document and SWE-coverage cases can be evaluated too.
6. **Consider a majority vote over 3 runs for each requirement.** It would make results more stable, at 3× the cost. Measure it before adopting it.
7. **Compare the agent (#17–#21) against these numbers,** using the same calibration cases and the same metrics.
