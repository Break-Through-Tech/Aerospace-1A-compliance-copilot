# AI Review Brainstorm (Sprint Packet Activity 6)

## Purpose

Activity 6 asks us to imagine handing a single requirement to an LLM reviewer
and think through what that interaction would need to look like, *before* any
of it is built ("Do not build the complete AI system during this sprint" —
this document is brainstorm only, no implementation).

The packet's own worked example is:

> SR-042: "The spacecraft shall notify the pilot quickly when fuel is low."

This is not a hypothetical shape for us — it is almost exactly
**SFMC-REQ-008 / SFMC-REQ-009** in the real Starhawk SFMC SRS before those
requirements were tightened:

> SFMC-REQ-008 — "The SFMC shall display a low-fuel warning when remaining
> fuel falls below 15 percent of usable fuel capacity."
> SFMC-REQ-009 — "When remaining fuel falls below 5 percent of usable fuel
> capacity, the SFMC shall display a critical-fuel warning and generate an
> audible alarm."

Both were rated **ACCEPTABLE** in `docs/manual_requirement_review.csv`
precisely *because* they replace SR-042's "quickly" / "low" with numeric
thresholds (15%, 5%) and an observable display/alarm behavior. SR-042 is, in
effect, the unquantified draft that SFMC-REQ-008/009 became after someone
fixed exactly the defect class this activity is about. That makes SR-042 a
useful stand-in: whatever an LLM reviewer would need to say about SR-042 is
almost a preview of what it should have said about REQ-008/009 before they
were fixed, and every claim below is checked against what the manual process
(Activities 3–5) actually did with real SRS text, not invented in the
abstract.

---

## What information should be provided to the LLM?

Not just the bare sentence. The manual review needed, and repeatedly used,
more than the one requirement's text:

- **The requirement text and its ID** (`SR-042`), so any finding can be
  logged against a stable identifier — every row of
  `docs/manual_requirement_review.csv` is keyed by Requirement ID for exactly
  this reason.
- **The surrounding SRS**, not just the one sentence. Several manual findings
  are only findable by cross-referencing other requirements: SFMC-REQ-030's
  "immediately" is flagged as a gap specifically because SFMC-REQ-027
  *elsewhere in the same document* already gives an explicit 1-second bound
  for the general case — you cannot know "immediately" is under-specified
  without seeing that comparison point. The same applies to SR-042/"fuel is
  low": whether "low" is under-specified can only be judged once the reviewer
  can see that SFMC-REQ-008/009 exist and already define numeric thresholds
  for the same concept elsewhere in the document.
- **The SRS's own "Open Items" list**, if the source document has one. A
  striking number of manual findings (SFMC-REQ-004, -006, -015, -025, -030,
  -033/034, -037, -047, -050) turned out to be gaps the SRS's own authors had
  *already* flagged as unresolved open items. An LLM reviewer that can see
  the open-items list gets a strong, cheap signal that a term is genuinely
  unresolved rather than merely worded loosely — without it, the model would
  have to infer that from silence alone.
- **A fixed taxonomy of defect types to check against** (see
  `docs/requirement_quality_taxonomy.md`), so the model's output categories
  are the same five buckets a human reviewer converged on (Undefined Term,
  Unquantified Performance Criterion, Unverifiable Behavior, Compound
  Requirement, Missing Numerical Bound) rather than an open-ended, differently
  -worded finding every time.

## What NASA reference material would it need?

This is where the session's INDIVIDUAL/SET/PROCESS/MULTIPLE classification
work in `docs/nasa_guidance_analysis.csv` matters directly, and it changes
the naive answer.

The naive assumption would be "feed it NPR 7150.2 §4.1, that's the
compliance standard." But `docs/nasa_guidance_analysis.csv` shows that almost
every NPR §4.1 clause (SWE-050, SWE-051, SWE-053, SWE-054, SWE-055, ...) is
classified **PROCESS**: each one is a directive that the *project manager*
run some activity (elicit requirements, analyze them, manage changes,
validate the system) across the whole requirement set. None of that is a
property you can check by reading one requirement sentence — SWE-050 tells
you whether the PM ran a requirements-management process, not whether "the
spacecraft shall notify the pilot quickly when fuel is low" is well-written.
Citing SWE-050 against SR-042 would be a category error: real-looking, but
not actually grounds for the verdict.

