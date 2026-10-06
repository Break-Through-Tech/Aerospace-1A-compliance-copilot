"""NPR 7150.2D extraction adapted from the team's data-preparation notebook.
Page ranges and Appendix C repair are specific to the bundled edition.
"""

import re

import pandas as pd
import pdfplumber


def apply_category(clause_id):
    clauses_sections_to_categories = {
        "3.1": "Software Life Cycle Planning",
        "3.2": "Software Cost Estimation",
        "3.3": "Software Schedules",
        "3.4": "Software Training",
        "3.5": "Software Classification Assessments",
        "3.6": "Software Assurance and Software IV&V",
        "3.7": "Safety-Critical Software",
        "3.8": "Automatic Generation of Software Source Code",
        "3.9": "Software Development Processes and Practices",
        "3.10": "Software Reuse",
        "3.11": "Software Cybersecurity",
        "3.12": "Software Bi-Directional Traceability",
        "4.1": "Software Requirements",
        "4.2": "Software Architecture",
        "4.3": "Software Design",
        "4.4": "Software Implementation",
        "4.5": "Software Testing",
        "4.6": "Software Operations, Maintenance, and Retirement",
        "5.1": "Software Configuration Management",
        "5.2": "Software Risk Management",
        "5.3": "Software Peer Reviews/Inspections",
        "5.4": "Software Measurements",
        "5.5": "Software Non-Conformance or Defect Management",
    }

    # exact match on the first two parts (3.10.1 -> "3.10"), so 3.10 / 3.11 / 3.12 no longer fall into 3.1
    section_id = ".".join(str(clause_id).split(".")[:2])
    return clauses_sections_to_categories.get(section_id, "General Guidance")


def extract_and_add_action_verbs(text):
    text_lower = str(text).lower()
    verbs = []
    for verb in ["develop", "test", "document", "verify", "track", "maintain", "assess", "review"]:
        if verb in text_lower:
            verbs.append(verb)

    return verbs


EXPECTED_SECTIONS = [
    "3.1",
    "3.2",
    "3.3",
    "3.4",
    "3.5",
    "3.6",
    "3.7",
    "3.8",
    "3.9",
    "3.10",
    "3.11",
    "3.12",
    "4.1",
    "4.2",
    "4.3",
    "4.4",
    "4.5",
    "4.6",
    "5.1",
    "5.2",
    "5.3",
    "5.4",
    "5.5",
]

SWE_TAG = re.compile(r"\[(SWE-\d+)\]")

JUNK_TAIL = re.compile(
    r"(?:\n\s*\n\s*(?:&\s*Validation|Requirements)\s*$)"  # 2nd line of wrapped 3.6 / Ch.5 titles
    r"|(?:\n\s*(?:Content\s*\n\s*)?6\.1\s+Software Engineering Products[\s\S]*$)"  # Chapter 6 start
)


def section_key(s):
    return tuple(int(p) for p in str(s).split("."))


def audit_clause_list(df, matrix_dict):
    issues = {}

    # 1. A clause carrying 2+ SWE tags means the next clause's number was lost and it got swallowed
    multi = {}
    for _, row in df.iterrows():
        blob = row["text"] + "\n" + "\n".join(row["notes"])
        ids = list(dict.fromkeys(SWE_TAG.findall(blob)))
        if len(ids) > 1:
            multi[row["clause_id"]] = ids
    issues["clauses_with_multiple_swe_ids"] = multi

    # Compare identities, not just counts: a missing clause can hide behind a duplicate.
    body_ids, matrix_ids = set(df["swe_id"]), set(matrix_dict)
    issues["in_matrix_not_in_body"] = sorted(matrix_ids - body_ids)
    issues["in_body_not_in_matrix"] = sorted(body_ids - matrix_ids)

    # Each SWE ID and clause ID must appear only once.
    issues["duplicate_swe_ids"] = sorted(df["swe_id"][df["swe_id"].duplicated()].unique())
    issues["duplicate_clause_ids"] = sorted(df["clause_id"][df["clause_id"].duplicated()].unique())

    # Check that every expected section is represented.
    issues["missing_sections"] = [s for s in EXPECTED_SECTIONS if s not in set(df["section"])]

    # Detect leftover wrapped headings and Chapter 6 text.
    junk = []
    for _, row in df.iterrows():
        fields = [row["text"]] + list(row["notes"])
        if any(JUNK_TAIL.search(f) for f in fields):
            junk.append(row["clause_id"])

    issues["clauses_with_trailing_junk"] = junk

    # Confirm body clause numbers agree with Appendix C.
    mismatch = {}
    for _, row in df.iterrows():
        m = matrix_dict.get(row["swe_id"])
        if m and m.get("matrix_section") and m["matrix_section"] != row["clause_id"]:
            mismatch[row["swe_id"]] = (row["clause_id"], m["matrix_section"])
    issues["clause_id_vs_matrix_section"] = mismatch

    return issues


