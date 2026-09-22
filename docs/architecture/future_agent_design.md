> **This is a design document for a later milestone (Oct/Nov per
> Challenge-Project-Overview.md); no runtime agent code exists yet.**
> Everything below is a spec: schema sketches, tool contracts, and an
> orchestration sketch. No `.py` module, no runnable agent, and no network
> calls are part of this sprint's deliverable. Pydantic-style code blocks
> here describe *intended* shapes only.

# Future Agent Design: Tool-Calling Compliance Copilot

## Scope and relationship to this sprint

`Challenge-Project-Overview.md` lays out a two-stage architecture: an
**October Non-Agentic RAG baseline**, then a **November Tool-Calling LLM
Agent** wrapping that pipeline in three tools — `retrieve_clause`,
`check_requirement`, `log_gap` — with a **December** stretch goal of a
LangGraph refactor. This document designs that November agent early, so the
October baseline and this sprint's manual/taxonomy work (Activities 3–6) feed
directly into its schema instead of the November team re-deriving it from
scratch. It builds on, and should not diverge from, four artifacts already
produced this session:

- `docs/manual_requirement_review.csv` — the proven output schema (54 rows).
- `docs/requirement_quality_taxonomy.md` — the 5-category Issue Category
  enum, each with NASA Basis and Detection Questions.
- `docs/nasa_guidance_analysis.csv` — the INDIVIDUAL/SET/PROCESS/MULTIPLE
  classification of every NPR 7150.2 §4.1 and SWEHB 5.09 clause.
- `data/srs_clause_triage.csv` — a worked example, per-requirement, of which
  clauses are "Applicable Guidance Level" for that requirement.

---

## Tool 1: `retrieve_clause(query, source_filter)`

**Purpose:** retrieve candidate clauses from the initial retrieval corpus
this sprint already built — `data/npr7150_clauses.csv` (NPR 7150.2D clauses,
columns: `clause_id, npr_section, chapter, requirement_text, applicability,
source_url`) and `data/swehb_5_09_guidance.csv` (SWEHB 5.09 guidance,
columns: `topic, guidance_text, category, source_url`).

### Should it filter by INDIVIDUAL/MULTIPLE by default?

**Yes — default `source_filter` should restrict retrieval to clauses
classified INDIVIDUAL or MULTIPLE in `docs/nasa_guidance_analysis.csv`,
excluding pure PROCESS clauses, with an explicit opt-in to widen the pool.**

Justification, from this session's own finding: `docs/nasa_guidance_analysis.csv`
classifies most NPR 7150.2 §4.1 clauses (SWE-050, SWE-051, SWE-053, SWE-054,
SWE-055, SWE-057…) as **PROCESS** — obligations on the project manager to run
an activity (elicit, analyze, track, validate) across the whole requirement
set, not properties checkable by reading one requirement sentence. Confirming
this empirically: **zero of the 19 NEEDS REVIEW rows in
`docs/manual_requirement_review.csv` cite a PROCESS-only NPR clause** — every
NASA Source cites an SWEHB 5.09 characteristic classified INDIVIDUAL (Specific,
Testable, Measurable, Complete, Performance Metric Guidance) or, for the
safety-critical subset, a MULTIPLE clause (Safety Requirements Guidance,
SWE-134, SWE-052, NPR SWE-192 — see `data/srs_clause_triage.csv` rows for
SFMC-REQ-014/015/019/020/030/040/041/043, all tagged `MULTIPLE`). Since
`check_requirement` operates on one requirement sentence at a time, retrieving
a PROCESS clause as a "candidate" would hand the LLM a clause it cannot
actually ground a sentence-level verdict in — citing SWE-050 against "the
spacecraft shall notify the pilot quickly when fuel is low" would be a
category error: real-looking, but not actually supporting the claim. That is
precisely the kind of technically-present-but-non-supporting citation the
project's own "zero ungrounded or hallucinated verdicts" success criterion is
meant to catch, so excluding it at retrieval time (rather than trusting the
LLM to self-filter after seeing it) is a stronger, and cheaper, guardrail.

