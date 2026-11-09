# Estonian housing-loan terms dataset

**Last updated:** 2026-11-09 (all bank and official-source values were checked on this date unless a field says otherwise)
**Files:** `banks.json`, `banks.csv` (same content, flattened), `sources.json` (official context), `euribor.json` (Euribor, written by `scripts/fetch_euribor.py`), `schema.json` (field documentation)
**Version:** 0.1.0

The public copies of these files are served at `/data/` on the site. `euribor.json` also has an `updated` date (the fetch date) beside `fetched_at`.

## Neutrality statement

- This dataset lists the housing-loan terms that each bank **publishes** on its own website and price list.
- Banks are listed in **alphabetical order**. The order means nothing.
- There is **no ranking, score, "best" label or recommendation**. Nothing here says which bank suits anyone.
- This is **not financial advice** and not an offer. Rates are individual; each bank decides after its own assessment.
- The publisher earns nothing from any bank: no affiliate links, no paid placement.
- `null` means the bank does not publish the value, or it was not found on the cited page. It never means "zero" or "no".

## Coverage

Eight banks issue housing loans in Estonia and take part in the EIS housing-loan guarantee:
Bigbank, Citadele, Coop Pank, Holm Bank, LHV, Luminor, SEB, Swedbank.
Inbank is excluded (it offers only an unsecured "kodu väikelaen"). Non-bank property lenders are out of scope for v0.1.

## Schema (`banks.json`)

Top level: `{ "meta": {...}, "banks": [ ... ] }`

Each bank has `id`, `bank_name` (short), `legal_name`, then fields shaped like:

```json
{ "value": "<string | number | boolean | list | null>",
  "unit": "<optional>",
  "note": "<string or null: caveats, derivations, why null>",
  "source": "<URL the value was read from>",
  "checked": "YYYY-MM-DD" }
```

| Field | Meaning |
|---|---|
| product_url_et / product_url_en | Bank's home-loan page in Estonian / English |
| loan_types | Housing-loan products named on the page |
| rate_basis | Reference rate and margin structure (e.g. 6M Euribor + individual margin) |
| margin | `"individual"` when only examples or "from" rates are published |
| promo_rates | Time-limited or group offers, quoted with validity dates |
| contract_fee | Arrangement / contract fee (lepingutasu) |
| valuation_fee | Property valuation cost if published |
| amendment_fee | Contract change fees |
| early_repayment_fee | Early repayment compensation |
| min_loan_amount_eur | Minimum loan amount |
| min_down_payment_pct | Standard minimum own contribution |
| max_ltv_pct / max_ltv_with_eis_pct | Max loan-to-value without / with EIS guarantee ("derived" in note if computed from the down payment) |
| usual_max_ltv_pct | Usual maximum LTV when stated separately from the published or derived figure. Omitted when not reported |
| regional_ltv_rules | Region effect on LTV. `null`, a short statement, or an object of county limits (CSV holds objects and stage lists as JSON text) |
| property_condition_ltv | Whether the condition of the property can change LTV. Omitted when not reported |
| construction_ltv_stages | Construction-loan LTV by stage: `stage`, `max_ltv_pct`, and optionally `basis`, `condition`, `qualifier`. Omitted when not reported |
| max_term_years | Maximum term |
| eis_participation | Bank offers the EIS housing-loan guarantee |
| eis_programs | EIS target groups the bank names: young_family, young_specialist, energy_efficient, large_family, veteran, returned_dwelling_tenant, rural. `null` = bank does not itemise them |
| eis_rural | Bank offers the EIS rural housing-loan guarantee (per EIS) |
| green_discount | Energy-class (A/B) rate or fee benefits |
| young_buyer_offer | Age-based offers |
| worked_example.* | The bank's representative APR example (tüüpnäide): loan_amount_eur, term_months, rate_type, margin_pct, euribor_pct, euribor_date, nominal_rate_pct, apr_pct, contract_fee_eur, monthly_payment_eur, total_repayments_eur, total_payable_eur, total_cost_of_credit_eur, example_date |
| income_rules | Published income / affordability conditions |
| dsti_max_pct | Published max debt-service-to-income |
| digital_application | How to apply online |
| account_requirement | Whether a current account at the bank is required |

Values computed by us (not stated by the bank) say "Computed" or "Derived" in `note`.

**Non-public values.** A field whose `source` is not a URL comes from industry knowledge, not from a public page. Do not present it as the bank's published term. The site labels it "industry insider information, not published by the bank".

- Luminor `regional_ltv_rules`: 80% LTV outside Harju and Tartu county, 90% with the EIS guarantee; Harju and Tartu county left null. Source: `Information from a former member of Luminor's housing loan team (not publicly published by Luminor), 2026-11-09`.
- Bigbank `usual_max_ltv_pct` (usually 85%), `regional_ltv_rules` (region usually does not change the LTV), `property_condition_ltv` (the condition of the property can lower the LTV), and `construction_ltv_stages` (ehituslaen: usually 50% of the land plot's value, 70% once the building is closed, 85% at 95% complete). Source: `Information from Sander Seppik, a former member of Bigbank's housing loan team (insider information, not published on Bigbank's website), 2026-11-09`. Bigbank's published `max_ltv_pct` of 85% stays a figure derived from the public down-payment term.

### CSV

One row per bank. Each field becomes three columns: `<field>`, `<field>__note`, `<field>__source`.
Worked-example fields are prefixed `example_`. Lists of text are joined with ` | `. Lists of objects, including `construction_ltv_stages`, are JSON text.

## Official context (`sources.json`)

- 6-month Euribor (latest 5 fixings in this snapshot, secondary source with EMMI delay; licensing note included)
- Average rate and volume of new housing loans in Estonia (ECB MIR series compiled by Eesti Pank)
- Eesti Pank housing-loan limits (LTV 85%/90%, DSTI 50% at 6% stress, 30 years)
- EIS housing-loan guarantee and rural guarantee terms

## Euribor (`euribor.json`)

Run `python3 scripts/fetch_euribor.py` from the repository root to refresh 1M, 3M, 6M and 12M Euribor from https://www.euribor-rates.eu/en/. Each rate carries `rate_pct`, `value_date`, `source_url`; the file carries `fetched_at` and `updated`. The source republishes EMMI rates with a 24-hour delay.

The script writes the file only after all four tenors parse and pass range and freshness checks. A failed run leaves the previous file in place and exits non-zero. `python3 scripts/fetch_euribor.py --dry-run` prints the parse and does not write.

**Licensing — open question:** Euribor is administered by EMMI (European Money Markets Institute). Publicly redistributing Euribor values (including in this dataset or an API) may require an EMMI licence. That question is under review. Until it is resolved, the site republishes the fixings with attribution and a link to the source. Not legal advice.

## Freshness

Worked examples carry their own Euribor date. Several are old (Swedbank: 2025-07-09; Holm: 2025-04-11) — they are reproduced as published, not updated.
Re-check every field at least monthly; promotions expire (e.g. Luminor offer ends 2026-12-01; SEB, Citadele, LHV, Swedbank offers end 2026-12-31).

## Licence

Proposed: CC BY 4.0 for the compilation. Underlying facts belong to the banks and public bodies cited.