def split_multi_swe(row, matrix_dict):
    """Split one row whose text holds several [SWE-xxx] tags into one row per SWE ID."""
    text = row["text"]
    tags = list(SWE_TAG.finditer(text))
    if len(tags) <= 1:
        return [row.to_dict()]

    # Lettered sub-items (a., b., ...) after a tag still belong to it, so each swallowed
    # clause starts at the last blank line before its own tag
    bounds = [0]
    for this_tag, next_tag in zip(tags, tags[1:]):
        gap = text.rfind("\n\n", this_tag.end(), next_tag.start())
        bounds.append(gap if gap != -1 else this_tag.end())
    bounds.append(len(text))

    rows = []
    for i, tag in enumerate(tags):
        new = row.to_dict()
        swe_id = tag.group(1)
        new["swe_id"] = swe_id
        new["text"] = text[bounds[i] : bounds[i + 1]].strip()
        new["notes"] = (
            list(row["notes"]) if i == len(tags) - 1 else []
        )  # notes follow the last clause
        if i > 0:
            m = matrix_dict.get(swe_id, {})
            new.update(m)
            new["clause_id"] = m.get("matrix_section")
            new["section"] = ".".join(new["clause_id"].split(".")[:2]) if new["clause_id"] else None
            new["sources"] = ["body", "matrix"] if m else ["body"]
            if not m:
                print(
                    f"WARNING: {swe_id} was split out but has no Appendix C row, so its clause_id is unknown"
                )
        rows.append(new)
    return rows


def strip_junk(s):
    return JUNK_TAIL.sub("", s).rstrip()


