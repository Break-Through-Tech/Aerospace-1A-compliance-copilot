"""Benchmark validation and metrics with abstentions counted explicitly."""

from pathlib import Path

import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

from .data import validate_table


LABELS = ["Meets", "Partial", "Gap"]
PREDICTIONS = LABELS + ["REVIEW"]
KEYS = ["requirement_id", "swe_id"]


def validate_benchmark(frame, requirements=None, clauses=None, split=None):
    validate_table(frame, KEYS + ["verdict", "assessment_scope"], [])
    if not frame.verdict.isin(LABELS).all():
        raise ValueError("Benchmark verdicts must be Meets, Partial, or Gap")
    if not frame.assessment_scope.eq("srs_evidence").all():
        raise ValueError(
            "Benchmark scope must be srs_evidence, matching the documented assessed provisions"
        )
    if "split" in frame:
        validate_table(frame, ["split"], [])
        if split is None and frame.split.nunique() > 1:
            raise ValueError("Choose a split explicitly; do not mix tuning and test rows")
        if split is not None:
            frame = frame.loc[frame.split == split].copy()
            if frame.empty:
                raise ValueError("No benchmark rows in split {}".format(split))
    elif split is not None:
        raise ValueError("Benchmark has no split column")
    if frame.duplicated(KEYS).any():
        raise ValueError("Duplicate benchmark requirement/clause pairs")
    if requirements is not None:
        unknown = set(frame.requirement_id) - set(requirements.requirement_id) - {"DOCUMENT"}
        if unknown:
            raise ValueError("Unknown benchmark requirement IDs: {}".format(sorted(unknown)))
    if clauses is not None:
        unknown = set(frame.swe_id) - set(clauses.swe_id)
        if unknown:
            raise ValueError("Unknown benchmark SWE IDs: {}".format(sorted(unknown)))
    return frame.reset_index(drop=True)


def load_benchmark(path, requirements, clauses, split=None):
    return validate_benchmark(pd.read_csv(Path(path), dtype=str), requirements, clauses, split)


def evaluate_predictions(benchmark, predictions, gap_labels=("Gap",)):
    benchmark = validate_benchmark(benchmark)
    validate_table(predictions, KEYS + ["verdict", "assessment_scope"], [])
    if predictions.duplicated(KEYS).any():
        raise ValueError("Duplicate prediction pairs")
    if not predictions.verdict.isin(PREDICTIONS).all():
        raise ValueError("Invalid prediction verdict")
    if not gap_labels or not set(gap_labels).issubset(LABELS):
        raise ValueError("gap_labels must be a nonempty subset of supported verdicts")
    merged = benchmark.merge(
        predictions[KEYS + ["verdict", "assessment_scope"]],
        on=KEYS,
        how="left",
        suffixes=("_gold", "_pred"),
        validate="one_to_one",
    )
    if merged.verdict_pred.isna().any():
        raise ValueError("Missing predictions for benchmark pairs")
    if not merged.assessment_scope_gold.eq(merged.assessment_scope_pred).all():
        raise ValueError("Prediction and benchmark assessment scopes differ")
    gold = merged.verdict_gold
    predicted = merged.verdict_pred
    precision, recall, f1, support = precision_recall_fscore_support(
        gold, predicted, labels=LABELS, zero_division=0
    )
    actual_gap = gold.isin(gap_labels)
    flagged_gap = predicted.isin(gap_labels)
    tp = int((actual_gap & flagged_gap).sum())
    fp = int((~actual_gap & flagged_gap).sum())
    fn = int((actual_gap & ~flagged_gap).sum())  # REVIEW is a missed gap, not excluded.
    confusion = {
        label: {guess: int(((gold == label) & (predicted == guess)).sum()) for guess in PREDICTIONS}
        for label in LABELS
    }
    return {
        "benchmark_rows": len(merged),
        "assessment_scope": "srs_evidence",
        "decision_coverage": float(predicted.ne("REVIEW").mean()),
        "accuracy_including_reviews": float(gold.eq(predicted).mean()),
        "per_class": {
            label: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i, label in enumerate(LABELS)
        },
        "gap_detection": {
            "positive_labels": list(gap_labels),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
        },
        "confusion_matrix": confusion,
        "zero_division_policy": "Undefined precision/recall is reported as 0; inspect support counts.",
    }


def evaluate_retrieval(benchmark, matches):
    """Recall of benchmarked pairs only; unlabeled matches are not false positives."""
    pairs = benchmark.loc[benchmark.requirement_id != "DOCUMENT", KEYS].drop_duplicates()
    if pairs.empty:
        return {"benchmark_pairs": 0, "pair_recall_at_k": None, "requirement_hit_rate_at_k": None}
    candidates = set(map(tuple, matches.loc[matches.retrieval_status == "CANDIDATE", KEYS].values))
    hits = [tuple(pair) in candidates for pair in pairs.values]
    found = pairs.copy()
    found["hit"] = hits
    return {
        "benchmark_pairs": len(pairs),
        "pair_recall_at_k": sum(hits) / len(hits),
        "requirement_hit_rate_at_k": float(found.groupby("requirement_id").hit.any().mean()),
        "precision": None,
        "precision_note": "Not estimated: other retrieved clauses may be relevant but unlabeled.",
    }
