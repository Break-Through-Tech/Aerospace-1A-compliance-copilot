import pandas as pd
import pytest

from compliance_copilot.evaluation import (
    evaluate_predictions,
    evaluate_retrieval,
    validate_benchmark,
)


def frame(labels):
    return pd.DataFrame(
        [
            {
                "requirement_id": "SFMC-REQ-{:03d}".format(i + 1),
                "swe_id": "SWE-210",
                "verdict": label,
                "assessment_scope": "srs_evidence",
            }
            for i, label in enumerate(labels)
        ]
    )


def test_reviews_are_missed_gaps_and_metrics_have_known_values():
    result = evaluate_predictions(
        frame(["Gap", "Gap", "Meets", "Partial"]), frame(["Gap", "REVIEW", "Gap", "Partial"])
    )
    assert result["decision_coverage"] == 0.75
    assert result["accuracy_including_reviews"] == 0.5
    assert result["gap_detection"]["precision"] == 0.5
    assert result["gap_detection"]["recall"] == 0.5
    assert result["confusion_matrix"]["Gap"]["REVIEW"] == 1


def test_benchmark_requires_compatible_scope_and_unique_pairs():
    benchmark = frame(["Gap"])
    with pytest.raises(ValueError, match="Duplicate"):
        validate_benchmark(pd.concat([benchmark, benchmark]))
    benchmark["assessment_scope"] = "full_clause_compliance"
    with pytest.raises(ValueError, match="scope"):
        validate_benchmark(benchmark)


def test_tuning_and_test_splits_are_not_silently_mixed():
    benchmark = frame(["Gap", "Meets"])
    benchmark["split"] = ["tune", "test"]
    with pytest.raises(ValueError, match="split"):
        validate_benchmark(benchmark)
    assert len(validate_benchmark(benchmark, split="test")) == 1


def test_missing_prediction_is_an_error_instead_of_inflating_metrics():
    with pytest.raises(ValueError, match="Missing predictions"):
        evaluate_predictions(frame(["Gap", "Meets"]), frame(["Gap"]))


def test_retrieval_metrics_do_not_treat_unlabeled_candidates_as_wrong():
    benchmark = frame(["Gap", "Partial"])
    matches = pd.DataFrame(
        [
            {
                "requirement_id": "SFMC-REQ-001",
                "swe_id": "SWE-210",
                "retrieval_status": "CANDIDATE",
            },
            {
                "requirement_id": "SFMC-REQ-001",
                "swe_id": "SWE-157",
                "retrieval_status": "CANDIDATE",
            },
            {
                "requirement_id": "SFMC-REQ-002",
                "swe_id": None,
                "retrieval_status": "NO_LEXICAL_MATCH",
            },
        ]
    )
    result = evaluate_retrieval(benchmark, matches)
    assert result["pair_recall_at_k"] == 0.5
    assert result["precision"] is None
