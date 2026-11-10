import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
D="2026-11-10"

# Eesti Pank / ECB MIR series, monthly, pulled from the ECB Data Portal on 2026-11-10.
# 15 months covers the year-on-year comparison in the market page.
AVG = [("2025-07",3.79),("2025-08",3.78),("2025-09",3.75),("2025-10",3.75),("2025-11",3.76),
       ("2025-12",3.73),("2026-01",3.80),("2026-02",3.77),("2026-03",3.88),("2026-04",4.05),
       ("2026-05",4.12),("2026-06",4.14),("2026-07",4.25),("2026-08",4.26),("2026-09",4.45)]
VAR = [("2025-07",3.68),("2025-08",3.69),("2025-09",3.67),("2025-10",3.67),("2025-11",3.69),
       ("2025-12",3.67),("2026-01",3.68),("2026-02",3.69),("2026-03",3.80),("2026-04",3.93),
       ("2026-05",4.02),("2026-06",4.06),("2026-07",4.14),("2026-08",4.16),("2026-09",4.37)]
VOL = [("2026-07",293),("2026-08",270),("2026-09",302)]

src = {
 "meta": {"updated": D, "note": "Official and reference context for the bank dataset. Values copied from the cited pages on the checked date."},
 "euribor_6m": {
   "value_pct": 3.016, "value_date": "2026-11-06",
   "recent": [{"date":"2026-11-06","pct":3.016},{"date":"2026-11-05","pct":3.014},{"date":"2026-11-04","pct":3.008},{"date":"2026-11-03","pct":3.006},{"date":"2026-11-02","pct":2.994}],
   "source": "https://www.euribor-rates.eu/en/current-euribor-rates/",
   "source_type": "secondary (publishes EMMI rates with 24h delay)",
   "administrator": "European Money Markets Institute (EMMI), https://www.emmi-benchmarks.eu/",
   "cross_check": "Swedbank home-loan calculator showed 6M Euribor 3.016% on 2026-11-09 (https://www.swedbank.ee/private/credit/loans/home)",
   "live_file": "data/euribor.json (refresh with fetch_euribor.py)",
   "licensing_note": "Republishing Euribor values in a public dataset may require an EMMI licence. Open question; until resolved, the site may prefer linking to the source.",
   "checked": D},
 "eesti_pank_new_housing_loans": {
   "description": "Estonia, MFI interest rate statistics (compiled by Eesti Pank, published via the ECB Data Portal)",
   "avg_rate_new_business_pct": [{"month":m,"pct":p} for m,p in AVG],
   "avg_rate_new_business_series": "MIR.M.EE.B.A2C.A.R.A.2250.EUR.N (loans to households for house purchase, new business incl. renegotiations, all fixation periods)",
   "avg_rate_variable_upto_1y_pct": [{"month":m,"pct":p} for m,p in VAR],
   "avg_rate_variable_series": "MIR.M.EE.B.A2C.F.R.A.2250.EUR.N",
   "volume_pure_new_loans_eur_million": [{"month":m,"value":v} for m,v in VOL],
   "volume_series": "MIR.M.EE.B.A2C.A.B.A.2250.EUR.P (pure new loans, excludes renegotiations)",
   "source": "https://data-api.ecb.europa.eu/service/data/MIR/M.EE.B.A2C.A.R.A.2250.EUR.N?lastNObservations=15",
   "eesti_pank_stats_page": "https://statistika.eestipank.ee/et/p/FINANTSSEKTOR/147/979",
   "next_release": "Eesti Pank Q3 2026 interest-rate statistics release on 2026-11-19 08:00 (per Eesti Pank press page); October bank statistics on 2026-11-25",
   "checked": D},
 "emta_housing_loan_interest": {
   "deduction_ended": "2024-01-01",
   "last_year_deductible": 2023,
   "annual_cap_eur": 300,
   "max_refund_eur": 60,
   "tax_rate_then_pct": 20,
   "still_deductible": "Training costs and donations up to €1,200 but not more than 50% of taxable income; III pillar contributions up to 15% of taxable income and €6,000 a year",
   "source": "https://emta.ee/eraklient/eluasemelaenu-intressid", "checked": D},
 "eesti_pank_lending_rules": {
   "max_ltv_pct": 85, "max_ltv_state_guaranteed_pct": 90,
   "max_dsti_pct": 50, "dsti_stress_rate": "higher of contract rate or 6% for variable-rate loans",
   "max_term_years": 30,
   "exception": "Each bank may issue up to 15% of quarterly new housing-loan volume outside these limits",
   "in_force_since": "2015-03-01",
   "source": "https://www.eestipank.ee/finantsstabiilsus/eluasemelaenude-valjastamise-nouded", "checked": D},
 "eis_housing_loan_guarantee": {
   "how_to_apply": "Through the bank; no separate application to EIS",
   "issuing_banks": ["Bigbank","Citadele Pank","Coop Pank","Holm Bank","LHV Pank","Luminor","SEB Pank","Swedbank"],
   "min_down_payment_pct": 10, "min_down_payment_large_family_pct": 5,
   "guarantee_size": "up to 24% of collateral value, max €20,000; energy-efficient group max €50,000; large families up to 40%, max €50,000",
   "loan_amount_cap": "none",
   "fee": "3% of guaranteed amount, one-off at signing; large families 2%",
   "term_over_30y_conditions": "borrowers' age at loan end max 70 and property built or fully renovated within the last 10 years",
   "no_other_home_rule": "Young family, young specialist, energy-efficient, tenant and veteran groups: borrower may not own a home at application, unless it is sold within 12 months",
   "payment_holiday": "Loan holiday possible until a child turns 3",
   "target_groups": {
     "young_family": "Parent aged up to 35 with at least one child up to 16, or parent aged up to 40 with at least two children up to 16",
     "young_specialist": "Aged up to 35 with higher, vocational secondary or professional education, employed (probation ended) or in office, or sole proprietor active at least 1 year",
     "energy_efficient": "Buying an energy-efficient home or renovating to energy efficiency; proven by energy label or calculation",
     "large_family": "At least three children up to 19",
     "veteran": "Defence Forces or Defence League veteran (foreign mission or injured in service)",
     "returned_dwelling_tenant": "Tenant in a dwelling returned under ownership reform"},
   "source": "https://eis.ee/teenused/eluasemelaenu-kaendus/", "checked": D},
 "eis_rural_housing_loan_guarantee": {
   "banks": ["Coop Pank","Citadele"],
   "min_down_payment_pct": "15% of project value; 5% or 10% if borrower also belongs to another EIS target group",
   "guarantee": "up to 80% of outstanding principal, max €150,000",
   "loan_cap": "€200,000 and up to 95% of purchase/renovation cost",
   "fee": "1% per year of guarantee balance, paid monthly",
   "source": "https://eis.ee/teenused/maapiirkonna-eluasemelaenu-kaendus/", "checked": D}
}
json.dump(src, open(ROOT / "data" / "sources.json", "w"), ensure_ascii=False, indent=2)
