# Non-LLM benchmark performance

All 37 inputs were processed; each has a report mapping. The FULL_SRS report reviews all 54 numbered requirements and six core SWE provisions.

## Public calibration only

Positive label: NEEDS_REVIEW in REQUIREMENT/QUALITY. Seven labelled cases include six positives. Abstentions remain in the denominator.

| TP | FP | FN | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- |
| 5 | 0 | 1 | 100.00% | 83.33% | 90.91% |

RQ-015 / SFMC-REQ-035 remains an explicit missed NEEDS_REVIEW; the existing quality rules were preserved.

The 11 public references are calibration material. There are no public labels for the 26 HOLDOUT inputs, so no holdout precision, recall or F1 is reported.

These metrics assess the CA quality adapter. They do not measure the legacy TF-IDF retrieval/pair classifier or NASA project compliance.

## Other scopes and significant differences

- DOCUMENT: 1/1 outcome agreement; 1/1 issue-code agreement; 0 abstentions.
- RELATIONSHIP: 1/1 outcome agreement; 1/1 issue-code agreement; 0 abstentions.
- REQUIREMENT: 6/7 outcome agreement; 6/7 issue-code agreement; 1 abstentions.
- SWE_COVERAGE: 2/2 outcome agreement; 2/2 issue-code agreement; 0 abstentions.
- RQ-015 (SFMC-REQ-035): predicted UNDETERMINED / NONE, reference NEEDS_REVIEW / SAFETY_INTERACTION. No original phrase rule matched and the narrow positive check does not apply; quality needs human assessment. Reference rationale: Always is broad and its application to safety inhibits is unspecified; does not by itself prove an inconsistency with REQ-015.

Process-only SWE findings use NOT_ASSESSABLE when the SRS cannot establish lifecycle/process evidence; this is not project noncompliance. See report.json for each explanation and required external records.
