"""Import the team's existing clause export; do not rerun or replace extraction."""

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compliance_copilot.data import file_hash, parse_requirements, validate_clauses, write_json

# The saved NASA-HDBK-2203 topic 5.09 page and the date it was saved (issue #27); the notebook checks its hash
HANDBOOK_SNAPSHOT = "data/NASA-HDBK-2203_5.09_SRS.html"
HANDBOOK_SNAPSHOT_DATE = "2026-11-21"


def import_clauses(csv_path, root=ROOT):
    root = Path(root)
    frame = validate_clauses(pd.read_csv(csv_path, dtype={"swe_id": str, "clause_id": str}))
    frame = frame.loc[frame.srs_scope != "out"].copy()
    validate_clauses(frame)
    columns = ["swe_id", "clause_id", "text", "srs_scope"]
    columns += [name for name in ("srs_evidence", "source_url") if name in frame]
    frame = frame[columns]
    source_files = ["notebooks/N_PR_7150_002D_.pdf", "data/Starhawk Mission Computer SRS.md"]
    # Record the Handbook snapshot's hash too, when the file is present
    if (root / HANDBOOK_SNAPSHOT).exists():
        source_files.append(HANDBOOK_SNAPSHOT)
    requirements = parse_requirements((root / source_files[1]).read_text(encoding="utf-8-sig"))
    source_hashes = {name: file_hash(root / name) for name in source_files}
    output = root / "data/processed"
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "srs_addressable_clauses.csv"
    frame.to_csv(destination, index=False)
    manifest = {
        "origin": "Team's existing Aerospace_1A.ipynb SRS-addressable clause export",
        "source_hashes": source_hashes,
        "artifact_hashes": {destination.name: file_hash(destination)},
        "counts": {"srs_addressable": len(frame), "requirements": len(requirements)},
        "scope_status": "Team-curated applicability, not compliance labels.",
    }
    if HANDBOOK_SNAPSHOT in source_hashes:
        # When the Handbook page was saved, so its citations can be dated
        manifest["handbook_snapshot_date"] = HANDBOOK_SNAPSHOT_DATE
    write_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clauses",
        type=Path,
        required=True,
        help="srs_addressable_clauses.csv exported by the existing team notebook",
    )
    args = parser.parse_args()
    result = import_clauses(args.clauses)
    print("Imported {} team-prepared clauses.".format(result["counts"]["srs_addressable"]))
