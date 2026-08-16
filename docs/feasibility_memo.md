# CMS data feasibility memo

## Preliminary conclusion

The uploaded CMS files support a reproducible issuer-state-year panel. The core
claims, denial, and appeal fields repeat across plans but are invariant within
each issuer-state market, allowing safe collapse to that level.

The current pipeline produces 1,807 issuer-state-year outcome observations for
claims years 2015-2024, 48,300 medical-QHP plan-year observations for market
years 2015-2026, and 2,322 issuer-state-year participation observations. Every
medical QHP in the constructed plan panel links to an age-40 base premium in the
Rate PUF. The final outcome-to-market linkage rate is 79.9%; most unmatched
issuer-years also lack usable reported denial outcomes.

## Current coverage

- Publication years: 2017-2026.
- Claims years: 2015-2024.
- Individual medical QHPs only in the processed panels.
- Approximately 30-33 federal-platform states per year.
- State-based exchanges not using the federal platform are generally absent.

## Measurement changes

Publications through 2023 report aggregate issuer claims. Beginning with the 2024
publication, claims are split into in-network and out-of-network categories.
The script creates a harmonized total by summing those categories when needed.
An in-network-only outcome is therefore available for a shorter period.

Detailed plan-level denial reasons and resubmission measures also have shorter
histories and substantial missingness. They should be secondary outcomes.

## Identification still unresolved

The CMS data establish outcome feasibility, not causal identification. A legal
pilot must determine how many states adopted a consistently defined reform
during the observable claims period, whether it applied to Marketplace plans,
and whether sufficient untreated comparison states remain.

Two source anomalies are retained and flagged rather than silently removed:
one issuer reports more denied than received claims, and another reports more
appeals overturned than filed. See `output/tables/known_data_issues.csv`.

The ten-year outcome window is potentially adequate for a staggered-adoption
design, but credibility depends on the number, timing, and comparability of
verified reforms. A narrower policy family remains recommended.

## ERISA limitation

The Form 5500/MEPS analysis should initially be descriptive. Form 5500 commonly
identifies the plan sponsor's location rather than every participant's state,
and some smaller plans are not required to file. It should not be represented
as direct self-funded-plan denial data.
