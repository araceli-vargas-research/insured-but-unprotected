# Insured but Unprotected

Reproducibility repository for a proposed study of state insurance regulation,
claims denials, appeals, and Marketplace outcomes in the United States.

## Research question

Do state procedural protections make promised insurance coverage easier to
enforce, and are any benefits accompanied by higher premiums or reduced plan
choice?

## Current status

This is a **feasibility-stage repository**, not a completed causal study. It
downloads CMS Transparency in QHP Coverage files spanning claims years
2015-2024, links the corresponding Plan Attributes files, supplies reproducible
cleaning code and harmonized panels, and includes empty legal-coding templates.
No treatment effects have been estimated.

## Current feasibility results

- 1,807 issuer-state-year outcome observations, claims years 2015-2024.
- 48,300 medical-QHP plan-year observations, market years 2015-2026.
- 2,322 issuer-state-year market participation observations.
- Complete age-40 base-premium linkage for the constructed medical-QHP panel.
- 79.9% contemporaneous linkage between Transparency outcomes and market/rate records.
- Two implausible source records retained and flagged for audit rather than deleted.

## Current unit of observation

The primary processed file uses one row per:

```text
issuer x state x claims year
```

Issuer-level values repeat across plan rows in the CMS workbooks. The cleaning
script verifies that these fields are invariant before collapsing them.

## Included outputs

- `data/processed/issuer_state_year.csv`: principal outcome panel.
- `data/processed/plan_state_year.csv`: plan-level denial-reason panel.
- `data/processed/plan_2026_attributes_linked.csv`: linkage demonstration.
- `data/processed/medical_qhp_plan_year.csv`: medical Marketplace plans, 2015-2026.
- `data/processed/issuer_state_market_year.csv`: issuer participation and plan counts.
- `data/processed/state_market_year.csv`: state-level Marketplace participation.
- `data/processed/plan_rating_area_age40_premiums.csv`: standardized plan premiums.
- `data/processed/issuer_state_premiums.csv`: issuer-state premium summaries.
- `data/processed/state_rating_area_silver_premiums.csv`: lowest silver premiums.
- `data/processed/analysis_issuer_state_year.csv`: merged analysis-ready panel.
- `output/tables/file_inventory.csv`: file and sample inventory.
- `output/tables/data_quality_summary.csv`: outcome missingness by year.
- `output/tables/known_data_issues.csv`: observations requiring source review.
- `output/tables/plan_attributes_linkage.csv`: linkage success.
- `docs/feasibility_memo.md`: limitations and remaining decisions.

## Reproduce the processed files

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python code/00_download_cms.py
python code/01_build_cms_panel.py
python code/02_validate_outputs.py
python code/03_build_market_panel.py
python code/04_build_premium_panel.py
python code/05_build_analysis_panel.py
```

The first command downloads and validates all required public CMS ZIP files for
2015-2026. It is restart-safe: valid existing files are skipped. Preview the
download list without transferring anything with:

```bash
python code/00_download_cms.py --dry-run
```

CMS distributes the Exchange PUFs as direct versioned ZIP files, so no API key
or account is required.

Alternatively, reproduce the complete CMS pipeline with:

```bash
make all
```

## Outcome definitions

```text
total denial rate = total claims denied / total claims received
in-network denial rate = in-network claims denied / in-network claims received
internal appeal rate = internal appeals filed / total claims denied
internal reversal rate = internal appeals overturned / internal appeals filed
external reversal rate = external appeals overturned / external appeals filed
```

The denominators reflect the available CMS aggregates and require substantive
review before final econometric use. Appeals may concern adverse determinations
beyond the claims-denial count used in the provisional appeal-rate denominator.

## Critical limitations

1. CMS publication year is not claims year. The files have an approximately
   two-year reporting lag.
2. The 2017-2019 publications are issuer-level and require a medical-issuer
   filter based on contemporaneous Plan Attributes data.
3. Publications through 2023 report aggregate claims; later files split network
   status. In-network-only analysis therefore has a shorter time series.
4. Only federal-platform Marketplace states are represented.
5. Detailed plan-level denial reasons have substantial missingness.
6. Plan identifiers and detailed denial reasons are unavailable in the earliest
   issuer-level files.
7. No state law has yet been coded or verified. Causal identification remains
   unproven.

## Next research steps

1. Archive the 2025 and 2026 Transparency data dictionaries.
2. Add older Transparency PUFs to lengthen the pre-treatment period.
3. Select one precisely defined policy family.
4. Complete a three-state legal-coding pilot using primary sources.
5. Add historical Rate, Plan Attributes, and Service Area PUFs.
6. Audit treatment timing, sample composition, and pre-trends before estimating
   causal effects.

Instructions for publishing this package as a private repository are in
`docs/github_setup.md`.

## Data provenance

CMS Exchange PUF landing page:
https://www.cms.gov/marketplace/resources/data/public-use-files

All raw files included here are public CMS source files supplied for the
research handoff. They are preserved unchanged; all transformations occur in
the scripts and processed directories.
