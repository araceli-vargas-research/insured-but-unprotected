#!/usr/bin/env python3
"""Fail-fast validation checks for processed research data."""

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
panel = pd.read_csv(ROOT / "data" / "processed" / "issuer_state_year.csv", dtype={"issuer_id": "string"})

assert not panel.duplicated(["issuer_id", "state", "claims_year"]).any()
assert set(panel["claims_year"]) == set(range(2015, 2025))
assert panel["state"].str.fullmatch(r"[A-Z]{2}").all()

for column in [
    "denial_rate_total", "denial_rate_in_network", "internal_appeal_rate",
    "internal_reversal_rate", "external_reversal_rate",
]:
    values = panel[column].dropna()
    assert (values >= 0).all(), f"Negative values in {column}"
    # Values above one can signal denominator-definition or reporting problems.
    if (values > 1).any():
        print(f"WARNING: {column} has {(values > 1).sum()} observations above 1; retain and investigate.")

print(f"Validated {len(panel):,} unique issuer-state-year observations.")
