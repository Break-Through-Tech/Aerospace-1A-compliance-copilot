# Requirement Rewrites (Activity 5)

## Purpose

Activity 3 identified 19 "NEEDS REVIEW" requirements in the Starhawk SFMC SRS
(`docs/manual_requirement_review.csv`); Activity 4 generalized those findings
into five taxonomy categories (`docs/requirement_quality_taxonomy.md`). This
document takes the next step: **correcting**, not just identifying, a
selection of those requirements.

Six requirements were selected, spanning all five taxonomy categories (the
packet asks for at least five requirements across at least three categories):

| Requirement | Taxonomy Category |
|---|---|
| SFMC-REQ-010 | Compound Requirement |
| SFMC-REQ-016 | Unquantified Performance Criterion |
| SFMC-REQ-025 | Undefined Term |
| SFMC-REQ-030 | Undefined Term |
| SFMC-REQ-040 | Unverifiable Behavior |
| SFMC-REQ-047 | Missing Numerical Bound |

**A note on method, per the Sprint Packet's own guidance:** for requirements
where the actual defect is a missing categorical definition or a missing
performance/capacity number that no one has supplied, the "Proposed
revision" below shows the *structure* of a corrected requirement with a
bracketed placeholder (e.g., `[accuracy TBD by stakeholder]`) rather than an
invented number. Inventing a number to make a rewrite look finished would
just relocate the ambiguity — a reviewer would no longer be able to tell
that the figure was never actually engineered. SFMC-REQ-010 is the one
selection below where a real, complete fix *is* possible without inventing
any new engineering fact, because splitting a compound sentence into its two
constituent obligations requires no new information — only structural
separation.

---

## 1. SFMC-REQ-010 — Engine Failure

**Original requirement:**
> If the SFMC detects a failure of a main engine, it shall notify the pilot and take appropriate corrective action.

**Identified problem (Compound Requirement):** The sentence bundles two
independent obligations joined by "and": (1) notify the pilot of the
failure — fully specified and independently testable — and (2) "take
appropriate corrective action" — undefined, since the SRS never maps engine
failure modes to specific corrective actions anywhere. As currently written,
an implementation could satisfy the notification half while the "corrective
action" half is unverifiable, and a reviewer grading the sentence as a whole
could pass or fail it based on only the clause they focused on.

**Proposed revision:** Split into two separate requirement IDs so each has
its own verification method:

