import json

import pandas as pd

from compliance_copilot.pipeline import run_baseline


def test_real_corpus_exports_and_no_benchmark_claim(project_root, tmp_path):
    result = run_baseline(project_root, output_dir=tmp_path)
    assert result["metrics"]["evaluation_status"] == "awaiting_advisor_benchmark"
    assert result["matches"].requirement_id.nunique() == 54
    assert len(result["document_assessments"]) == 14
    citations = dict(zip(result["clauses"].swe_id, result["clauses"].clause_id))
    for row in result["assessments"].to_dict("records"):
        assert citations[row["swe_id"]] == row["clause_id"]
    for path in tmp_path.glob("*.json"):
        json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)),
        )
    exported = json.loads((tmp_path / "pair_assessments.json").read_text(encoding="utf-8"))
    assert isinstance(exported[0]["evidence"], list)


def test_supplied_synthetic_fixture_is_evaluated_independently_of_retrieval(project_root, tmp_path):
    # Hand-authored test fixture; not advisor ground truth or a performance benchmark.
    benchmark = tmp_path / "synthetic_test_fixture.csv"
    pd.DataFrame(
        [
            {
                "requirement_id": "DOCUMENT",
                "swe_id": "SWE-210",
                "verdict": "Gap",
                "assessment_scope": "srs_evidence",
            },
            {
                "requirement_id": "SFMC-REQ-049",
                "swe_id": "SWE-157",
                "verdict": "Partial",
                "assessment_scope": "srs_evidence",
            },
        ]
    ).to_csv(benchmark, index=False)
    result = run_baseline(project_root, tmp_path / "output", benchmark)
    assert result["metrics"]["classification"]["benchmark_rows"] == 2
    assert result["metrics"]["classification"]["accuracy_including_reviews"] == 1
    assert len(result["benchmark_predictions"]) == 2
    run_baseline(project_root, tmp_path / "output")
    assert not (tmp_path / "output/benchmark_predictions.csv").exists()
    assert not (tmp_path / "output/benchmark_predictions.json").exists()
