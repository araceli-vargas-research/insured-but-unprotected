#!/usr/bin/env python3
"""Building the harmonized CMS Marketplace Transparency panels.

Raw files are never modified. CMS suppression markers (*, **, ***, N/A) are
converted to missing values only in processed outputs. Publication year and
claims year are kept separately because the Transparency PUF is released with
an approximately two-year lag.
"""

from io import BytesIO
from pathlib import Path
import re
from zipfile import ZipFile

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CMS = RAW / "cms_downloads"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "output" / "tables"

PUBLICATION_YEARS = range(2017, 2027)


def clean_name(value):
    value = str(value).strip().replace('"', "")
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return value


def numeric(series):
    cleaned = series.astype("string").str.replace("\u00a0", "", regex=False).str.strip().replace(
        {"*": pd.NA, "**": pd.NA, "***": pd.NA, "N/A": pd.NA, "nan": pd.NA}
    )
    cleaned = cleaned.str.replace(",", "", regex=False).str.replace("%", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def first_column(frame, *candidates):
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    return None


def read_single_file_zip(path, suffix):
    with ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(suffix)]
        if len(members) != 1:
            raise ValueError(f"Expected one {suffix} file in {path}; found {members}")
        return BytesIO(archive.read(members[0]))


def read_csv_content(content, **kwargs):
    raw = content.getvalue()
    try:
        return pd.read_csv(BytesIO(raw), encoding="utf-8", **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(BytesIO(raw), encoding="cp1252", **kwargs)


def find_header_row(content, sheet):
    preview = pd.read_excel(content, sheet_name=sheet, header=None, nrows=6, dtype="string")
    for row_number, row in preview.iterrows():
        if any(str(value).strip().lower() == "state" for value in row.dropna()):
            return int(row_number)
    raise ValueError(f"Could not locate header row in sheet {sheet}")


def load_medical_keys(publication_year):
    path = CMS / "03_plan_attributes_pufs" / f"{publication_year}_plan-attributes-puf.zip"
    content = read_single_file_zip(path, ".csv")
    usecols = ["StateCode", "IssuerId", "StandardComponentId", "MarketCoverage", "DentalOnlyPlan"]
    attrs = read_csv_content(content, dtype="string", usecols=lambda c: c in usecols, low_memory=False)
    attrs.columns = [clean_name(c) for c in attrs.columns]
    if "marketcoverage" in attrs:
        attrs = attrs.loc[attrs["marketcoverage"].str.contains("Individual", case=False, na=False)]
    if "dentalonlyplan" in attrs:
        attrs = attrs.loc[attrs["dentalonlyplan"].str.lower().eq("no")]
    issuer_keys = set(zip(attrs["statecode"].str.strip(), attrs["issuerid"].str.strip()))
    plan_ids = set(attrs["standardcomponentid"].dropna().str.strip())
    return issuer_keys, plan_ids


def load_individual_qhp(publication_year):
    path = CMS / "01_transparency_pufs" / f"{publication_year}_transparency-in-coverage-puf.zip"
    content = read_single_file_zip(path, ".xlsx")
    book = pd.ExcelFile(content)
    sheet = next((name for name in book.sheet_names if "Ind QHP" in name), None)
    if sheet is None:
        sheet = next(name for name in book.sheet_names if "PUF Transparency" in name)
    header = find_header_row(content, sheet)
    content.seek(0)
    frame = pd.read_excel(content, sheet_name=sheet, header=header, dtype="string")
    frame.columns = [clean_name(c) for c in frame.columns]
    frame = frame.loc[frame["state"].str.fullmatch(r"[A-Z]{2}", na=False)].copy()
    if "qhp_sadp" in frame:
        frame = frame.loc[frame["qhp_sadp"].str.upper().eq("QHP")].copy()
    elif "qhp_or_sadp" in frame:
        frame = frame.loc[frame["qhp_or_sadp"].str.upper().eq("QHP")].copy()
    elif publication_year <= 2020:
        medical_issuers, medical_plans = load_medical_keys(publication_year)
        if "plan_id" in frame:
            frame = frame.loc[frame["plan_id"].str.strip().isin(medical_plans)].copy()
        else:
            keys = list(zip(frame["state"].str.strip(), frame["issuer_id"].str.strip()))
            frame = frame.loc[[key in medical_issuers for key in keys]].copy()
    return frame, sheet, path


def build_issuer_panel(frame, publication_year, claims_year, claims_year_verified):
    key = ["state", "issuer_id"]
    issuer_name = first_column(frame, "issuer_name")

    aliases = {
        "claims_received_in_network": ["issuer_claims_received_in_network"],
        "claims_received_out_of_network": ["issuer_claims_received_out_of_network"],
        "claims_denied_in_network": ["issuer_claims_denied_in_network"],
        "claims_denied_out_of_network": ["issuer_claims_denied_out_of_network"],
        "claims_received_total_reported": ["issuer_claims_received"],
        "claims_denied_total_reported": ["issuer_claims_denials", "issuer_claims_denied"],
        "claims_resubmitted_in_network": ["issuer_claims_resubmitted_in_network"],
        "claims_resubmitted_out_of_network": ["issuer_claims_resubmitted_out_of_network"],
        "internal_appeals_filed": ["issuer_internal_appeals_filed", "issuer_internal_appeals_filled"],
        "internal_appeals_overturned": ["issuer_number_internal_appeals_overturned"],
        "external_appeals_filed": ["issuer_external_appeals_filed"],
        "external_appeals_overturned": ["issuer_number_external_appeals_overturned"],
    }
    aliases["claims_received_total_reported"].append("claims_received")
    aliases["claims_denied_total_reported"].extend(["claims_denials", "claims_denied"])
    aliases["internal_appeals_filed"].append("internal_appeals_filed")
    aliases["internal_appeals_overturned"].append("number_internal_appeals_overturned")
    aliases["external_appeals_filed"].append("external_appeals_filed")
    aliases["external_appeals_overturned"].append("number_external_appeals_overturned")

    selected = key + ([issuer_name] if issuer_name else [])
    column_map = {}
    for output, options in aliases.items():
        source = first_column(frame, *options)
        if source:
            selected.append(source)
            column_map[source] = output

    out = frame[selected].rename(columns=column_map).copy()
    if issuer_name and issuer_name != "issuer_name":
        out = out.rename(columns={issuer_name: "issuer_name"})

    measure_columns = [c for c in out.columns if c not in key + ["issuer_name"]]
    for column in measure_columns:
        out[column] = numeric(out[column])

    # Issuer fields repeat on plan rows. Suppression markers may coexist with a
    # disclosed numeric value; after converting suppression to missing, require
    # at most one distinct disclosed value before collapsing.
    checks = out.groupby(key, dropna=False)[measure_columns].nunique(dropna=True)
    if (checks > 1).any().any():
        bad = (checks > 1).stack()
        raise ValueError(f"Conflicting disclosed issuer fields: {bad[bad].index.tolist()[:10]}")
    out = out.groupby(key, as_index=False, dropna=False).first()

    for required in [
        "claims_received_in_network", "claims_received_out_of_network",
        "claims_denied_in_network", "claims_denied_out_of_network",
        "claims_received_total_reported", "claims_denied_total_reported",
        "internal_appeals_filed", "internal_appeals_overturned",
        "external_appeals_filed", "external_appeals_overturned",
    ]:
        if required not in out:
            out[required] = np.nan

    split_received = out[["claims_received_in_network", "claims_received_out_of_network"]].sum(axis=1, min_count=1)
    split_denied = out[["claims_denied_in_network", "claims_denied_out_of_network"]].sum(axis=1, min_count=1)
    out["claims_received_total"] = out["claims_received_total_reported"].where(
        out["claims_received_total_reported"].notna(), split_received
    )
    out["claims_denied_total"] = out["claims_denied_total_reported"].where(
        out["claims_denied_total_reported"].notna(), split_denied
    )

    out["denial_rate_total"] = out["claims_denied_total"] / out["claims_received_total"]
    out["denial_rate_in_network"] = out["claims_denied_in_network"] / out["claims_received_in_network"]
    out["internal_appeal_rate"] = out["internal_appeals_filed"] / out["claims_denied_total"]
    out["internal_reversal_rate"] = out["internal_appeals_overturned"] / out["internal_appeals_filed"]
    out["external_reversal_rate"] = out["external_appeals_overturned"] / out["external_appeals_filed"]
    out.replace([np.inf, -np.inf], np.nan, inplace=True)

    out.insert(0, "claims_year_verified", claims_year_verified)
    out.insert(0, "claims_year", claims_year)
    out.insert(0, "puf_publication_year", publication_year)
    return out


def build_plan_panel(frame, publication_year, claims_year, claims_year_verified):
    identifiers = [
        c for c in ["state", "issuer_id", "issuer_name", "plan_id", "plan_type", "metal_level"]
        if c in frame.columns
    ]
    measures = [c for c in frame.columns if c.startswith("plan_number_claim")]
    enrollment = [c for c in ["enrollment_data", "disenrollment_data", "average_monthly_enrollment", "average_monthly_disenrollment"] if c in frame.columns]
    out = frame[identifiers + measures + enrollment].copy()
    for column in measures + enrollment:
        out[column] = numeric(out[column])
    out.insert(0, "claims_year_verified", claims_year_verified)
    out.insert(0, "claims_year", claims_year)
    out.insert(0, "puf_publication_year", publication_year)
    return out


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    issuer_parts, plan_parts, inventory = [], [], []

    for publication_year in PUBLICATION_YEARS:
        claims_year = publication_year - 2
        verified = True
        frame, sheet, path = load_individual_qhp(publication_year)
        issuer = build_issuer_panel(frame, publication_year, claims_year, verified)
        plan = build_plan_panel(frame, publication_year, claims_year, verified) if "plan_id" in frame else None
        issuer_parts.append(issuer)
        if plan is not None:
            plan_parts.append(plan)
        inventory.append({
            "file": path.name,
            "sheet": sheet,
            "puf_publication_year": publication_year,
            "claims_year": claims_year,
            "claims_year_verified": verified,
            "raw_plan_rows": len(frame),
            "states": frame["state"].nunique(),
            "issuer_state_markets": len(issuer),
            "plans": frame["plan_id"].nunique() if "plan_id" in frame else 0,
        })

    issuer_panel = pd.concat(issuer_parts, ignore_index=True, sort=False)
    plan_panel = pd.concat(plan_parts, ignore_index=True, sort=False)
    issuer_panel.to_csv(PROCESSED / "issuer_state_year.csv", index=False)
    plan_panel.to_csv(PROCESSED / "plan_state_year.csv", index=False)
    pd.DataFrame(inventory).to_csv(TABLES / "file_inventory.csv", index=False)

    outcomes = [
        "denial_rate_total", "denial_rate_in_network", "internal_appeal_rate",
        "internal_reversal_rate", "external_reversal_rate",
    ]
    quality = []
    for year, group in issuer_panel.groupby("claims_year"):
        for outcome in outcomes:
            quality.append({
                "claims_year": year,
                "variable": outcome,
                "issuer_state_observations": len(group),
                "nonmissing": int(group[outcome].notna().sum()),
                "missing_share": float(group[outcome].isna().mean()),
            })
    pd.DataFrame(quality).to_csv(TABLES / "data_quality_summary.csv", index=False)

    known_issues = issuer_panel.loc[
        (issuer_panel["internal_reversal_rate"] > 1)
        | (issuer_panel["external_reversal_rate"] > 1)
        | (issuer_panel["internal_appeal_rate"] > 1)
        | (issuer_panel["denial_rate_total"] > 1),
        [
            "puf_publication_year", "claims_year", "state", "issuer_id", "issuer_name",
            "claims_received_total", "claims_denied_total", "internal_appeals_filed",
            "internal_appeals_overturned", "external_appeals_filed",
            "external_appeals_overturned", "denial_rate_total",
            "internal_appeal_rate", "internal_reversal_rate", "external_reversal_rate",
        ],
    ].copy()
    known_issues["review_status"] = "retain_and_investigate_source_reporting"
    known_issues.to_csv(TABLES / "known_data_issues.csv", index=False)

    attributes_content = read_single_file_zip(
        CMS / "03_plan_attributes_pufs" / "2026_plan-attributes-puf.zip", ".csv"
    )
    attributes = read_csv_content(attributes_content, dtype="string", low_memory=False)
    attributes = attributes.rename(columns={"StateCode": "state", "IssuerId": "issuer_id", "StandardComponentId": "plan_id"})
    attributes["plan_id"] = attributes["plan_id"].str.strip()
    latest = plan_panel.loc[plan_panel["puf_publication_year"] == 2026].copy()
    keep = [
        "state", "issuer_id", "plan_id", "IssuerMarketPlaceMarketingName", "MarketCoverage",
        "DentalOnlyPlan", "PlanMarketingName", "PlanType", "MetalLevel", "IsNewPlan",
        "NetworkId", "ServiceAreaId", "NationalNetwork", "IsHSAEligible",
        "MEHBDedInnTier1Individual", "MEHBInnTier1IndividualMOOP",
    ]
    keep = [c for c in keep if c in attributes.columns]
    attributes = attributes[keep].drop_duplicates(["state", "issuer_id", "plan_id"])
    linked = latest.merge(attributes, on=["state", "issuer_id", "plan_id"], how="left", indicator=True)
    linked.to_csv(PROCESSED / "plan_2026_attributes_linked.csv", index=False)

    link_summary = pd.DataFrame([{
        "transparency_plans": len(latest),
        "matched_plans": int((linked["_merge"] == "both").sum()),
        "plan_match_rate": float((linked["_merge"] == "both").mean()),
    }])
    link_summary.to_csv(TABLES / "plan_attributes_linkage.csv", index=False)


if __name__ == "__main__":
    main()
