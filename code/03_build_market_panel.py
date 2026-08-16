#!/usr/bin/env python3
"""Constructed annual medical-QHP plan and issuer-state market panels."""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CMS = ROOT / "data" / "raw" / "cms_downloads"
OUT = ROOT / "data" / "processed"
TABLES = ROOT / "output" / "tables"


def read_zip_csv(path):
    with ZipFile(path) as archive:
        member = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
        raw = archive.read(member)
    try:
        return pd.read_csv(BytesIO(raw), encoding="utf-8", dtype="string", low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(BytesIO(raw), encoding="cp1252", dtype="string", low_memory=False)


def main():
    plans = []
    for year in range(2015, 2027):
        path = CMS / "03_plan_attributes_pufs" / f"{year}_plan-attributes-puf.zip"
        frame = read_zip_csv(path)
        frame = frame.loc[
            frame["MarketCoverage"].str.contains("Individual", case=False, na=False)
            & frame["DentalOnlyPlan"].str.lower().eq("no")
            & ~frame["QHPNonQHPTypeId"].str.contains("Off the Exchange", case=False, na=False)
        ].copy()
        keep = [
            "StateCode", "IssuerId", "IssuerMarketPlaceMarketingName", "StandardComponentId",
            "PlanMarketingName", "PlanType", "MetalLevel", "IsNewPlan", "NetworkId",
            "ServiceAreaId", "NationalNetwork", "IsHSAEligible", "QHPNonQHPTypeId",
            "MEHBDedInnTier1Individual", "MEHBInnTier1IndividualMOOP",
        ]
        keep = [column for column in keep if column in frame]
        frame = frame[keep].drop_duplicates(["StateCode", "IssuerId", "StandardComponentId"])
        frame.insert(0, "market_year", year)
        plans.append(frame)

    plan_panel = pd.concat(plans, ignore_index=True, sort=False).rename(columns={
        "StateCode": "state", "IssuerId": "issuer_id", "IssuerMarketPlaceMarketingName": "issuer_name",
        "StandardComponentId": "plan_id", "PlanMarketingName": "plan_name", "PlanType": "plan_type",
        "MetalLevel": "metal_level", "IsNewPlan": "is_new_plan", "NetworkId": "network_id",
        "ServiceAreaId": "service_area_id", "NationalNetwork": "national_network",
        "IsHSAEligible": "is_hsa_eligible", "QHPNonQHPTypeId": "exchange_status",
        "MEHBDedInnTier1Individual": "individual_medical_deductible",
        "MEHBInnTier1IndividualMOOP": "individual_medical_moop",
    })
    OUT.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    plan_panel.to_csv(OUT / "medical_qhp_plan_year.csv", index=False)

    group = plan_panel.groupby(["market_year", "state", "issuer_id"], dropna=False)
    issuer = group.agg(
        issuer_name=("issuer_name", "first"),
        plan_count=("plan_id", "nunique"),
        product_count=("plan_id", lambda x: x.str[:10].nunique()),
        network_count=("network_id", "nunique"),
        service_area_count=("service_area_id", "nunique"),
    ).reset_index()
    issuer["new_plan_count"] = group["is_new_plan"].apply(
        lambda x: x.str.contains("new", case=False, na=False).sum()
    ).to_numpy()
    issuer.to_csv(OUT / "issuer_state_market_year.csv", index=False)

    state = issuer.groupby(["market_year", "state"]).agg(
        issuer_count=("issuer_id", "nunique"),
        plan_count=("plan_count", "sum"),
        product_count=("product_count", "sum"),
    ).reset_index()
    state.to_csv(OUT / "state_market_year.csv", index=False)

    summary = state.groupby("market_year").agg(
        states=("state", "nunique"),
        issuer_state_markets=("issuer_count", "sum"),
        plans=("plan_count", "sum"),
    ).reset_index()
    summary.to_csv(TABLES / "market_panel_summary.csv", index=False)
    print(f"Built {len(plan_panel):,} plan-year and {len(issuer):,} issuer-state-year observations.")


if __name__ == "__main__":
    main()
