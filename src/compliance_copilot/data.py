"""Load validated data; never infer compliance from successful parsing."""

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


REQUIREMENT_PATTERN = re.compile(
    r"^\*\*(SFMC-REQ-\d{3})\s*[—–-]\s*(.*?)\*\*\s*\n" r"(.*?)(?=^\*\*SFMC-REQ-|^#|\Z)",
    flags=re.MULTILINE | re.DOTALL,
)


def validate_table(frame, columns, identifiers):
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError("Missing columns: {}".format(sorted(missing)))
    if frame.empty:
        raise ValueError("Input table is empty.")
    for column in columns:
        if frame[column].isna().any() or frame[column].astype(str).str.strip().eq("").any():
            raise ValueError("Missing values in {}".format(column))
    for column in identifiers:
        if frame[column].duplicated().any():
            raise ValueError("Duplicate {} values".format(column))


def parse_requirements(srs_text):
    rows = []
    for requirement_id, title, text in REQUIREMENT_PATTERN.findall(srs_text):
        text = re.sub(r"^---\s*$", "", text, flags=re.MULTILINE)
        rows.append(
            {
                "requirement_id": requirement_id,
                "title": title.strip(),
                "text": re.sub(r"\s+", " ", text).strip(),
            }
        )
    frame = pd.DataFrame(rows, columns=["requirement_id", "title", "text"])
    validate_table(frame, frame.columns, ["requirement_id"])
    return frame


def validate_clauses(frame):
    validate_table(frame, ["swe_id", "clause_id", "text", "srs_scope"], ["swe_id", "clause_id"])
    if not frame["swe_id"].str.fullmatch(r"SWE-\d{3}").all():
        raise ValueError("Invalid SWE IDs")
    if not frame["clause_id"].str.fullmatch(r"[3-5]\.\d+(?:\.\d+)*").all():
        raise ValueError("Invalid clause IDs")
    if not frame["srs_scope"].isin(["direct", "partial", "out"]).all():
        raise ValueError("Invalid SRS applicability scope")
    return frame


def load_inputs(project_root):
    root = Path(project_root)
    manifest_path = root / "data/processed/manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("Run python scripts/prepare_data.py first.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for relative in [
        "notebooks/N_PR_7150_002D_.pdf",
        "data/Starhawk Mission Computer SRS.md",
        "data/srs_scope.json",
    ]:
        actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        if actual != manifest["source_hashes"].get(relative):
            raise ValueError("Source changed: {}. Re-run scripts/prepare_data.py.".format(relative))
    srs_text = (root / "data/Starhawk Mission Computer SRS.md").read_text(encoding="utf-8-sig")
    path = root / "data/processed/srs_addressable_clauses.csv"
    if not path.exists():
        raise FileNotFoundError("Run python scripts/prepare_data.py first: {}".format(path))
    clauses = validate_clauses(pd.read_csv(path, dtype={"swe_id": str, "clause_id": str}))
    expected = manifest.get("artifact_hashes", {}).get(path.name)
    if expected != hashlib.sha256(path.read_bytes()).hexdigest():
        raise ValueError("Prepared clause data changed. Re-run scripts/prepare_data.py.")
    return parse_requirements(srs_text), clauses, srs_text


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
