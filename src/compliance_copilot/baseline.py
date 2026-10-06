"""Explicit, limited SRS evidence checks. Unsupported cases abstain as REVIEW.

Meets/Partial/Gap describe only assessed_provision, never complete NASA compliance.
Document checks run independently of retrieval so missing text cannot hide a gap.
"""

import re

import pandas as pd

from .data import validate_clauses, validate_table


AMBIGUITY_RULES = {
    "quickly": "Specify a measurable response-time limit.",
    "immediately": "Clarify the maximum allowed response time.",
    "without noticeable delay": "Response time is subjective.",
    "reasonably close": "Define an acceptable arrival distance.",
    "extremely accurate": "Define the accuracy metric and limit.",
    "important": "Identify exactly which data or communications are covered.",
    "appropriate corrective action": "Define the required corrective action.",
    "whenever possible": "Define when continued operation is required.",
    "seriously damaged": "Define the condition that triggers this behavior.",
    "sufficient storage": "Define storage capacity or the expected workload.",
    "state-of-the-art": "Identify the applicable security criteria.",
    "securely encrypted": "Identify the applicable encryption requirements.",
    "safe and efficient": "Define safety and efficiency criteria.",
    "safest destination": "Define destination selection criteria.",
    "safe location": "Define what qualifies as a safe location.",
    "friendly spacecraft": "Define friendly, hostile, and unknown classification criteria.",
    "greatest danger": "Define threat-priority factors and ranking method.",
    "nonessential spacecraft functions": "Identify functions that may be delayed or disabled.",
}
ASSESSMENT_COLUMNS = [
    "requirement_id",
    "swe_id",
    "clause_id",
    "clause_text",
    "srs_scope",
    "assessment_scope",
    "assessed_provision",
    "verdict",
    "evidence",
    "missing_evidence",
    "reason",
    "findings",
]
PROVISIONS = {
    "SWE-034": "Explicit software acceptance criteria in the supplied SRS",
    "SWE-050": "Recorded requirements and approval evidence in the supplied SRS",
    "SWE-052": "Explicit parent-requirement links for the SRS requirements",
    "SWE-053": "Requirements revision history or change records in the supplied SRS",
    "SWE-157": "SRS access-protection requirements; NASA-STD-1006 conformance is unverified",
    "SWE-184": "Safety constraints, controls, mitigations and assumptions stated in the SRS",
    "SWE-210": "Requirements for collecting, reporting and storing adversarial-detection data",
}
NEGATION = re.compile(r"\b(?:shall|must|will|does|do|should)\s+(?:not|never)\b", re.I)
ADVERSARIAL = re.compile(
    r"\b(?:adversarial|intrusion|cyberattack|cyber.attack|unauthorized access)\b", re.I
)
DETECTION = re.compile(r"\bdetect(?:ion|ed|ing|s)?\b", re.I)
ACCESS_CONTROL = re.compile(
    r"\b(?:verify|authenticate)\b.*\b(?:pilot|user|identity|authorized)\b"
    r"|\breject\b.*\bunauthorized\s+(?:commands|access)\b",
    re.I,
)
SAFETY_CONTROL = re.compile(
    r"\bprevent\b.*\b(?:weapon|firing|hazard)\b|\b(?:safety constraint|safety control|hazard mitigation)\b",
    re.I,
)


def ambiguity_findings(text):
    return [
        "{}: {}".format(phrase, reason)
        for phrase, reason in AMBIGUITY_RULES.items()
        if re.search(r"\b" + re.escape(phrase) + r"\b", text, re.I)
    ]


def keyword_findings(requirements):
    frame = requirements.copy()
    frame["findings"] = frame.text.map(ambiguity_findings)
    frame["status"] = frame.findings.map(lambda v: "NEEDS_REVIEW" if v else "NO_RULE_MATCH")
    return frame


def _result(
    requirement_id,
    clause,
    verdict="REVIEW",
    evidence=None,
    missing=None,
    reason="No supported evidence rule for this pair.",
    findings=None,
):
    return {
        "requirement_id": requirement_id,
        "swe_id": clause["swe_id"],
        "clause_id": clause["clause_id"],
        "clause_text": clause["text"],
        "srs_scope": clause["srs_scope"],
        "assessment_scope": "srs_evidence",
        "assessed_provision": PROVISIONS.get(
            clause["swe_id"], "No implemented SRS provision check"
        ),
        "verdict": verdict,
        "evidence": evidence or [],
        "missing_evidence": missing or [],
        "reason": reason,
        "findings": findings or [],
    }


def _adversarial_data(texts):
    # Data-management verbs must occur in the same requirement as adversarial detection.
    relevant = [
        t
        for t in texts
        if ADVERSARIAL.search(t)
        and DETECTION.search(t)
        and re.search(r"\b(?:shall|must)\b", t, re.I)
    ]
    if not relevant:
        return (
            "Gap",
            [],
            ["Explicit adversarial-detection data requirements"],
            "No matching data requirement in assessed text.",
        )
    if any(NEGATION.search(t) for t in relevant):
        return "REVIEW", relevant, [], "Negated data requirements need human interpretation."
    if any(
        re.search(r"\b(?:may|can|could|might|should)\b", t, re.I) or ambiguity_findings(t)
        for t in relevant
    ):
        return (
            "REVIEW",
            relevant,
            [],
            "Optional or ambiguous data obligations need human interpretation.",
        )
    checks = {
        "collection": r"\b(?:collect\w*|record\w*|log\w*)\b",
        "reporting": r"\b(?:report\w*|notify|notification\w*|alert\w*)\b",
        "storage": r"\b(?:stor\w*|retain\w*|persist\w*)\b",
    }
    missing = [
        name
        for name, pattern in checks.items()
        if not any(re.search(pattern, t, re.I) for t in relevant)
    ]
    return (
        "Meets" if not missing else "Partial" if len(missing) < 3 else "Gap",
        relevant,
        missing,
        "Checked explicit collection, reporting and storage wording for adversarial-detection data.",
    )


