#!/usr/bin/env python3
"""Merged denial outcomes with contemporaneous market and premium measures."""

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
TABLES = ROOT / "output" / "tables"


def main():
    outcomes = pd.read_csv(OUT / "issuer_state_year.csv", dtype={"issuer_id": "string"})
    market = pd.read_csv(OUT / "issuer_state_market_year.csv", dtype={"issuer_id": "string"})
    premiums = pd.read_csv(OUT / "issuer_state_premiums.csv", dtype={"issuer_id": "string"})

    market = market.rename(columns={"market_year": "claims_year"})
    premiums = premiums.rename(columns={"market_year": "claims_year"})
    keys = ["claims_year", "state", "issuer_id"]

    market_keep = [c for c in market.columns if c != "issuer_name"]
    panel = outcomes.merge(market[market_keep], on=keys, how="left", indicator="market_merge")
    panel = panel.merge(premiums, on=keys, how="left", indicator="premium_merge")
    panel.to_csv(OUT / "analysis_issuer_state_year.csv", index=False)

    summary = panel.groupby("claims_year").agg(
        outcome_observations=("issuer_id", "size"),
        market_matches=("market_merge", lambda x: x.eq("both").sum()),
        premium_matches=("premium_merge", lambda x: x.eq("both").sum()),
        denial_rate_observations=("denial_rate_total", "count"),
    ).reset_index()
    summary["market_match_share"] = summary["market_matches"] / summary["outcome_observations"]
    summary["premium_match_share"] = summary["premium_matches"] / summary["outcome_observations"]
    summary.to_csv(TABLES / "analysis_panel_linkage.csv", index=False)
    print(f"Built {len(panel):,} analysis rows; market match {panel.market_merge.eq('both').mean():.1%}; premium match {panel.premium_merge.eq('both').mean():.1%}.")


if __name__ == "__main__":
    main()