MULTIPLE clauses are kept in the default pool (not excluded alongside
PROCESS) because, per `docs/nasa_guidance_analysis.csv`'s own reasoning, they
still bear directly on a single requirement even though they *also* involve a
document- or process-level component — e.g. Safety Requirements Guidance
genuinely is part of what should ground a verdict on a weapons-interlock
requirement like SFMC-REQ-014/015, and `data/srs_clause_triage.csv` already
uses `MULTIPLE` (not a third exclusion bucket) for exactly those rows.

`source_filter` should support:
- `individual_and_multiple` (default) — SWEHB 5.09 INDIVIDUAL/MULTIPLE rows
  only, i.e. the same pool `data/srs_clause_triage.csv` draws its "Applicable
  Guidance Level" citations from.
- `include_process` — widen to also retrieve PROCESS clauses, reserved for a
  future process-compliance mode (e.g. "did the PM run this activity"),
  explicitly *not* what `check_requirement` should use for a per-sentence
  verdict.
- `npr_only` / `swehb_only` — source restriction, orthogonal to the level
  filter above.

```
# Design sketch — NOT executable this sprint
class RetrieveClauseRequest(BaseModel):
    query: str                      # the requirement text, or a sub-phrase
    source_filter: Literal[
        "individual_and_multiple",  # default
        "include_process",
        "npr_only",
        "swehb_only",
    ] = "individual_and_multiple"
    top_k: int = 5

class CandidateClause(BaseModel):
    clause_id: str                  # e.g. "SWE-050" or "SWEHB-5.09-Specific"
    source: Literal["NPR-7150.2D", "SWEHB-5.09"]
    guidance_level: Literal["INDIVIDUAL", "SET", "PROCESS", "MULTIPLE"]
    clause_text: str
    source_url: str
    relevance_score: float

class RetrieveClauseResponse(BaseModel):
    candidates: list[CandidateClause]
```

A cheap October-baseline shortcut worth noting for design continuity:
`data/srs_clause_triage.csv` has *already done this retrieval-and-filtering
step by hand* for all 54 SFMC requirements. The November agent's
`retrieve_clause` could be validated against that file directly (does the
agent's retrieved set for SFMC-REQ-014 match the "Checkable Clauses" column
already recorded there?) before trusting it on unseen SRS text.

---

## Tool 2: `check_requirement(requirement_text, candidate_clauses)`

**Purpose:** produce a structured verdict for one requirement, grounded only
in the clauses `retrieve_clause` actually returned.

### Schema

