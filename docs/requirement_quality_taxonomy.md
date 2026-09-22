# Requirement Quality Taxonomy

## Purpose

Activity 3 produced 19 individual "NEEDS REVIEW" findings against the Starhawk
SFMC Software Requirements Specification (54 requirements reviewed, `docs/manual_requirement_review.csv`).
Read one at a time, those findings look like one-off observations — "'quickly'
has no defined limit," "'safe' is undefined," "this sentence bundles two
obligations." Read together, they cluster into a small number of recurring
*problem types*. This document names and defines those types.

The point of generalizing is that a named, defined problem type is something
repeatable: a category, not a one-time comment. Each definition below is
written so that a reviewer — human or an automated Compliance Copilot check —
can take a requirement sentence they have never seen before and ask a fixed
set of *Detection Questions* to decide whether that requirement exhibits the
problem, without needing the specific wording ("safe," "quickly," "critical")
that happened to trigger the original observation. That is the generalization
the Sprint Packet asks for: turning "'quickly' has no defined limit" into
"Unquantified Performance Criterion," a concept that also catches "extremely
accurate," "without noticeable delay," and any future requirement with the
same shape. Each category is also grounded in the actual NASA guidance
(SWEHB 5.09 characteristics, cited in `data/swehb_5_09_guidance.csv` and
analyzed in `docs/nasa_guidance_analysis.csv`) that the manual review already
cited as the underlying rule being violated, so the taxonomy stays traceable
to a real source rather than an invented standard.

Five distinct Issue Category values appear across the 19 NEEDS REVIEW rows.
No category below was invented beyond what the data actually shows, and none
of the five that appear has been omitted.

---

## 1. Undefined Term

