import pandas as pd
import pytest

from compliance_copilot.baseline import EvidenceBaseline, keyword_findings
from compliance_copilot.data import load_inputs, parse_requirements, validate_clauses


def requirement(text):
    return {"requirement_id": "SFMC-REQ-001", "title": "Example", "text": text}


def test_original_srs_parser_and_keyword_flags_are_preserved(project_root):
    requirements, _, _ = load_inputs(project_root)
    assert len(requirements) == 54
    old = pd.read_csv(project_root / "notebooks/baseline_results.csv")
    new = keyword_findings(requirements)
    assert list(new.requirement_id) == list(old.requirement_id)
    assert list(new.text) == list(old.text)
    assert list(new.status) == list(old.status)


def test_duplicate_requirement_ids_are_rejected():
    text = "**SFMC-REQ-001 — Example**\nThe system shall log events.\n"
    with pytest.raises(ValueError, match="Duplicate"):
        parse_requirements(text + text)


def test_section_level_citation_is_valid(clauses):
    example = clauses.iloc[:1].copy()
    example["clause_id"] = "5.2"
    validate_clauses(example)


def test_negated_security_requirement_does_not_claim_protection(clauses):
    model = EvidenceBaseline(clauses)
    positive = model.assess_pair(requirement("The system shall authenticate the user."), "SWE-157")
    negative = model.assess_pair(
        requirement("The system shall not authenticate the user."), "SWE-157"
    )
    assert positive["verdict"] == "Partial"
    assert negative["verdict"] == "REVIEW"


@pytest.mark.parametrize(
    "text,verdict",
    [
        (
            "The system shall collect, report, and store data on detected adversarial actions.",
            "Meets",
        ),
        ("The system shall record data on detected adversarial actions.", "Partial"),
        ("The system shall detect adversarial actions.", "Gap"),
        (
            "The system shall not collect, report, or store data on detected adversarial actions.",
            "REVIEW",
        ),
        (
            "The system shall detect adversarial actions and may collect, report, and store data.",
            "REVIEW",
        ),
        (
            "The system shall quickly collect, report, and store data on detected adversarial actions.",
            "REVIEW",
        ),
        ("The system shall store mission events.", "REVIEW"),
    ],
)
def test_adversarial_data_requires_relevant_detection_and_each_operation(clauses, text, verdict):
    result = EvidenceBaseline(clauses).assess_pair(requirement(text), "SWE-210")
    assert result["verdict"] == verdict
    assert result["clause_id"] == "3.11.8"


def test_unsupported_clause_and_unrelated_text_abstain(clauses):
    result = EvidenceBaseline(clauses).assess_pair(
        requirement("The display shall refresh."), "SWE-134"
    )
    assert result["verdict"] == "REVIEW"
    assert result["assessment_scope"] == "srs_evidence"


def test_document_checks_do_not_confuse_mission_needs_with_trace_links(project_root):
    requirements, clauses, text = load_inputs(project_root)
    results = EvidenceBaseline(clauses).assess_document(requirements, text).set_index("swe_id")
    assert results.loc["SWE-052", "verdict"] == "Gap"
    assert len(results.loc["SWE-052", "missing_evidence"]) == 54
    assert results.loc["SWE-210", "verdict"] == "Gap"
    assert results.loc["SWE-053", "verdict"] == "Gap"
    assert results.loc["SWE-050", "verdict"] == "Partial"  # IDs do not prove approval.