> **SFMC-REQ-010a — Engine Failure Notification.** If the SFMC detects a failure of a main engine, it shall notify the pilot of the failure.
>
> **SFMC-REQ-010b — Engine Failure Corrective Action.** If the SFMC detects a failure of a main engine, the SFMC shall take the corrective action specified in [the engine-failure corrective-action mapping, TBD by propulsion engineering — a table of failure mode → required action, e.g., shut down the affected engine, cut fuel flow, isolate the failed engine's feed line] for the specific failure mode detected.

**Assumptions made:** None beyond the mechanical split itself — no new
timing, wording, or behavior was added to SFMC-REQ-010a; it is the
notification clause of the original sentence, verbatim in intent. No
corrective-action content was invented for SFMC-REQ-010b; it was left as an
explicit placeholder referencing a mapping that does not yet exist in the
SRS.

**Questions requiring stakeholder clarification:** What are the specific
main-engine failure modes the SFMC must be able to detect, and what is the
required corrective action for each mode? This is propulsion-engineering
input; no such mapping exists anywhere else in the SRS to draw from.

---

## 2. SFMC-REQ-016 — Targeting Performance

**Original requirement:**
> The targeting system shall be extremely accurate.

**Identified problem (Unquantified Performance Criterion):** "Extremely
accurate" is a subjective description of an accuracy attribute with no
numeric metric (e.g., miss distance, hit probability), no stated range or
operating conditions, and no way to write a pass/fail test from the text
alone. The SRS's own Open Item #7 flags "required targeting accuracy" as
explicitly unresolved — this is not an oversight in the review, it is a
gap the original authors already knew about.

**Proposed revision:**
> The targeting system shall achieve [a targeting accuracy metric TBD by stakeholder — e.g., a maximum miss distance in meters, or a minimum hit probability] when engaging a target at [range/engagement conditions TBD by stakeholder].

**Assumptions made:** None. No miss-distance figure, hit-probability value,
or engagement range was invented; the revision only fixes the *shape* of the
requirement (a named metric plus a number plus stated conditions) that a
real accuracy requirement needs.

**Questions requiring stakeholder clarification:** Per Open Item #7 — what
is the required targeting accuracy, expressed as which metric (miss
distance, circular error probable, hit probability, or similar), at what
target range/engagement geometry, and under what conditions (e.g., target
maneuvering vs. stationary)? This requires input from weapons-systems
engineering, since no accuracy figure appears anywhere else in the SRS to
derive one from.

---

## 3. SFMC-REQ-025 — Secure Communications

**Original requirement:**
> All important communications shall be securely encrypted.

**Identified problem (Undefined Term):** Two separate undefined terms sit
in one short sentence. "Important" communications are never defined or
distinguished from routine ones anywhere in the SRS (Open Item #4 flags this
directly), so it is unclear which messages the requirement even applies to.
"Securely encrypted" names no algorithm, key length, or standard (Open Item
#9), so even for messages everyone agrees are "important," there is no
objective way to check compliance.

**Proposed revision:**
> All communications meeting [the "important communication" classification criteria, TBD by stakeholder] shall be encrypted using [the required encryption algorithm/standard, TBD by stakeholder — e.g., a specific FIPS-approved cipher suite and minimum key length].

**Assumptions made:** None. No message category and no cipher suite or key
length was invented; both placeholders mark information the SRS itself
already lists as open.

**Questions requiring stakeholder clarification:** (1) Per Open Item #4 —
what criteria distinguish an "important" communication from a routine one
(e.g., message type, mission-criticality, classification level)? (2) Per
Open Item #9 — what encryption algorithm(s)/standard(s) are required (e.g.,
a specific NIST/FIPS-approved cipher, minimum key length)? This needs input
from the communications subsystem owner and a cybersecurity stakeholder,
respectively.

---

## 4. SFMC-REQ-030 — Critical Faults

**Original requirement:**
> The SFMC shall immediately notify the pilot of all critical faults.

**Identified problem (Undefined Term):** "Critical fault" is never
distinguished from the general faults already covered by SFMC-REQ-027
(fault display within 1 second), SFMC-REQ-028, and SFMC-REQ-029 — the SRS's
own Open Item #3 flags this gap directly. Separately, "immediately" is an
unquantified timing term, which stands out because SFMC-REQ-027 gives an
explicit 1-second bound for the general case this requirement is presumably
meant to tighten or specialize.

**Proposed revision:**
> The SFMC shall notify the pilot of any fault meeting [the "critical fault" classification criteria, TBD by stakeholder] within [a maximum notification latency, TBD by stakeholder — note SFMC-REQ-027 already establishes 1 second for general fault display; stakeholders should confirm whether that bound applies here, a tighter bound is required for critical faults specifically, or some other value applies].

**Assumptions made:** The revision assumes "critical fault" is meant as a
subset of the general fault category already covered by SFMC-REQ-027/028/029
(consistent with how the taxonomy document and the original review describe
it) — no new fault categories or examples were invented. The 1-second figure
from SFMC-REQ-027 is surfaced only as an existing reference point for
stakeholders to accept or override, not asserted as the answer; no new
number was invented for the critical-fault case.

**Questions requiring stakeholder clarification:** Per Open Item #3 — what
criteria distinguish a "critical" fault from the general faults already
covered elsewhere? And does the 1-second bound in SFMC-REQ-027 apply to
critical faults, or is a different (e.g., tighter) maximum latency required
given that "immediately" suggests something more urgent? This requires input
from a fault-management/safety engineer.

---

## 5. SFMC-REQ-040 — Software Failure

**Original requirement:**
> The SFMC software shall never crash during a mission.

**Identified problem (Unverifiable Behavior):** "Never" is an absolute
claim that no finite test campaign can prove true — passing tests only show
that a crash was not observed during testing, not that one cannot occur.
There is no reliability target (e.g., MTBF, maximum permitted crash rate)
that a tester could actually check an implementation against.

**Proposed revision:**
> The SFMC software shall maintain a reliability of at least [a reliability target, TBD by stakeholder — e.g., a Mean Time Between Failures (MTBF) figure, or a maximum permitted number of crashes] over a mission of up to 72 hours (per SFMC-REQ-039).

**Assumptions made:** The 72-hour mission-duration figure is not invented —
it is taken directly from SFMC-REQ-039, which already establishes it
elsewhere in the SRS, and is used here only to scope the reliability window,
not to supply the reliability number itself. No MTBF value or crash-rate
figure was invented.

**Questions requiring stakeholder clarification:** What quantitative
reliability target should replace "never crash" — a specific MTBF, a
maximum permitted crash count per mission, or a maximum permitted crash
rate? This is a reliability/safety-engineering determination; no such figure
exists anywhere else in the SRS to derive one from.

---

## 6. SFMC-REQ-047 — Log Capacity

**Original requirement:**
> The mission log shall contain sufficient storage for an entire mission.

**Identified problem (Missing Numerical Bound):** "Sufficient storage" is a
qualitative sizing claim with no concrete capacity figure — an implementer
cannot size a log partition or buffer from this text alone. The SRS's own
Open Item #6 flags the required log storage capacity as explicitly
unresolved.

**Proposed revision:**
> The mission log shall provide at least [a storage capacity, TBD by stakeholder — e.g., in MB/GB] of storage, sized to accommodate fault-log entries (per the fields listed in SFMC-REQ-029/SFMC-REQ-046) at the expected logging rate for the maximum mission duration of 72 hours (per SFMC-REQ-039).

**Assumptions made:** The 72-hour maximum mission duration is not invented
— it is SFMC-REQ-039's existing figure, referenced here (as the taxonomy
document itself suggests) as a scoping anchor for the eventual capacity
number, not as a substitute for it. No expected log-entry rate, entry size,
or final storage figure (MB/GB) was invented.

**Questions requiring stakeholder clarification:** Per Open Item #6 — what
is the required log storage capacity? Answering this also requires an
expected log-entry rate and average entry size (neither of which is
specified elsewhere in the SRS), so that a capacity figure can be derived
against the 72-hour mission ceiling. This needs input from a systems/storage
engineer.

---

## Confirmation

None of the proposed revisions above fabricate a numeric value. Every
number that appears (the 1-second bound referenced for SFMC-REQ-030, and
the 72-hour mission duration referenced for SFMC-REQ-040 and SFMC-REQ-047)
is quoted from an existing SRS requirement (SFMC-REQ-027 and SFMC-REQ-039,
respectively) and used only to scope or anchor a still-missing figure, never
asserted as the missing figure itself. Every place where a genuinely new
number or category definition would be needed (targeting accuracy,
encryption standard, "important"/"critical" classification criteria,
reliability target, log storage capacity, engine-failure corrective-action
mapping) is left as an explicit `[... TBD by stakeholder]` placeholder with
a corresponding question in that requirement's "Questions requiring
stakeholder clarification" section.
