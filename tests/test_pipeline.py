import json
import runpy

import pandas as pd

from compliance_copilot.pipeline import run_baseline
from compliance_copilot.data import load_inputs


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


def test_existing_team_export_is_imported_without_reextracting(project_root, tmp_path):
    for relative in ["notebooks/N_PR_7150_002D_.pdf", "data/Starhawk Mission Computer SRS.md"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((project_root / relative).read_bytes())
    importer = runpy.run_path(str(project_root / "scripts/import_clauses.py"))["import_clauses"]
    team_export = project_root / "data/processed/srs_addressable_clauses.csv"
    importer(team_export, root=tmp_path)
    _, clauses, _ = load_inputs(tmp_path)
    original = pd.read_csv(team_export)
    assert list(clauses.text) == list(original.text)
    assert list(clauses.srs_scope) == list(original.srs_scope)
    # Git may convert text line endings during a Windows checkout.
    for relative in [
        "data/Starhawk Mission Computer SRS.md",
        "data/processed/srs_addressable_clauses.csv",
    ]:
        target = tmp_path / relative
        content = target.read_bytes().replace(b"\r\n", b"\n")
        target.write_bytes(content.replace(b"\n", b"\r\n"))
    requirements, clauses, _ = load_inputs(tmp_path)
    assert len(requirements) == 54 and len(clauses) == 14