class EvidenceBaseline:
    def __init__(self, clauses):
        validate_clauses(clauses)
        self.clauses = {row["swe_id"]: row for row in clauses.to_dict("records")}

    def assess_pair(self, requirement, swe_id):
        if swe_id not in self.clauses:
            raise ValueError("Unknown SWE ID: {}".format(swe_id))
        clause = self.clauses[swe_id]
        text = requirement["text"]
        findings = ambiguity_findings(text)
        base = _result(requirement["requirement_id"], clause, findings=findings)
        if clause["srs_scope"] == "out":
            base["reason"] = "Clause is outside the curated SRS scope."
        elif swe_id == "SWE-210" and ADVERSARIAL.search(text) and DETECTION.search(text):
            verdict, evidence, missing, reason = _adversarial_data([text])
            base.update(verdict=verdict, evidence=evidence, missing_evidence=missing, reason=reason)
        elif swe_id in ("SWE-157", "SWE-184"):
            pattern = ACCESS_CONTROL if swe_id == "SWE-157" else SAFETY_CONTROL
            if pattern.search(text) and re.search(r"\b(?:shall|must)\b", text, re.I):
                if NEGATION.search(text):
                    base.update(evidence=[text], reason="Negation requires human interpretation.")
                else:
                    base.update(
                        verdict="Partial",
                        evidence=[text],
                        missing_evidence=[
                            "Remaining clause obligations require document or external evidence"
                        ],
                        reason="Explicit protection/control requirement supports part of the SRS provision.",
                    )
        return base

    def assess_pairs(self, requirements, pairs):
        validate_table(requirements, ["requirement_id", "title", "text"], ["requirement_id"])
        lookup = {r["requirement_id"]: r for r in requirements.to_dict("records")}
        rows = []
        for pair in pairs[["requirement_id", "swe_id"]].drop_duplicates().to_dict("records"):
            if pair["requirement_id"] not in lookup:
                raise ValueError("Unknown requirement ID: {}".format(pair["requirement_id"]))
            rows.append(self.assess_pair(lookup[pair["requirement_id"]], pair["swe_id"]))
        return pd.DataFrame(rows, columns=ASSESSMENT_COLUMNS)

    def assess_document(self, requirements, srs_text):
        """DOCUMENT results assess missing global evidence, not individual sentences."""
        texts = list(requirements.text)
        rows = []
        for swe_id, clause in self.clauses.items():
            row = _result("DOCUMENT", clause, reason="No implemented document evidence rule.")
            if clause["srs_scope"] == "out":
                continue
            if swe_id == "SWE-210":
                verdict, evidence, missing, reason = _adversarial_data(texts)
                row.update(
                    verdict=verdict, evidence=evidence, missing_evidence=missing, reason=reason
                )
            elif swe_id == "SWE-050":
                row.update(
                    verdict="Partial",
                    evidence=list(requirements.requirement_id),
                    missing_evidence=["Verified approval and ongoing requirements maintenance"],
                    reason="Requirements are recorded with stable IDs; approval is not inferred from metadata.",
                )
            elif swe_id == "SWE-052":
                # Only table rows qualify, not the SRS's list of unlinked mission needs.
                links = {}
                for line in srs_text.splitlines():
                    if line.lstrip().startswith("|") and re.search(r"\bMN-\d+\b", line):
                        for requirement_id in re.findall(r"SFMC-REQ-\d{3}", line):
                            links[requirement_id] = line.strip()
                missing = [r for r in requirements.requirement_id if r not in links]
                row.update(
                    verdict="Partial" if links else "Gap",
                    evidence=list(links.values()),
                    missing_evidence=missing
                    or ["Bidirectional linkage and traceability to other engineering artifacts"],
                    reason="Checks explicit requirement-to-parent links; full bidirectional traceability is unverified.",
                )
            elif swe_id == "SWE-034":
                row.update(missing_evidence=["Defined and documented software acceptance criteria"])
                if re.search(r"\b(?:acceptance criteria|pass criteria)\b", srs_text, re.I):
                    row.update(
                        reason="Acceptance-criteria wording found; adequacy needs human review."
                    )
                else:
                    row.update(
                        verdict="Gap",
                        reason="No explicit acceptance criteria found; numeric requirements alone are insufficient.",
                    )
            elif swe_id == "SWE-053":
                if re.search(r"\b(?:revision history|change history|change log)\b", srs_text, re.I):
                    row.update(
                        reason="Change-history wording found; entries and management require review."
                    )
                else:
                    row.update(
                        verdict="Gap",
                        missing_evidence=[
                            "Requirements change history or change-management record"
                        ],
                        reason="A version number alone does not document requirements changes.",
                    )
            elif swe_id in ("SWE-157", "SWE-184"):
                pattern = ACCESS_CONTROL if swe_id == "SWE-157" else SAFETY_CONTROL
                evidence = [t for t in texts if pattern.search(t) and not NEGATION.search(t)]
                row.update(
                    verdict="Partial" if evidence else "REVIEW",
                    evidence=evidence,
                    missing_evidence=[
                        "Complete provision evidence and any referenced standard conformance"
                    ],
                    reason="Aggregates explicit SRS protection/control evidence; does not verify implementation or full coverage.",
                )
            rows.append(row)
        return pd.DataFrame(rows, columns=ASSESSMENT_COLUMNS)