**Definition:** The requirement's pass/fail behavior hinges on a word or
phrase (an adjective, a classification, or a named condition) that is never
defined anywhere in the SRS — no glossary entry, no threshold, no
enumerated criteria — leaving the reader to guess what qualifies. This is
distinct from *Unquantified Performance Criterion* in that the missing
information is a categorical/definitional boundary ("which faults count as
critical?", "which spacecraft count as friendly?") rather than a missing
number on an otherwise-numeric performance attribute.

**Why It Matters:** A requirement built on an undefined term cannot be
independently verified — two testers (or two developers) can reach opposite
conclusions about whether a given case satisfies it, because they are each
supplying their own private definition. It also hides missing engineering
analysis: "critical fault" sounds like a requirement, but the actual
engineering work (a fault taxonomy) hasn't been done yet. Left undefined, the
term gets defined implicitly and inconsistently by whichever engineer happens
to implement or test that requirement.

**Example:** SFMC-REQ-030 — "critical fault" is never distinguished from the
general faults already covered by SFMC-REQ-027/028/029, and the SRS's own
Open Item #3 flags this explicitly. Ten other NEEDS REVIEW requirements share
this same category: SFMC-REQ-004 ("safe," "efficient"), SFMC-REQ-015
("friendly spacecraft"), SFMC-REQ-018 ("greatest danger"), SFMC-REQ-025
("important" communications), SFMC-REQ-032 ("nonessential spacecraft
functions," and an SRS scope gap around "life-support"), SFMC-REQ-033
("seriously damaged," "safest destination"), SFMC-REQ-034 ("safe location"),
SFMC-REQ-041 ("recoverable" fault), SFMC-REQ-042 ("important mission data"),
and SFMC-REQ-050 ("state-of-the-art").

**NASA Basis:** SWEHB 5.09 - Specific, cited on all 11 rows in this category
(several rows additionally cite Testable, Measurable, or Complete). Per
`data/swehb_5_09_guidance.csv`: "A well-written requirement is clear and
unambiguous -- it avoids subjective terms ... and states exactly what is
required."

**Detection Questions:**
- Does this requirement contain an adjective, category label, or named
  condition (e.g., "critical," "friendly," "important," "safe") that isn't
  defined elsewhere in this document?
- If two engineers each independently decided whether a specific real-world
  case satisfies this term, is there a real chance they'd disagree?
- Is there a glossary entry, a numeric threshold, or an enumerated list
  anywhere in the SRS that pins down this term's meaning?
- Does an "Open Item" or similar unresolved-issue list in the source
  document already flag this exact term as undefined?

---

## 2. Unquantified Performance Criterion

**Definition:** The requirement describes a performance, timing, accuracy,
or proximity attribute using a subjective qualitative word ("quickly,"
"extremely accurate," "reasonably close," "without noticeable delay")
instead of a number, tolerance, or measurable threshold.

**Why It Matters:** Performance requirements exist to be designed against
and tested against. Without a number, there is nothing for a designer to
size the system to and nothing for a tester to measure against — "quickly
enough" for one reviewer might be too slow for a pilot in combat. This
category is the exact generalization the Sprint Packet's own worked example
("'quickly' has no defined limit" → "Unquantified performance criterion")
describes, and it recurs across timing, distance, and accuracy attributes
alike, not just response time.

**Example:** SFMC-REQ-021 — "the system shall respond quickly to dangerous
threats" has no response-time threshold and no definition of "dangerous"
(the "dangerous" half of this same sentence is separately double-counted
under Undefined Term territory in the row's explanation, but the row's
recorded Issue Category is Unquantified Performance Criterion). Three other
NEEDS REVIEW requirements share this category: SFMC-REQ-006 ("reasonably
close" arrival tolerance), SFMC-REQ-016 ("extremely accurate" targeting),
and SFMC-REQ-037 ("without noticeable delay" command response).

**NASA Basis:** SWEHB 5.09 - Performance Metric Guidance, cited on 3 of the
4 rows (SFMC-REQ-016, 021, 037); SFMC-REQ-006 instead cites SWEHB 5.09 -
Specific and Measurable. Per `data/swehb_5_09_guidance.csv`: "Non-functional
and performance requirements should use precise, measurable metrics
(specific thresholds, e.g. response time, throughput, latency) rather than
vague, subjective terms like 'fast' or 'efficient.'"

**Detection Questions:**
- Does this requirement describe a speed, latency, accuracy, distance, or
  similar continuous attribute using an adjective/adverb instead of a
  number and unit?
- Could you write a numeric pass/fail test for this requirement today,
  using only what's stated in the SRS?
- Is there a stated tolerance, threshold, or range, or would a tester have
  to supply their own judgment call?
- Does a comparable requirement elsewhere in the same document quantify the
  same kind of attribute (e.g., a different display-latency requirement
  gives "1 second" while this one doesn't give any number)?

---

## 3. Unverifiable Behavior

**Definition:** The requirement uses an absolute claim ("never," "always")
or an unfalsifiable escape clause ("whenever possible," "as needed") that no
finite test suite can actually prove true, because a passing test run only
shows the failure wasn't observed yet, and an escape clause can excuse any
failure after the fact with no way to disprove the excuse.

**Why It Matters:** These requirements read as stringent but are actually
untestable as written — they give no way to close out verification with
confidence, and an "as possible"-style clause can be used to explain away
any field failure without ever being in violation on paper. This is a
distinct failure mode from a missing number: even a fully quantified rewrite
of "never crashes" (e.g., a reliability target/MTBF) is what's needed, not
just a bigger number attached to the same absolute claim.

**Example:** SFMC-REQ-040 — "the software shall never crash" cannot be
proven by testing; only a bounded reliability target (e.g., MTBF, maximum
crash rate) is provable. SFMC-REQ-043 shares this category: "the SFMC shall
continue operating whenever possible" is an unfalsifiable escape clause with
no enumerated list of the subsystem-loss combinations it actually applies to.

**NASA Basis:** SWEHB 5.09 - Testable, cited on both rows. Per
`data/swehb_5_09_guidance.csv`: "A well-written requirement is specific and
verifiable: it must be clear enough to be tested against a defined,
objective success criterion."

**Detection Questions:**
- Does this requirement use an absolute word ("never," "always," "100%,"
  "any") for a property that can only be sampled, not exhaustively proven?
- Does it use a qualifying escape phrase ("whenever possible," "where
  practical," "as needed") that has no accompanying list of the specific
  conditions it covers?
- Could a real-world failure of this requirement always be explained away
  as "not possible in that case," with no way to prove otherwise?
- Would a rewritten version with a bounded target (a rate, a percentage, an
  enumerated condition list) actually be verifiable where the current
  wording isn't?

---

## 4. Compound Requirement

**Definition:** A single requirement sentence bundles two or more distinct
obligations — typically joined by "and" — where the obligations are
independently verifiable (or not) and one of them fails a different quality
check (often Undefined Term) while the other is fine on its own.

**Why It Matters:** Bundling obligations into one requirement statement
hides partial compliance: an implementation could satisfy half the sentence
and fail the other half, and there is no way to trace pass/fail, verification
method, or a later change to just the affected half without first splitting
it. It also means a single well-formed obligation gets contaminated by
being yoked to a poorly-specified one, and reviewers may pass or fail the
entire compound sentence based on only the clause they focused on.

**Example:** SFMC-REQ-010 — "the system shall notify the pilot of an engine
failure and take appropriate corrective action" bundles a clear, testable
notification obligation with an undefined, untestable "appropriate
corrective action" obligation (no failure-mode-to-action mapping exists
anywhere in the SRS). This is currently the only NEEDS REVIEW requirement
recorded under this category.

**NASA Basis:** SWEHB 5.09 - Testable, per the row's citation. The
underlying rationale also implicates SWEHB 5.09 - Complete (each obligation
should be a self-contained, fully scoped statement), though the review row
itself cited only Testable.

**Detection Questions:**
- Does this requirement contain more than one independent "shall" obligation
  joined by "and" (or expressed as a list) inside a single requirement ID?
- Could one half of the sentence be satisfied while the other half is not?
- Would splitting the sentence into separate requirement IDs change how it
  would be verified (e.g., different verification methods, different
  owners, different acceptance criteria per half)?
- Does one clause of the compound sentence independently fail a different
  quality check (e.g., an undefined term) that the other clause does not?

---

## 5. Missing Numerical Bound

**Definition:** The requirement specifies a capacity, quantity, or resource
allocation using a qualitative sufficiency claim ("sufficient storage,"
"adequate margin") instead of a concrete number. This is a close relative of
*Unquantified Performance Criterion* but applies specifically to sizing/
capacity attributes (how much of something is needed) rather than to speed,
accuracy, or timing attributes (how fast or how precisely something must be
done).

**Why It Matters:** A capacity claim without a number cannot be designed
against — hardware/storage sizing, memory budgets, and buffer allocations
all require a concrete figure, and "sufficient" invites under-provisioning
that only surfaces as a failure in the field (e.g., a mission log that fills
up mid-mission) rather than at design or test time.

**Example:** SFMC-REQ-047 — "the SFMC shall provide sufficient storage for
an entire mission's fault log" gives no numeric capacity, even though the
SRS elsewhere fixes a 72-hour maximum mission duration (SFMC-REQ-039) that
could anchor a derived figure. The SRS's own Open Item #6 flags the missing
storage capacity explicitly. This is currently the only NEEDS REVIEW
requirement recorded under this category.

**NASA Basis:** SWEHB 5.09 - Measurable, per the row's citation. Per
`data/swehb_5_09_guidance.csv`: "A well-written requirement is measurable:
derived and decomposed requirements should remain testable and measurable
so conformance can be objectively evaluated."

**Detection Questions:**
- Does this requirement describe a capacity, quantity, or resource
  allocation ("storage," "bandwidth," "memory," "margin") using a
  qualitative sufficiency word instead of a number and unit?
- Could an implementer size a buffer, disk allocation, or budget directly
  from this requirement's text alone?
- Do other requirements elsewhere in the SRS already establish a bounding
  figure (e.g., a maximum duration or rate) that this requirement could
  reference to derive its own numeric bound, but currently doesn't?

---

## Summary Table

| # | Category Name | NEEDS REVIEW Requirements Covered | Count |
|---|---|---|---|
| 1 | Undefined Term | SFMC-REQ-004, -015, -018, -025, -030, -032, -033, -034, -041, -042, -050 | 11 |
| 2 | Unquantified Performance Criterion | SFMC-REQ-006, -016, -021, -037 | 4 |
| 3 | Unverifiable Behavior | SFMC-REQ-040, -043 | 2 |
| 4 | Compound Requirement | SFMC-REQ-010 | 1 |
| 5 | Missing Numerical Bound | SFMC-REQ-047 | 1 |
| | **Total** | | **19** |

All 19 NEEDS REVIEW rows from `docs/manual_requirement_review.csv` are
accounted for above, each counted under exactly the Issue Category value
recorded for it in that file; no requirement was double-counted across
categories.