def extract_nasa_clauses(pdf_path, scope_map):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page_no in range(19, 45):
            text = pdf.pages[page_no].extract_text()
            if text:
                full_text += text.strip() + "\n"

    DEFAULT_BOILERPLATE_PATTERNS = [
        r"^NPR\s+[\w.\-]+\s*--.*$",
        r"^This document does not bind the public.*$",
        r"^incorporated into a contract\..*$",
        r"^the NASA Online Directives Information System.*$",
        r"^this is the correct version before use.*$",
        r"^Page \d+ of \d+.*$",
    ]

    for boilerplate_pattern in DEFAULT_BOILERPLATE_PATTERNS:
        full_text = re.sub(boilerplate_pattern, "", full_text, flags=re.MULTILINE | re.IGNORECASE)

    full_text = re.sub(
        r"^\s*(?:Chapter\s+\d+.*|[3-5]\.\d+\s+[A-Za-z].*)$", "", full_text, flags=re.MULTILINE
    )

    full_text = re.sub(r"(\d+\.\d+(?:\.\d+)?[\s\S]*?)\n+\s*\1", r"\1", full_text)

    ch3_5_raw = re.split(r"\n(?=\s*[3-5]\.\d+\.\d+)", full_text)

    ch3_5_clauses = [c.strip() for c in ch3_5_raw if c.strip()]

    ch3_5_clauses = [c for c in ch3_5_clauses if re.search(r"^\s*[3-5]\.\d+\.\d+", c)]

    chunks = []

    for c in ch3_5_clauses:
        match = re.match(r"^\s*([3-5]\.\d+(?:\.\d+)?)\s+(.*)", c, re.DOTALL)
        if match:
            clause_id, text = match.groups()
            section_id = clause_id.rsplit(".", 1)[0]

            swe_match = re.search(r"\[(SWE-\d+)\]", text)
            if swe_match:
                # Separate main requirement text from any "Note:" paragraphs
                note_parts = re.split(r"\n(?=\s*Note(?:\s+\d+)?:)", text, flags=re.IGNORECASE)

                # The first part is the core requirement text
                req_text = note_parts[0].strip()

                # The remaining parts are notes attached to this requirement
                notes_list = [n.strip() for n in note_parts[1:] if n.strip()]

                chunks.append(
                    {
                        "swe_id": swe_match.group(1),
                        "section": section_id,
                        "clause_id": clause_id,
                        "text": req_text,
                        "notes": notes_list,
                    }
                )

    appendix_c_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_no in range(55, 80):
            page = pdf.pages[page_no]
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if len(row) < 3:
                        continue
                    if (
                        len(row) > 2
                        and re.match(r"^\d{3}$", str(row[1]).strip())
                        and not re.match(r"^\d{3}$", str(row[2]).strip())
                    ):
                        row = [""] + row  # page 77 table is missing the leading column
                    swe_num = str(row[2]).strip() if row[2] else ""
                    # Skips headers ('SWE\n#') and empty strings ('')
                    if not re.match(r"^\d{3}$", swe_num):
                        continue

                    swe_id = f"SWE-{swe_num}"

                    appendix_c_rows.append(
                        {"swe_id": swe_id, "raw_row": [c.strip() if c else "" for c in row]}
                    )

    matrix_dict = {}

    for item in appendix_c_rows:
        swe_id = item["swe_id"]
        row = item["raw_row"]

        section_num = row[1] if len(row) > 1 else None
        requirement_text = row[3] if len(row) > 3 else None
        authority = row[4] if len(row) > 4 else None

        class_marks = [col for col in row[5:10] if "x" in col.lower()] if len(row) >= 8 else []

        f_auth = row[12] if len(row) > 12 else None
        f_mark = row[-1] if len(row) > 0 else None

        matrix_dict[swe_id] = {
            "matrix_section": section_num,
            "matrix_requirement_text": (
                requirement_text.replace("\n", " ") if requirement_text else None
            ),
            "matrix_authority": authority,
            "matrix_class_marks": len(class_marks),
            "matrix_f_authority": f_auth,
            "matrix_f_mark": f_mark,
        }

    for chunk in chunks:
        swe_id = chunk["swe_id"]
        chunk["sources"] = ["body"]

        if swe_id in matrix_dict:
            chunk["sources"].append("matrix")
            chunk.update(matrix_dict[swe_id])
        else:
            chunk.update(
                {
                    "matrix_section": None,
                    "matrix_requirement_text": None,
                    "matrix_authority": None,
                    "matrix_class_marks": None,
                    "matrix_f_authority": None,
                    "matrix_f_mark": None,
                }
            )

    reqs_clauses_df = pd.DataFrame(chunks)

    repaired = []

    for _, row in reqs_clauses_df.iterrows():
        repaired.extend(split_multi_swe(row, matrix_dict))

    reqs_clauses_df = pd.DataFrame(repaired)

    reqs_clauses_df["text"] = reqs_clauses_df["text"].apply(strip_junk)

    reqs_clauses_df["notes"] = reqs_clauses_df["notes"].apply(
        lambda ns: [strip_junk(n) for n in ns if strip_junk(n)]
    )

    reqs_clauses_df["functional_category"] = reqs_clauses_df["clause_id"].apply(apply_category)

    reqs_clauses_df["action_verbs"] = reqs_clauses_df["text"].apply(extract_and_add_action_verbs)

    reqs_clauses_df = reqs_clauses_df.sort_values(
        "clause_id", key=lambda s: s.map(section_key)
    ).reset_index(drop=True)

    qa_after = audit_clause_list(reqs_clauses_df, matrix_dict)

    if any(qa_after.values()):
        raise ValueError("Extraction QA failed: {}".format(qa_after))

    unknown = set(scope_map) - set(reqs_clauses_df["swe_id"])

    if unknown:
        raise ValueError("Scope mapping references unknown SWE IDs: {}".format(sorted(unknown)))

    reqs_clauses_df["srs_scope"] = reqs_clauses_df["swe_id"].map(
        lambda s: scope_map.get(s, {}).get("scope", "out")
    )

    reqs_clauses_df["srs_evidence"] = reqs_clauses_df["swe_id"].map(
        lambda s: scope_map.get(s, {}).get("evidence", "")
    )

    reqs_clauses_df["source_url"] = (
        "https://nodis3.gsfc.nasa.gov/npg_img/N_PR_7150_002D_/N_PR_7150_002D_.pdf"
    )

    return reqs_clauses_df, qa_after
