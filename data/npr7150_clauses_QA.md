# QA: Content-Fidelity Spot-Check of Extracted Clauses

Scope: issue #1 checklist item "Sanity-check extracted clauses against source doc."
This is a **content-fidelity** pass, on top of (and separate from) the prior structural/integrity pass. It checks wording and meaning against the live source pages, not just schema/uniqueness.

Files checked:
- `data/npr7150_clauses.csv` (34 rows)
- `data/swehb_5_09_guidance.csv` (24 rows)

## Method

1. Fetched the live NPR 7150.2D Chapter 4 page (`https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7150_002D_&page_name=Chapter4`) two ways: once via the `WebFetch` tool (model-summarized) for a first pass, and once with a direct `curl` download of the raw HTML, which I stripped to plain text. The raw-HTML text is the authoritative comparison source — it is the actual page content, not a paraphrase.
2. Wrote a small Python/regex script to parse every `4.x.y <requirement text> [SWE-nnn]` block out of the raw page text and programmatically diff it (section number + whitespace-normalized text) against every row of `npr7150_clauses.csv`, keyed by `clause_id`. This let me verify **all 34 rows**, not just a sample of 8, with an automated exact-match check, then read the surrounding notes/scope language manually to judge `applicability`.
3. Fetched the live SWEHB 5.09 SRS page (`https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695669/...`) the same way (WebFetch pass + raw `curl` download stripped to text, ~144KB / 2233 lines). I located the source paragraph for every one of the 24 `topic` rows in `swehb_5_09_guidance.csv` in the raw text and compared `guidance_text` against it for accuracy and topic-matching (verbatim where the source is quoted, otherwise checked that the paraphrase doesn't misrepresent or mix up topics).
4. Independently re-ran structural checks with pandas: row counts, per-column null counts, `clause_id`/`topic` duplicate counts, section-distribution counts, empty-string checks, and `source_url` consistency — without relying on the prior summary.
5. No changes were needed in either CSV (see "Issues found and fixed" below for the one item flagged for attention but not altered).

## NPR Chapter 4 spot-checks

All 34 rows were checked (exceeds the required minimum of 8, spread across 4.1–4.6), via an automated whitespace-normalized text diff plus manual reading of section context/notes for `applicability`. Result: **34/34 exact match** on `requirement_text` and `npr_section`; all `applicability` values are consistent with the live page.

| clause_id | matches live page? | notes |
|---|---|---|
| SWE-050 (4.1.2) | yes | Verbatim match. Applicability "All projects" — no restriction stated. |
| SWE-051 (4.1.3) | yes | Verbatim match. |
| SWE-184 (4.1.4) | yes | Verbatim match. |
| SWE-053 (4.1.5) | yes | Verbatim match. |
| SWE-054 (4.1.6) | yes | Verbatim match. |
| SWE-055 (4.1.7) | yes | Verbatim match. |
| SWE-057 (4.2.3) | yes | Verbatim match. |
| SWE-143 (4.2.4) | yes | Verbatim match, including the "shall perform a software architecture review on the following categories of projects:" lead-in (sub-items a/b live on the page but are correctly omitted from `requirement_text`, consistent with how other colon-terminated rows like SWE-065 are stored). Applicability "Category 1 & 2 Class A/B only" exactly matches live sub-items a/b ("Category 1 Projects... Category 2 Projects... Class A or Class B"). |
| SWE-058 (4.3.2) | yes | Verbatim match. |
| SWE-060 (4.4.2) | yes | Verbatim match. |
| SWE-061 (4.4.3) | yes | Verbatim match. |
| SWE-135 (4.4.4) | yes | Verbatim match. Note on cyclomatic complexity for safety-critical software is additional guidance, not an applicability restriction — CSV correctly leaves applicability as "All projects". |
| SWE-062 (4.4.5) | yes | Verbatim match. |
| SWE-186 (4.4.6) | yes | Verbatim match. |
| SWE-063 (4.4.7) | yes | Verbatim match. |
| SWE-136 (4.4.8) | yes | Verbatim match. |
| SWE-065 (4.5.2) | yes | Verbatim match (colon lead-in; sub-items a–d correctly omitted from `requirement_text`). |
| SWE-066 (4.5.3) | yes | Verbatim match. Note recommends independent testing for Class A/B/C as best practice, not a scope restriction — "All projects" is correct. |
| SWE-187 (4.5.4) | yes | Verbatim match. |
| SWE-068 (4.5.5) | yes | Verbatim match. |
| SWE-070 (4.5.6) | yes | Verbatim match. Applicability "Flight software/flight equipment only" matches "...qualification of flight software or flight equipment." |
| SWE-071 (4.5.7) | yes | Verbatim match. |
| SWE-073 (4.5.8) | yes | Verbatim match. |
| SWE-189 (4.5.9) | yes | Verbatim match. |
| SWE-190 (4.5.10) | yes | Verbatim match. |
| SWE-191 (4.5.11) | yes | Verbatim match. |
| SWE-192 (4.5.12) | yes | Verbatim match. Applicability "Safety-critical projects only" is a reasonable inference from "...trace to a hazardous event, cause, or mitigation technique" (the page itself has no explicit scope tag on this line, but the content is intrinsically safety-critical-only). |
| SWE-193 (4.5.13) | yes | Verbatim match. Applicability "Projects with uplinked content only" matches "...loaded or uplinked data, rules, and code...". |
| SWE-211 (4.5.14) | yes | Verbatim match. |
| SWE-075 (4.6.2) | yes | Verbatim match. |
| SWE-077 (4.6.3) | yes | Verbatim match (including the curly apostrophe in "software's"). |
| SWE-194 (4.6.4) | yes | Verbatim match. |
| SWE-195 (4.6.5) | yes | Verbatim match. |
| SWE-196 (4.6.6) | yes | Verbatim match. |

## SWEHB 5.09 spot-checks

All 24 rows were checked (exceeds the required minimum of 6). Most are verbatim quotes of the live page; the SMART-style characteristic rows and a couple of others are clearly-labeled paraphrases/syntheses of adjacent bullet lists, all confirmed accurate and correctly attributed to their stated topic.

| topic | accurate? | notes |
|---|---|---|
| 3.1 Introduction | yes | Verbatim match. |
| 3.2 CSCI Requirements | yes | Verbatim match. |
| 3.3 Qualification Provisions | yes | Verbatim match. |
| 3.4 Rationale and Supporting Information | yes | Verbatim match. |
| 3.5 Additional Requirements and Information | yes | Verbatim match. |
| Functional requirement types | yes | Verbatim match. |
| Non-functional requirement types | yes | Verbatim match. |
| Interface requirement types | yes | Verbatim match. |
| Specific | yes | Accurate paraphrase of the "Specific: Clear and unambiguous (e.g., avoid subjective terms like 'efficient' or 'user-friendly')" bullet under Characteristics of Functional Requirements. |
| Testable | yes | Accurate paraphrase of "Specific and verifiable/testable: Each requirement should be clear enough to be tested with defined success criteria." |
| Traceable | yes | Accurate paraphrase of "Traceable: Linked to user needs, business goals, or use cases," with "parent requirement"/"unique identifier" reasonably drawn from the adjacent traceability/ID guidance elsewhere on the page. |
| Complete | yes | Accurate paraphrase of "Complete: Cover all expected inputs, outputs, and scenarios." |
| Measurable | yes | Accurate paraphrase of the Best-Practices bullet "Ensure all derived and decomposed requirements are testable and measurable." |
| Prioritized | yes | Accurate paraphrase of "Prioritize requirements: Identify which functions are critical vs. optional." |
| Decomposed vs Derived Requirements | **partially — NEEDS ATTENTION (minor)** | `guidance_text` is a verbatim, accurate definition of *Decomposed* requirements (matches §3.2.1.1.1 exactly) but never mentions *Derived* requirements at all, despite the topic label promising a decomposed-vs-derived comparison. Not a misrepresentation (what it says is true), but the row under-delivers on its own title. See "Issues found and fixed". |
| State vs Mode Requirements | yes | Accurate excerpt of §3.2.1.2: "A state represents a specific situation during the life of a system where certain conditions hold true. They specify how the system should behave in each state and how it should transition between states based on events or conditions." matches verbatim. |
| Safety Requirements Guidance | yes | Verbatim match of the §3.2.1.4 lead sentence plus the SWE-134 reference sentence. |
| Performance Metric Guidance | yes | Accurate synthesis of the two adjacent NFR best-practice bullets ("Use precise metrics..." and "Define conditions..."). |
| SWE-050 - Software Requirements | yes | Requirement clause matches NPR text (minus the COTS/GOTS/MOTS/OSS list, an intentional simplification that doesn't change meaning); "foundational SWE reference" framing is consistent with the page citing SWE-050 for rationale guidance and in the decomposition Best Practices list. |
| SWE-051 - Software Requirements Analysis | yes | Matches; correctly reflects that the page cites SWE-050/SWE-051 together in the decomposition/derivation Best Practices section. |
| SWE-052 - Bidirectional Traceability | yes | Verbatim match of the §3.2.1.4 traceability-tagging sentences. |
| SWE-053 - Manage Requirements Changes | yes | Verbatim match. |
| SWE-134 - Safety-Critical Software Design Requirements | yes | Verbatim match through "...shall implement the following items in the software: a." (row is truncated right before the item list, which is a length choice, not an error — it doesn't misstate anything). |
| SWE-200 - Software Requirements Volatility Metrics | yes | Verbatim match. |

## Structural re-check results

Independently re-run with pandas (not just trusting the prior summary):

**`npr7150_clauses.csv`**
- Row count: 34 (confirmed)
- Columns: `clause_id, npr_section, chapter, requirement_text, applicability, source_url` — all present
- Nulls: 0 in every column
- Empty strings (non-null but blank): 0
- Duplicate `clause_id`: 0; duplicate full rows: 0
- Section distribution: 4.1→6, 4.2→2, 4.3→1, 4.4→7, 4.5→13, 4.6→5 → total 34 (matches the verified reference exactly)
- `source_url`: single consistent value across all rows

**`swehb_5_09_guidance.csv`**
- Row count: 24 (confirmed)
- Columns: `topic, guidance_text, category, source_url` — all present
- Nulls: 0 in every column
- Empty strings: 0
- Duplicate `topic`: 0; duplicate full rows: 0
- Category distribution: characteristic 9, structure 5, management 5, safety 2, quality-attribute 1, interface 1, performance 1 → total 24
- `source_url`: single consistent value across all rows

No discrepancies from the prior structural summary.

## Issues found and fixed

No factual errors (misquoted text, wrong applicability, or mismatched clause_id/topic) were found in either CSV, so **no rows were edited**.

One item is flagged for attention rather than fixed, since it isn't factually wrong, just incomplete relative to its own label:

- **NEEDS ATTENTION (minor):** `swehb_5_09_guidance.csv`, topic **"Decomposed vs Derived Requirements"**. The `guidance_text` only defines *Decomposed* requirements (an exact quote of SWEHB §3.2.1.1.1) and says nothing about *Derived* requirements, even though the topic title implies a comparison of both (the live page has a separate, equally-detailed §3.2.1.1.2 "Derived Requirements" section that isn't reflected here, plus a §3.2.1.1.3 "Summary of Relationships" table contrasting the two). This does not misrepresent anything — everything stated is accurate — but a downstream user reading this row for "Derived Requirements" content would get nothing. Recommend either renaming the topic to "Decomposed Requirements" or expanding `guidance_text` to also summarize Derived requirements; left as-is pending a decision from whoever owns the extraction script/content scope.

## Overall verdict: ready for downstream use? **Yes**

Both CSVs are content-faithful to their live source pages. All 34 NPR 7150.2D clauses were checked (not just a sample) via an exact automated text/section diff against the raw live Chapter 4 page and all matched with zero discrepancies in requirement text, section number, or applicability. All 24 SWEHB 5.09 guidance rows were checked against the raw live page and are either verbatim quotes or accurate, non-misleading paraphrases correctly attributed to their topic. The independent structural re-check reproduces the previously reported counts, nulls, and duplicate results exactly. The single flagged item ("Decomposed vs Derived Requirements") is a completeness nuance, not a correctness defect, and does not block downstream use — it's noted above so it doesn't silently pass through.
