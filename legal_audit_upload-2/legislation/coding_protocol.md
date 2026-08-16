# State-Law Coding Protocol

## Unit of observation

The event file records one jurisdiction-policy-family slot for each of the 50 states and the District of Columbia. If a family contains several legally distinct changes, duplicate the row and assign a new event ID. The analysis file is a state-year panel for 2015–2026.

## Coding sequence

1. Search the state legislature, insurance code, administrative code, insurance department bulletins, and official registers.
2. Record the enacted bill or regulation and its codified citation.
3. Read the operative text and definitions; do not code from a bill summary alone.
4. Record enactment, effective, implementation, amendment, and repeal dates separately.
5. Code the affected market: individual/Marketplace, fully insured group, Medicaid managed care, or self-funded ERISA plans.
6. Record exclusions, transition rules, grandfathering, enforcement authority, and whether the rule creates a private right or only administrative enforcement.
7. Save a stable official URL and an access date. Add a secondary source only as a discovery or interpretive aid.
8. A second reviewer independently checks the citation, effective date, scope, and treatment coding before the row becomes verified.

## Treatment rules

- Use the date the obligation becomes operative, not merely the enactment date.
- For midyear effective dates, preserve the exact date in the event sheet. The empirical specification should either use fractional exposure, assign treatment beginning in the next full plan year, or report both conventions.
- A missing law is not a zero. Code `0` only after a documented search supports absence of the defined protection.
- Code the incremental state requirement relative to the federal baseline. Do not relabel a federal obligation as state treatment.
- Do not assume a law reaches self-funded employer plans. Record any express application and then assess ERISA preemption separately.
- Do not combine unlike provisions into a single treatment without retaining the underlying indicators.
- Amendments that materially change deadlines, scope, exemptions, or enforcement require a new event row.

## Recommended primary outcomes and treatment

The initial design should use prior-authorization procedure as the main treatment family. Outcomes may include Marketplace denial rates, appeal rates, reversal rates, premiums, and issuer participation. Other legal families are best treated as separate indicators or prespecified indices after coding reliability is established.

## Review statuses

- `Not Started`: no legal conclusion.
- `In Review`: sources are being assessed.
- `Verified - First Review`: one reviewer has completed the primary-source coding.
- `Verified - Second Review`: an independent reviewer has confirmed it.
- `Needs Legal Review`: ambiguity remains about scope, preemption, dates, or interpretation.

## Audit trail

Never overwrite a material interpretation silently. Record the change in notes, preserve the earlier source, update `last_verified`, and identify the reviewer. The Git history should make all revisions traceable.

