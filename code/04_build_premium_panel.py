#!/usr/bin/env python3
"""Constructed beginning-of-year age-40 Marketplace premium measures.

The Rate PUFs are large, so they are streamed in chunks. Medical QHP plan IDs
come from 03_build_market_panel.py. IndividualRate is the base individual rate;
the separate tobacco surcharge field is not used.
"""

from pathlib import Path
from zipfile import ZipFile
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CMS = ROOT / "data" / "raw" / "cms_downloads"
OUT = ROOT / "data" / "processed"
TABLES = ROOT / "output" / "tables"


def read_age40_rows(path, valid_plan_ids):
    columns = [
        "BusinessYear", "StateCode", "IssuerId", "RateEffectiveDate",
        "RateExpirationDate", "PlanId", "RatingAreaId", "Tobacco", "Age",
        "IndividualRate",
    ]
    selected = []
    with ZipFile(path) as archive:
        member = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
        with archive.open(member) as stream:
            reader = pd.read_csv(
                stream, encoding="cp1252", dtype="string", usecols=columns,
                chunksize=500_000, low_memory=False,
            )
            for chunk in reader:
                keep = chunk["Age"].str.strip().eq("40") & chunk["PlanId"].isin(valid_plan_ids)
                if keep.any():
                    selected.append(chunk.loc[keep].copy())
    return pd.concat(selected, ignore_index=True) if selected else pd.DataFrame(columns=columns)


def main():
    plans = pd.read_csv(OUT / "medical_qhp_plan_year.csv", dtype="string", low_memory=False)
    annual = []
    diagnostics = []

    for year in range(2015, 2027):
        year_plans = plans.loc[plans["market_year"].astype(int).eq(year)].copy()
        valid_ids = set(year_plans["plan_id"].dropna())
        path = CMS / "02_rate_pufs" / f"{year}_rate-puf.zip"
        rates = read_age40_rows(path, valid_ids)
        rates["individual_rate_age40"] = pd.to_numeric(rates["IndividualRate"], errors="coerce")
        rates["rate_effective_date"] = pd.to_datetime(rates["RateEffectiveDate"], errors="coerce")
        rates = rates.loc[rates["individual_rate_age40"].gt(0)].copy()
        rates = rates.sort_values("rate_effective_date")

        # Beginning-of-year rate for each plan and rating area. Tobacco rows can
        # duplicate the base IndividualRate, so they are collapsed here.
        keys = ["StateCode", "IssuerId", "PlanId", "RatingAreaId"]
        rates = rates.groupby(keys, as_index=False).first()
        rates.insert(0, "market_year", year)
        rates = rates.rename(columns={
            "StateCode": "state", "IssuerId": "issuer_id", "PlanId": "plan_id",
            "RatingAreaId": "rating_area_id",
        })
        metadata = year_plans[["state", "issuer_id", "plan_id", "metal_level", "plan_type"]].drop_duplicates()
        rates = rates.merge(metadata, on=["state", "issuer_id", "plan_id"], how="left", validate="many_to_one")
        annual.append(rates)
        diagnostics.append({
            "market_year": year,
            "medical_qhp_plans": len(valid_ids),
            "plans_with_age40_rate": rates["plan_id"].nunique(),
            "plan_rate_match_share": rates["plan_id"].nunique() / len(valid_ids) if valid_ids else None,
            "plan_rating_area_rows": len(rates),
        })
        print(f"{year}: {rates['plan_id'].nunique():,}/{len(valid_ids):,} plans with age-40 rates")

    panel = pd.concat(annual, ignore_index=True, sort=False)
    panel.to_csv(OUT / "plan_rating_area_age40_premiums.csv", index=False)

    issuer = panel.groupby(["market_year", "state", "issuer_id"]).agg(
        median_age40_premium=("individual_rate_age40", "median"),
        mean_age40_premium=("individual_rate_age40", "mean"),
        minimum_age40_premium=("individual_rate_age40", "min"),
        rated_plans=("plan_id", "nunique"),
        rating_areas=("rating_area_id", "nunique"),
    ).reset_index()
    issuer.to_csv(OUT / "issuer_state_premiums.csv", index=False)

    silver = panel.loc[panel["metal_level"].str.contains("Silver", case=False, na=False)].copy()
    benchmark = silver.groupby(["market_year", "state", "rating_area_id"]).agg(
        lowest_silver_age40_premium=("individual_rate_age40", "min"),
        silver_issuer_count=("issuer_id", "nunique"),
        silver_plan_count=("plan_id", "nunique"),
    ).reset_index()
    benchmark.to_csv(OUT / "state_rating_area_silver_premiums.csv", index=False)
    pd.DataFrame(diagnostics).to_csv(TABLES / "premium_linkage_summary.csv", index=False)


if __name__ == "__main__":
    main()