The schema is not invented for this document — it is the column set
`docs/manual_requirement_review.csv` already proved out over 54 rows, plus a
citation-groundedness field required by `Challenge-Project-Overview.md`'s
success criteria ("100% of generated verdicts must cite the specific
standard clause ID"; "zero ungrounded or hallucinated verdicts").

```
# Design sketch — NOT executable this sprint
class IssueCategory(str, Enum):
    # The 5 categories from docs/requirement_quality_taxonomy.md — no
    # category invented beyond what that document's 19-row analysis showed.
    UNDEFINED_TERM = "undefined_term"
    UNQUANTIFIED_PERFORMANCE_CRITERION = "unquantified_performance_criterion"
    UNVERIFIABLE_BEHAVIOR = "unverifiable_behavior"
    COMPOUND_REQUIREMENT = "compound_requirement"
    MISSING_NUMERICAL_BOUND = "missing_numerical_bound"

class DefectCertainty(str, Enum):
    # Distinguishes "this IS a defect" from "this NEEDS a human" —
    # see docs/ai_review_brainstorm.md, "How should it distinguish a
    # definite defect from something that merely needs human review?"
    STRUCTURAL_DEFECT = "structural_defect"        # pattern-detectable from
                                                     # text alone, e.g. an
                                                     # "and" joining two
                                                     # shall-clauses, or an
                                                     # absolute "never"
    NEEDS_STAKEHOLDER_INPUT = "needs_stakeholder_input"  # category is
                                                     # confidently assigned,
                                                     # but the missing fact
                                                     # (a number, a boundary
                                                     # definition) cannot be
                                                     # supplied from the SRS

class CitedClause(BaseModel):
    clause_id: str          # MUST be a clause_id present in candidate_clauses
    guidance_level: Literal["INDIVIDUAL", "SET", "PROCESS", "MULTIPLE"]
    quoted_or_paraphrased_text: str

class IssueFinding(BaseModel):
    category: IssueCategory
    is_primary: bool                # supports multiple issues per
                                     # requirement, e.g. SFMC-REQ-025's
                                     # "important" + "securely encrypted"
    explanation: str
    defect_certainty: DefectCertainty
    nasa_source: list[CitedClause]  # non-empty for every NEEDS_REVIEW issue
    proposed_revision: str | None   # may contain "[... TBD by stakeholder]"
                                     # placeholders per docs/requirement_rewrites.md
                                     # convention — never a fabricated number
    stakeholder_question: str | None  # populated when defect_certainty ==
                                       # NEEDS_STAKEHOLDER_INPUT

class RequirementVerdict(BaseModel):
    requirement_id: str
    assessment: Literal["ACCEPTABLE", "NEEDS_REVIEW"]
    # ^ mirrors docs/manual_requirement_review.csv's own Assessment values,
    #   deliberately NOT a bare PASS/FAIL (see docs/ai_review_brainstorm.md).
    #   Mapping this onto Challenge-Project-Overview.md's benchmark labels
    #   (Meets / Partial / Gap) is an open design question for the Oct
    #   baseline team — likely ACCEPTABLE -> Meets, and NEEDS_REVIEW splits
    #   into Partial/Gap by severity (e.g. Compound/Unverifiable/safety-
    #   tagged issues -> Gap; a lone Undefined Term -> Partial) — but that
    #   split needs a stakeholder decision, not an invented threshold.
    issues: list[IssueFinding]      # empty iff assessment == "ACCEPTABLE"
    citation_groundedness: float    # 0.0-1.0: fraction of issues whose
                                     # nasa_source clause_ids are (a) present
                                     # in the retrieved candidate_clauses
                                     # AND (b) INDIVIDUAL/MULTIPLE level, not
                                     # a PROCESS clause misapplied to a
                                     # sentence-level finding
```

Two things this schema does *not* try to do, on purpose, per this session's
findings:
- It never lets `check_requirement` invent a numeric threshold or category
  boundary. Per `docs/requirement_rewrites.md`'s own confirmation section,
  every genuinely new number/definition (targeting accuracy, encryption
  standard, "critical fault" criteria, reliability target, log capacity,
  corrective-action mapping) was left as a placeholder with a stakeholder
  question — `proposed_revision` and `stakeholder_question` exist in this
  schema specifically to preserve that discipline in the agent, rather than
  letting a fluent LLM quietly fill the bracket in with a plausible-sounding
  number.
- It never treats `citation_groundedness` as advisory. A verdict whose
  `nasa_source` clause_ids don't appear in `candidate_clauses`, or whose
  cited clause is PROCESS-level, should be rejected and re-run (see
  orchestration below) rather than logged — this is the mechanism that
  actually delivers "zero ungrounded or hallucinated verdicts," not just a
  reported metric about it after the fact.

---

## Tool 3: `log_gap(requirement_id, verdict)`

**Purpose:** accumulate `RequirementVerdict` records into the final JSON and
Markdown gap report `Challenge-Project-Overview.md` asks for as a
deliverable ("Generate full JSON and Markdown gap reports").

```
# Design sketch — NOT executable this sprint
class GapLogEntry(BaseModel):
    requirement_id: str
    verdict: RequirementVerdict
    logged_at: datetime

class GapReport(BaseModel):
    entries: list[GapLogEntry]
    # Summary counts mirror the Summary Table already established in
    # docs/requirement_quality_taxonomy.md (category -> count, plus total),
    # so the automated report is visually/structurally comparable to the
    # manual one, not a differently-shaped artifact.
    summary_by_category: dict[IssueCategory, int]
    total_acceptable: int
    total_needs_review: int
```

- **JSON rendering**: `GapReport.model_dump_json()` — one record per
  requirement, machine-checkable against the benchmark in a later evaluation
  step (precision/recall against seeded gaps, per
  `Challenge-Project-Overview.md`'s Success Criteria).
- **Markdown rendering**: one section per NEEDS_REVIEW requirement, in the
  same *Original / Identified problem / Proposed revision / Assumptions made
  / Questions requiring stakeholder clarification* shape already used in
  `docs/requirement_rewrites.md`, plus a leading summary table shaped like
  `docs/requirement_quality_taxonomy.md`'s Summary Table. Reusing that layout
  is deliberate: a reviewer who has already read this sprint's docs should
  find the automated report structurally familiar, not a new format to
  learn.

`log_gap` is intentionally a pure accumulation step with no re-judgment
logic — any correction (e.g., low `citation_groundedness`) must happen
*before* `log_gap` is called, inside the orchestration loop below, so the
log never contains a verdict the agent itself flagged as ungrounded.

---

## Orchestration: the agent loop across a full SRS

```
for requirement in parsed_srs.requirements:            # e.g. 54 SFMC-REQ-XXX rows
    attempt = 0
    verdict = None
    while attempt < MAX_RETRIES and verdict is None:
        attempt += 1

        # 1. retrieve_clause — default filtered to INDIVIDUAL/MULTIPLE
        candidates = retrieve_clause(
            query=requirement.text,
            source_filter="individual_and_multiple",
        )

        # 2. check_requirement — grounded only in what was retrieved
        draft_verdict = check_requirement(
            requirement_text=requirement.text,
            candidate_clauses=candidates,
        )

        # 3. groundedness gate — reject and retry with a refined query
        #    instead of logging an under-cited verdict
        if draft_verdict.citation_groundedness < GROUNDEDNESS_THRESHOLD:
            # widen or refine the retrieve_clause query (e.g. include the
            # specific flagged term as the query) and loop
            continue

        verdict = draft_verdict

    # 4. log_gap — only a grounded verdict reaches the report
    log_gap(requirement_id=requirement.id, verdict=verdict or FALLBACK_FLAG_FOR_HUMAN)

final_report = compile_gap_report(all_logged_entries)  # -> GapReport
write_json(final_report)
write_markdown(final_report)
```

Notes on the loop:
- **Retry-on-low-groundedness**, not retry-on-failure, is the key design
  choice: it is the mechanism-level answer to the "zero ungrounded verdicts"
  success criterion, rather than trusting a single LLM pass to self-police.
- A requirement that still cannot clear the groundedness threshold after
  `MAX_RETRIES` should be logged as an explicit `NEEDS_HUMAN_REVIEW` flag
  (not silently dropped, and not force-logged with a weak citation) — this
  mirrors this sprint's own repeated finding that some gaps (e.g. what
  counts as a "critical fault") cannot be resolved from the SRS text alone
  and must route to a person.
- Cross-requirement context (the "REQ-030 vs. REQ-027's 1-second bound"
  pattern from `docs/requirement_quality_taxonomy.md`) is not naturally
  visible to a per-requirement loop. A later refinement (candidate for the
  December LangGraph stretch, not this sprint) could pass a lightweight
  index of already-seen requirements' quantified values into `retrieve_clause`
  or `check_requirement`'s context, so the agent can propose "SFMC-REQ-027
  already establishes 1 second for the general case" the way the human
  reviewer did, instead of treating each requirement as fully independent.

## Issue Category enum: what becomes the agent's enum, and what doesn't

The agent's `IssueCategory` enum should be **exactly the five categories** in
`docs/requirement_quality_taxonomy.md` — Undefined Term, Unquantified
Performance Criterion, Unverifiable Behavior, Compound Requirement, Missing
Numerical Bound — because that document is explicit that "[n]o category...
was invented beyond what the data actually shows, and none of the five that
appear has been omitted," having been derived from all 19 real NEEDS REVIEW
findings. Each category's Detection Questions in that document should become
the check the agent runs (or the questions embedded in its
`check_requirement` prompt) to decide category membership, and each
category's NASA Basis should become the `guidance_level` cross-check on the
`nasa_source` citation the agent proposes for that category.

Two things intentionally *not* baked into the enum yet: (1) a catch-all
"Other" category for defect types the current 54-row SRS never exercised —
adding one now would violate the same "don't invent beyond the evidence"
principle the taxonomy document holds itself to, so it's better left as an
explicit open question for whoever runs the agent against a second SRS in
October/November and finds a genuinely new pattern; (2) the ACCEPTABLE/
NEEDS_REVIEW → Meets/Partial/Gap mapping noted above in the
`RequirementVerdict` schema, which needs a severity rule the taxonomy doesn't
currently define.
