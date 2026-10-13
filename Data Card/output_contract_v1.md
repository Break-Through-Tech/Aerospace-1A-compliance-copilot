# SRS Compliance Copilot — Output Contract v1.0.0 (Draft)

**Status:** Proposed for Challenge Advisor review, 2026-10-12.  
**Purpose:** A common output shape for Teams 1A and 1B so implementations and results can be compared without requiring the same algorithms.  
**Machine specification:** [`output_contract_schema_v1.json`](output_contract_schema_v1.json).  
**Worked example:** [`sample_output_v1.json`](sample_output_v1.json).

## 1. What the tool does — and does not do

Given an SRS, the tool (1) decides whether each extracted statement is a software requirement, (2) critiques the quality of each software requirement using *NASA-HDBK-2203, Ver. D, topic 5.09*, (3) identifies requirements that provide evidence relevant to applicable *NPR 7150.2D §4.1* SWE provisions, (4) reports cross-requirement and document-level issues, and (5) summarizes **evidence visible in the SRS**, not the engineering project's legal/organizational compliance.

**Non-negotiable distinction:** A requirement mentioning a safety feature is evidence of a documented safety-related requirement; it does **not** prove that project management fulfilled SWE-184. Likewise, a document version number does not prove change management under SWE-053. A missing approval/signature or an absent process record is not automatically evidence of noncompliance when the only supplied input is an SRS.

**Authority:** NPR provisions are requirements for applicable NASA projects (subject to applicability/tailoring); the Handbook provides recommended SRS-writing and content guidance. Never describe failure to follow a Handbook recommendation alone as violation of an NPR requirement.

**Core NPR scope (six provisions only):** SWE-050 (§4.1.2), SWE-051 (§4.1.3), SWE-184 (§4.1.4), SWE-053 (§4.1.5), SWE-054 (§4.1.6), SWE-055 (§4.1.7). SWE-052 is a useful *later extension*, but it is **not** a §4.1 provision; it appears under requirements traceability elsewhere in the NPR.

## 2. Top-level object

One UTF-8 JSON file, `report.json`, conforming to JSON Schema Draft 2020-12.

| Field | Shape | Meaning |
|---|---|---|
| `schema_version` | literal `"1.0.0"` | Contract compatibility identifier. |
| `run` | object | SRS identity, reference versions, method, evaluation scope (`DEMO` / `FULL_SRS`), UTC timestamp, limitations. |
| `requirement_reviews` | array | Exactly one review for each unique requirement ID in a full run. |
| `relationships` | array | Cross-requirement consistency/interaction findings. May be empty. |
| `document_findings` | array | Checks that need a document-wide view, including missing content. |
| `swe_coverage` | array | One evidence summary per core NPR SWE in a **full** run. |

### Per-requirement record

- `requirement_id`, `raw_text`: IDs and source text are preserved verbatim (apart from harmless whitespace normalization).
- `software_requirement_status`: `YES` / `NO` / `UNCERTAIN`. This is a **scope/allocation** judgment, not a quality verdict.
- `quality_status`: `ACCEPTABLE` / `NEEDS_REVIEW` / `UNDETERMINED`. `ACCEPTABLE` means no demonstrated writing defect under the checks performed, not a certificate of perfection.
- `quality_issues[]`: zero or more specific findings containing a controlled issue code, severity, explanation, *SRS evidence excerpt and locator*, NASA reference, suggested action, and whether a stakeholder decision is needed.
- `swe_links[]`: zero or more relevant NPR §4.1 provisions. Each has `swe_id`, strength, explanation, actual SRS evidence, and specific NPR citation.
- `primary_swe_id`, `primary_swe_strength`: the **strongest justified SWE association**, or both `null` if there is none. Never select a SWE merely because the text shares words with a clause.
- `summary`: one or two evidence-grounded sentences.

**Evidence strengths** (applied to *visible SRS content*, not NASA-project compliance):

| Value | Interpretation |
|---|---|
| `DIRECT_CONTENT` | The requirement explicitly expresses a relevant behavior/control/content expectation (e.g., weapons firing inhibit and SWE-184). |
| `PARTIAL_CONTENT` | Relevant but incomplete or unresolved content (e.g., undefined safety classification). |
| `INDIRECT_CONTEXT` | Related background, but insufficient to infer a specific SWE obligation is represented. |
| *No link / `null`* | No sufficiently justified provision association. Abstention is expected where necessary. |

### Relationship record

`relationship_id`, `requirement_ids`, `status`, `issue_code`, `explanation`, `srs_evidence`, `nasa_references`, `recommendation`.

`status` is one of:

- `CONFIRMED_CONFLICT`: mutually impossible obligations **under the same explicit conditions**.
- `NEEDS_CLARIFICATION`: possible interaction, scope overlap, precedence ambiguity, or conflicting interpretation, not yet a proven contradiction.
- `NO_CONFIRMED_CONFLICT`: compared statements can coexist, even if documentation could be clearer.