The material that *is* the right size for a single-sentence review is
**SWEHB 5.09's INDIVIDUAL-level characteristics** — Specific, Testable,
Measurable, Complete, Traceable, and Performance Metric Guidance, plus the
functional/non-functional/interface type definitions — because, per
`docs/nasa_guidance_analysis.csv`'s own reasoning for each of those rows,
they are "directly checkable by reading one requirement sentence in
isolation." This is exactly what the manual review already did: every one of
the 19 NEEDS REVIEW rows in `docs/manual_requirement_review.csv` cites an
SWEHB 5.09 characteristic in its NASA Source column (e.g., "SWEHB 5.09 -
Specific", "SWEHB 5.09 - Performance Metric Guidance") — **zero of the 19
rows cite an NPR 7150.2 clause**, which is strong evidence for the
INDIVIDUAL-vs-PROCESS split rather than an assumption about it.

For SR-042 specifically: "quickly" would be checked against **Performance
Metric Guidance** ("non-functional and performance requirements should use
precise, measurable metrics... rather than vague, subjective terms like
'fast' or 'efficient'") — the same clause already cited for SFMC-REQ-016,
-021, -037 in the taxonomy's Unquantified Performance Criterion category —
and "fuel is low" would be checked against **Specific** ("avoids subjective
terms... states exactly what is required"), the same clause cited on all 11
Undefined Term rows. `data/srs_clause_triage.csv` already shows the pattern
for picking which clauses apply per requirement (most rows are INDIVIDUAL and
pull only the generic Specific/Testable/Traceable/Measurable set; a smaller
MULTIPLE subset also pulls in safety or mode-related guidance) — SR-042 would
be a plain INDIVIDUAL case, since it is neither safety-critical-weapon-system
language nor mode-conditioned.

## What should the LLM return?

The schema the manual process already proved out, in
`docs/manual_requirement_review.csv`'s own columns: **Assessment, Issue
Category, Explanation, NASA Source, Proposed Revision.** That is not an
arbitrary design choice for this brainstorm — it is the schema 54 real rows
were already filled into successfully, so an LLM reviewer should return
structurally the same thing rather than free-text prose: an assessment, a
category from the fixed taxonomy (or none, if acceptable), a short
explanation, one or more specific NASA clause citations, and — where
possible — a proposed revision.

## Should it simply say PASS or FAIL?

No — the manual process never used PASS/FAIL, and for good reason. It used
**ACCEPTABLE / NEEDS REVIEW**, a distinction about verifiability rather than
a binary judgment of correctness, and even "NEEDS REVIEW" is not a verdict on
its own — it is always paired with an Issue Category and Explanation. A bare
PASS/FAIL would collapse exactly the information that makes the taxonomy
useful: "NEEDS REVIEW / Unquantified Performance Criterion" and "NEEDS
REVIEW / Compound Requirement" call for completely different remediation
(supply a number vs. split a sentence), and a single FAIL bit destroys that
distinction. SR-042 would come back NEEDS REVIEW with (at least) two
category tags, not a single FAIL.

## Should it identify multiple issues?

Yes — several real rows carry more than one problem in one sentence.
SFMC-REQ-004 flags both "safe" and "efficient" as separately undefined;
SFMC-REQ-025 flags both "important" (undefined scope) and "securely
encrypted" (unnamed standard); SFMC-REQ-021's own explanation notes that
"dangerous" is *also* an Undefined Term problem even though the row's
recorded Issue Category is Unquantified Performance Criterion (the taxonomy
document explicitly calls this out as "double-counted... under Undefined
Term territory"). SR-042 itself has exactly this shape: "quickly" is an
Unquantified Performance Criterion and "fuel is low" is an Undefined Term
(vs. SFMC-REQ-008's explicit 15%), in one short sentence. So the schema needs
a *list* of issues, with one designated as primary if forced to choose (the
manual review's convention, per the taxonomy document), not a single-category
field.

## Should it quote or cite NASA guidance?

Yes, and it should cite the *specific clause ID*, not just gesture at "NASA
guidance." This is not just good practice — it is the project's own stated
success criterion: `Challenge-Project-Overview.md` requires "100% of
generated verdicts must cite the specific standard clause ID" with "zero
ungrounded or hallucinated verdicts." The manual review already demonstrates
what a grounded citation looks like: every NEEDS REVIEW row's NASA Source
field names the exact SWEHB 5.09 characteristic that was violated (e.g.,
"SWEHB 5.09 - Specific; SWEHB 5.09 - Measurable" for SFMC-REQ-006), and the
citations are always drawn from INDIVIDUAL-level guidance for a sentence-
level finding, never PROCESS-level NPR clauses. For SR-042, a grounded
citation would name "SWEHB 5.09 - Performance Metric Guidance" for "quickly"
and "SWEHB 5.09 - Specific" for "low," not "NPR 7150.2 §4.1" — citing the
NPR clause would technically look like a citation but would not actually
support the claim being made, which is exactly the kind of ungrounded-but-
plausible-looking citation the success criterion is trying to rule out.

## Should it propose a rewrite?

Yes, but with the same discipline `docs/requirement_rewrites.md` already
established: propose the *structure* of a fix, and use an explicit
`[... TBD by stakeholder]` placeholder rather than inventing a number or
definition that no one has actually engineered. Every one of the six worked
rewrites in that document follows this rule — the only rewrite that is fully
"complete" without a placeholder is SFMC-REQ-010 (Compound Requirement),
because splitting a sentence into two IDs needs no new engineering fact,
while the other five (targeting accuracy, encryption standard, "critical
fault" criteria, reliability target, log capacity) all leave a bracketed
placeholder because the missing number or definition is domain knowledge the
requirement text does not and cannot contain. For SR-042, the honest rewrite
is structural, not a real threshold:

> "The spacecraft shall display a low-fuel warning when remaining fuel falls
> below [a threshold TBD by propulsion/safety stakeholder, e.g. a percentage
> of usable fuel capacity] within [a maximum notification latency TBD by
> stakeholder]."

Note this happens to reconstruct the *shape* SFMC-REQ-008/009 actually ended
up with (percentage threshold + explicit display/alarm behavior) — which is
a good sanity check that the placeholder-based rewrite approach converges on
the same structure real engineers converged on, without the LLM having had
to invent the 15%/5% figures themselves.

## How should it distinguish a definite defect from something that merely needs human review?

This is really two different kinds of confidence, and the manual review data
shows the line clearly:

- **Structural/syntactic defects the model can flag with high confidence on
  text alone**: Compound Requirement (an "and" joining two independently-
  verifiable obligations — SFMC-REQ-010), Unverifiable Behavior (absolute
  words like "never"/"always," or unfalsifiable escape clauses like
  "whenever possible" — SFMC-REQ-040, -043), and the *presence* of an
  unquantified performance word or missing-number pattern (SFMC-REQ-006,
  -016, -021, -037, -047). These are pattern-detectable: the taxonomy's own
  Detection Questions for each category are phrased as yes/no checks
  answerable from the sentence (and, for Undefined Term, from the rest of
  the SRS) alone.
- **What genuinely needs a human/domain expert**: the *correct value* to fill
  in. Every single "Proposed Revision" cell in `docs/manual_requirement_review.csv`
  for a Missing Numerical Bound or Unquantified Performance Criterion row
  says, in some form, "we do not have enough information to propose specific
  criteria" or "no specific value can be proposed without further input."
  That is the honest boundary: the model can be highly confident *that*
  SR-042 is defective (quantifiable claim, no quantity given) while having
  zero basis for proposing *what* the fuel threshold or response-time bound
  should actually be — that number is a propulsion/safety engineering
  decision, exactly like SFMC-REQ-016's targeting accuracy or
  SFMC-REQ-047's log capacity.

So the distinguishing rule is: **category assignment is a text-pattern
judgment the model can make with high confidence; the specific missing fact
is a domain judgment the model should never fabricate, and should route to a
human via an explicit placeholder and a stated "Question requiring
stakeholder clarification" instead.**

## How could we tell whether the LLM's critique was correct?

The manual process itself is the ground truth we already have: all 54 rows
of `docs/manual_requirement_review.csv` (19 NEEDS REVIEW, 35 ACCEPTABLE) form
a human-labeled benchmark we could score an LLM reviewer against today,
which is exactly the "Ground-Truth Benchmark" success criterion in
`Challenge-Project-Overview.md`. Concretely, correctness could be checked
along three axes that map onto that document's stated metrics:
1. **Assessment agreement** — did the model's ACCEPTABLE/NEEDS REVIEW match
   the human label (this is precision/recall against seeded gaps).
2. **Category agreement** — for NEEDS REVIEW rows, did the model pick the
   same one of the five taxonomy categories (or a defensible additional one
   we hadn't seen)?
3. **Citation groundedness** — does the cited clause ID actually exist in
   the corpus (`data/npr7150_clauses.csv` / `data/swehb_5_09_guidance.csv`),
   and is it INDIVIDUAL-level guidance that genuinely supports the claim
   being made, rather than a PROCESS-level clause cited for a sentence-level
   finding? This directly operationalizes the "zero ungrounded or
   hallucinated verdicts" criterion.

For SR-042 specifically, since it isn't a real SRS row, a fair check is
whether the model's *category and citation* for SR-042 line up with the
category and citation the human reviewers actually gave SFMC-REQ-008/009's
predecessor problems and SFMC-REQ-037 ("without noticeable delay" —
already-graded as Unquantified Performance Criterion / Performance Metric
Guidance).

## What information might be impossible to determine from the requirement alone?

Several things the manual review needed came from *outside* the single
sentence, and some come from outside the SRS entirely:

- **Whether a term is truly undefined** requires scanning the rest of the
  document (a glossary entry, a numeric threshold stated elsewhere, an
  Open Item). SR-042's "low" cannot be judged in isolation — only by knowing
  SFMC-REQ-008/009 exist (or don't) elsewhere in the same SRS.
- **The actual correct numeric threshold or classification boundary.**
  No amount of reading SR-042 tells you whether the right fuel-warning
  threshold is 15%, 10%, or something mission-specific — that is a
  propulsion/safety engineering fact not contained in, or derivable from,
  requirement text, exactly as every "TBD by stakeholder" placeholder in
  `docs/requirement_rewrites.md` documents.
- **Set-level / document-level properties.** `docs/nasa_guidance_analysis.csv`
  classifies concepts like "Prioritized" (is this function critical vs.
  optional *relative to the others*) and "Decomposed vs. Derived" as SET-
  level: "you cannot tell if one requirement is 'prioritized' by reading it
  alone; you need the whole set." A single requirement can never answer a
  SET-level question by itself, no matter how much context is given about
  that one sentence.
- **Whether the PM actually ran the underlying process** (elicited the
  requirement properly, traced it to a parent need, validated it against
  the customer's operating environment) — these are the PROCESS-level NPR
  §4.1 obligations, and per `docs/nasa_guidance_analysis.csv` they describe
  an *activity performed by people*, not something a requirement sentence's
  text can attest to either way.
- **Real-world engineering adequacy of a number, once supplied.** Even after
  a human fills in "15%," nothing in the requirement text (or in SWEHB 5.09)
  can tell an LLM whether 15% is actually a *safe* margin for this
  spacecraft's fuel system — that is outside the scope of requirements-
  quality review entirely and belongs to a different kind of engineering
  analysis.
