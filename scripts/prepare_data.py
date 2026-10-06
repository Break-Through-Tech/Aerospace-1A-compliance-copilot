"""Rebuild baseline inputs offline from the repository's NASA PDF and SRS."""

import argparse
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compliance_copilot.data import parse_requirements, validate_clauses, write_json
from compliance_copilot.extraction import extract_nasa_clauses


def prepare_data(root=ROOT):
    root = Path(root)
    output = root / "data/processed"
    pdf = root / "notebooks/N_PR_7150_002D_.pdf"
    srs = root / "data/Starhawk Mission Computer SRS.md"
    scope_path = root / "data/srs_scope.json"
    clauses, qa = extract_nasa_clauses(pdf, json.loads(scope_path.read_text(encoding="utf-8")))
    validate_clauses(clauses)
    addressable = clauses.loc[clauses.srs_scope != "out"].reset_index(drop=True)
    requirements = parse_requirements(srs.read_text(encoding="utf-8-sig"))
    if (len(clauses), len(addressable), len(requirements)) != (100, 14, 54):
        raise ValueError(
            "Bundled corpus counts changed; review extraction and scope before exporting."
        )
    output.mkdir(parents=True, exist_ok=True)
    # JSON retains nested notes/action verbs; CSV is convenient for inspection.
    write_json(output / "nasa_clauses.json", clauses.to_dict("records"))
    clauses.to_csv(output / "annotated_nasa_clauses.csv", index=False)
    addressable.to_csv(output / "srs_addressable_clauses.csv", index=False)
    requirements.to_csv(output / "srs_requirements.csv", index=False)
    manifest = {
        "source_hashes": {
            str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (pdf, srs, scope_path)
        },
        "artifact_hashes": {
            name: hashlib.sha256((output / name).read_bytes()).hexdigest()
            for name in (
                "nasa_clauses.json",
                "annotated_nasa_clauses.csv",
                "srs_addressable_clauses.csv",
                "srs_requirements.csv",
            )
        },
        "counts": {
            "clauses": len(clauses),
            "srs_addressable": len(addressable),
            "requirements": len(requirements),
        },
        "extraction_qa": qa,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("pandas", "pdfplumber", "scikit-learn")
        },
        "scope_status": "Team-curated SRS applicability; not benchmark labels or verdicts.",
    }
    write_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    print(json.dumps(prepare_data(parser.parse_args().root), indent=2))