**Important test:** REQ-002 specifies a minimum of one update per 500 ms; REQ-038 specifies at least ten per second. Both minima can be satisfied simultaneously, so the pair is **not a confirmed contradiction**. REQ-015 and REQ-035 require scrutiny of safety interlock precedence, but the text does not establish that a weapons inhibit is part of the overridable automatic controls.

### Document finding

Each record identifies a criterion, an inspected SRS scope, `status` (`PRESENT`, `PARTIAL`, `MISSING`, `UNDETERMINED`), explanation, evidence where available, authority citation, and recommendation.

For **absence findings**, `srs_evidence` may be an empty list; in that case, `searched_scope` must identify the inspected document extent. A missing Handbook-recommended section is a **guidance gap**, not by itself an NPR violation.

### Six-SWE evidence summary

Exactly one `swe_coverage` entry for each core SWE for `FULL_SRS` runs. Each contains:

- `document_evidence`: `DOCUMENTED`, `PARTIAL_EVIDENCE`, `NO_SRS_EVIDENCE`, or `NOT_ASSESSABLE`.
- `project_compliance`: always `NOT_DETERMINED` in v1, since the input is an SRS alone.
- Supporting SRS excerpts and requirement IDs (where available).
- Explicit `external_evidence_needed` and rationale.
- The NPR clause reference with its section and URL.

`NOT_ASSESSABLE` is the correct response when the operative requirement concerns a process that cannot be verified from an SRS (e.g., change control, validation sign-offs or issue resolution). `NO_SRS_EVIDENCE` means that an SRS-searchable indicator was not found, **not** that a NASA manager failed to perform a required process.

## 3. Semantic validation (in addition to JSON Schema)

A JSON Schema validates structure and types. The following rules require programmatic checks or human review:

1. For `FULL_SRS`, review each of the 54 numbered Starhawk requirements exactly once; report extras (including unnumbered §2.1 “shall” statements) as findings rather than silently dropping them. IDs in the schema are intentionally not limited to the Starhawk prefix, so a different SRS can use its own identifiers and count; the included semantic validator applies the 54-ID completeness check to this Starhawk pilot.
2. For `FULL_SRS`, include exactly the six NPR §4.1 core SWE summaries; no duplicates.
3. Every referenced requirement ID must exist in the SRS. Every cited section/SWE ID must exist in the cited NASA source. Source excerpt text must support the claim; a valid citation ID alone is not proof of groundedness.
4. `primary_swe_id` and `primary_swe_strength` are either both `null` or correspond to one `swe_links[]` entry; if multiple links exist, choose the most direct substantiated association, not the highest similarity score.
5. For `ACCEPTABLE`, `quality_issues` should normally be empty; a non-empty issue array requires `NEEDS_REVIEW` or `UNDETERMINED`.
6. A relationship marked `CONFIRMED_CONFLICT` must explain precisely why both statements cannot be satisfied together under the same conditions. Mere differences in numeric minima are insufficient.
7. If the answer needs omitted evidence (hazard analyses, project baselines, stakeholder approval records), name the external evidence rather than guessing.
8. All outputs, including no-match and abstention cases, need human-readable explanations. Do not turn cosine similarity values or classifier confidence into NASA compliance verdicts.
9. Evidence quoted from the SRS must be faithfully transcribed (or be an exact supported short excerpt). Recommendations must not fabricate mission parameters, approval status, or NASA applicability.

## 4. Expected deliverables for Sprint 4

- `report.json`, parsed by the provided schema; may be a **DEMO** for the five-case meeting demonstration, then a **FULL_SRS** for the final sprint delivery.
- A small human-readable summary (`report.md` or equivalent) generated from the JSON. JSON is canonical; prose is a presentation layer.
- A command or notebook instruction that regenerates the report from the repository data.
- Unit or regression tests including a good requirement, an unclear requirement, a safety interaction, a missing document element, and a process-evidence abstention.
- An evaluation report with per-scope outcomes, false-positive/false-negative examples, citations checked by a reviewer, and explicit scope limitations.

**Technology neutral:** TF-IDF, rules, embeddings, Chroma/FAISS, or LLMs are all permissible. Results must be judged against the *same evidence rules and output contract*, not against the technology used.

## 5. Worked command and contract check

```bash
python -m pip install jsonschema
python -m jsonschema -i sample_output_v1.json output_contract_schema_v1.json
```

The example covers only three requirement IDs and one SWE. It uses `evaluation_scope=DEMO` deliberately. A full run has additional completeness obligations listed above.

## Sources and version control

- NASA NPR 7150.2D, Chapter 4, §4.1: <https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7150_002D_&page_name=Chapter4>
- NASA-HDBK-2203, Ver D, Topic 5.09: <https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695669/5.09+-+SRS+-+Software+Requirements+Specification>
- Starhawk SRS, `SH-SRS-001`, version 1.0: <https://github.com/Break-Through-Tech/Aerospace-1B-compliance-copilot/blob/main/data/Starhawk%20Mission%20Computer%20SRS.md>

This contract and benchmark are **draft teaching/evaluation artifacts**, not an official NASA compliance determination, endorsement, or substitute for formal review of current controlled standards.
