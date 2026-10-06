"""One baseline run shared by the notebook and command-line interface."""

import json
from pathlib import Path

import pandas as pd

from .baseline import EvidenceBaseline, keyword_findings
from .data import load_inputs, write_json
from .evaluation import evaluate_predictions, evaluate_retrieval, load_benchmark
from .retrieval import ClauseRetriever


def _export_frame(frame, output, name):
    # Serialize nested evidence as JSON within CSV cells, preserving the JSON export.
    records = json.loads(frame.to_json(orient="records", force_ascii=False, double_precision=15))
    write_json(output / (name + ".json"), records)
    csv = frame.copy()
    for column in csv:
        csv[column] = csv[column].map(
            lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
        )
    csv.to_csv(output / (name + ".csv"), index=False)


def run_baseline(project_root, output_dir=None, benchmark_path=None, split=None, top_k=3):
    root = Path(project_root)
    output = Path(output_dir) if output_dir else root / "output/baseline"
    requirements, clauses, srs_text = load_inputs(root)
    retriever = ClauseRetriever(clauses)
    matches = retriever.retrieve(requirements, top_k=top_k)
    model = EvidenceBaseline(clauses)
    candidates = matches.loc[matches.retrieval_status == "CANDIDATE"]
    assessments = model.assess_pairs(requirements, candidates)
    documents = model.assess_document(requirements, srs_text)
    keywords = keyword_findings(requirements)
    metrics = {
        "evaluation_status": "awaiting_advisor_benchmark",
        "requirements": len(requirements),
        "indexed_clauses": len(retriever.clauses),
        "top_k": top_k,
        "candidate_pairs": len(candidates),
        "requirements_without_lexical_match": int(
            matches.retrieval_status.eq("NO_LEXICAL_MATCH").sum()
        ),
        "keyword_status_counts": {k: int(v) for k, v in keywords.status.value_counts().items()},
        "candidate_verdict_counts": {
            k: int(v) for k, v in assessments.verdict.value_counts().items()
        },
        "document_verdict_counts": {k: int(v) for k, v in documents.verdict.value_counts().items()},
        "citation_id_validity": (
            float(
                assessments.apply(
                    lambda r: r.clause_id == model.clauses[r.swe_id]["clause_id"], axis=1
                ).mean()
            )
            if not assessments.empty
            else None
        ),
        "citation_note": "Valid corpus IDs are not a measure of semantic groundedness.",
    }
    benchmark_predictions = None
    if benchmark_path:
        benchmark = load_benchmark(benchmark_path, requirements, clauses, split)
        # Assess gold pairs directly: retrieval misses do not change classifier metrics.
        pair_rows = benchmark.loc[benchmark.requirement_id != "DOCUMENT"]
        direct = model.assess_pairs(requirements, pair_rows)
        doc_rows = documents.loc[
            documents.swe_id.isin(benchmark.loc[benchmark.requirement_id == "DOCUMENT", "swe_id"])
        ]
        benchmark_predictions = pd.concat([direct, doc_rows], ignore_index=True)
        metrics.update(
            evaluation_status="provided_benchmark_evaluated",
            benchmark_path=str(benchmark_path),
            benchmark_split=split,
            classification=evaluate_predictions(benchmark, benchmark_predictions),
            retrieval=evaluate_retrieval(benchmark, matches),
        )
    output.mkdir(parents=True, exist_ok=True)
    if benchmark_predictions is None:
        # Remove only our prior benchmark exports so an unevaluated run cannot
        # accidentally present stale benchmark predictions as current results.
        for extension in ("csv", "json"):
            stale = output / ("benchmark_predictions." + extension)
            if stale.exists():
                stale.unlink()
    for name, frame in [
        ("keyword_findings", keywords),
        ("clause_matches", matches),
        ("pair_assessments", assessments),
        ("document_assessments", documents),
    ]:
        _export_frame(frame, output, name)
    if benchmark_predictions is not None:
        _export_frame(benchmark_predictions, output, "benchmark_predictions")
    write_json(output / "metrics.json", metrics)
    return {
        "requirements": requirements,
        "clauses": clauses,
        "matches": matches,
        "keywords": keywords,
        "assessments": assessments,
        "document_assessments": documents,
        "metrics": metrics,
        "benchmark_predictions": benchmark_predictions,
    }
