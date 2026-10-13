#!/usr/bin/env python3
"""Validate the Copilot output schema and some cross-field constraints.

Usage:
  python -m pip install jsonschema
  python validate_report.py sample_output_v1.json
  python validate_report.py path/to/report.json
"""
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

SWE_IDS = {'SWE-050','SWE-051','SWE-184','SWE-053','SWE-054','SWE-055'}

def validate(path):
    directory = Path(__file__).resolve().parent
    schema = json.loads((directory/'output_contract_schema_v1.json').read_text(encoding='utf-8'))
    report = json.loads(Path(path).read_text(encoding='utf-8'))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(report)
    issues=[]
    reviews=report['requirement_reviews']
    ids=[r['requirement_id'] for r in reviews]
    if len(ids)!=len(set(ids)):
        issues.append('Duplicate requirement review IDs')
    for r in reviews:
        primary=r['primary_swe_id'];strength=r['primary_swe_strength']
        if (primary is None)!=(strength is None):
            issues.append(f"{r['requirement_id']}: primary SWE ID and strength must both be set or both null")
        if primary is not None and not any(l['swe_id']==primary and l['strength']==strength for l in r['swe_links']):
            issues.append(f"{r['requirement_id']}: primary SWE must match a link")
        if r['quality_status']=='ACCEPTABLE' and r['quality_issues']:
            issues.append(f"{r['requirement_id']}: ACCEPTABLE review has quality issues")
        swelinks=[x['swe_id'] for x in r['swe_links']]
        if len(swelinks)!=len(set(swelinks)):
            issues.append(f"{r['requirement_id']}: duplicated SWE links")
    for r in report['relationships']:
        unknown=set(r['requirement_ids'])-set(ids)
        if unknown:
            issues.append(f"{r['relationship_id']}: unreviewed relationship IDs {sorted(unknown)}")
    covers=[x['swe_id'] for x in report['swe_coverage']]
    if len(covers)!=len(set(covers)):
        issues.append('Duplicate SWE summaries')
    if report['run']['evaluation_scope']=='FULL_SRS':
        expected={f'SFMC-REQ-{n:03d}' for n in range(1,55)}
        if set(ids)!=expected:
            issues.append(f'Full Starhawk run: missing requirement IDs {sorted(expected-set(ids))}; extras {sorted(set(ids)-expected)}')
        if set(covers)!=SWE_IDS:
            issues.append(f'Full run: missing SWE IDs {sorted(SWE_IDS-set(covers))}')
        if not any(x['criterion']=='REQUIREMENT_IDENTIFIERS' for x in report['document_findings']):
            issues.append('Full Starhawk run: assess unnumbered §2.1 normative sentences using REQUIREMENT_IDENTIFIERS')
    for summary in report['swe_coverage']:
        missing=set(summary['supported_by_requirement_ids'])-set(ids)
        if missing:
            issues.append(f"{summary['swe_id']}: cited requirement IDs not reviewed: {sorted(missing)}")
        if summary['nasa_reference']['swe_id'] != summary['swe_id']:
            issues.append(f"{summary['swe_id']}: NPR citation SWE ID mismatch")
    if issues:
        raise ValueError('\n'.join(issues))
    return (len(reviews),len(report['relationships']),len(report['document_findings']),len(covers))

if __name__=='__main__':
    if len(sys.argv)!=2:
        print(__doc__);sys.exit(2)
    try:
        reqs,rels,docs,swes=validate(sys.argv[1])
        print(f'VALID: {reqs} requirements, {rels} relationships, {docs} document findings, {swes} SWE summaries')
    except Exception as exc:
        print('INVALID:',str(exc),file=sys.stderr)
        sys.exit(1)
