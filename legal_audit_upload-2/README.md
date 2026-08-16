# Legal Audit Package

this folder contains the legal-data infrastructure for **Insured but Unprotected: State Regulation and Hidden Contract Quality in U.S. Health Insurance**

## What is included

- `legislation/state_health_insurance_legal_audit.xlsx`: event-level coding sheet, state-year panel, source log, codebook, and quality-control checklist.
- `legislation/coding_protocol.md`: reproducible instructions for identifying, coding, and reviewing state laws.
- `legislation/federal_baseline.md`: federal rules that must be separated from incremental state protections.
- `legislation/source_hierarchy.md`: standards for acceptable legal sources.
- `legislation/validate_legal_audit.py`: automated structural and completeness checks.

## Important status note

The workbook is a **complete 51-jurisdiction audit framework**, not yet a final legal dataset. The 51 prior-authorization rows contain a national secondary-source inventory derived from the AMA's 2024 state-law chart. Nevada is explicitly flagged as a chart gap. These entries identify leads but must not be interpreted as final treatment codes. Exact citations, operative dates, market scope, amendments through 2026, and official state sources still require primary-source verification. The remaining policy-family rows remain inventory placeholders.

## Recommended first pass

Start with prior-authorization procedure laws. This is the most feasible policy family to code consistently across states and years. Add denial explanations, appeals, clinical review, continuity of care, and automated review only as the primary-source audit permits.

## Run the checks

From the repository root:

```bash
python3 legislation/validate_legal_audit.py
```

The script requires `openpyxl`:

```bash
python3 -m pip install openpyxl
```
