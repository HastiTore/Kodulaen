import json, csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
D = "2026-11-09"
BIGBANK_INSIDER = "Information from Sander Seppik, a former member of Bigbank's housing loan team (insider information, not published on Bigbank's website), 2026-11-09"
def F(value, source, note=None, unit=None, checked=None):
    d = {"value": value}
    if unit: d["unit"] = unit
    d["note"] = note
    d["source"] = source
    d["checked"] = checked or D
    return d
EIS_PAGE = "https://eis.ee/teenused/eluasemelaenu-kaendus/"
EIS_RURAL = "https://eis.ee/teenused/maapiirkonna-eluasemelaenu-kaendus/"
EP_RULES = "https://www.eestipank.ee/finantsstabiilsus/eluasemelaenude-valjastamise-nouded"

banks = []

# ---------- Bigbank ----------
P = "https://www.bigbank.ee/kodulaen/"; PT = "https://www.bigbank.ee/kodulaen/?tab=kodulaenu-kkk"
PRE = "https://static.bigbank.ee/assets/2026/02/02114022/Erakliendi_kodulaenu_kinnisvara_tagatisel_laenu_lepingueelne_teabeleht_EE_14_01_2026.pdf"
banks.append(dict(
 id="bigbank", bank_name="Bigbank AS",
 product_url_et=F(P, P), product_url_en=F(None, None, "No English home-loan page found (bigbank.ee/en/home-loan returns 404)."),
 loan_types=F(["kodulaen (annuity schedule)", "kodulaen erigraafikuga (interest-only start period)", "refinancing"], P),
 rate_basis=F("3, 6 or 12 month Euribor + individual margin; negative Euribor floored at 0", P),
 margin=F("individual", P, "No margin figure published; worked example states only the total rate 4.697% (margin + 6M Euribor)."),
 promo_rates=F(None, P, "No rate promotion shown on 2026-11-09."),
 contract_fee=F("0.4% of loan amount, min €150", P),
 valuation_fee=F(None, P, "Set by valuer; bank names partner Pindi Kinnisvara with -20% discount (code BIG20). Valuation by EKHÜ level 6/7 valuer required."),
 amendment_fee=F(None, PRE, "Not published on loan page; pre-contract sheet says amendments by agreement. Price list page not found (bigbank.ee/hinnakiri 404)."),
 early_repayment_fee=F("Full early repayment of variable-rate loan: 3 months' interest; none if bank notified at least 3 months ahead", PRE),
 min_loan_amount_eur=F(30000, P, "Smaller sums via 'kodu väikelaen'."),
 min_down_payment_pct=F(15, P, "10% with EIS guarantee; down to 0% with additional collateral. EIS not available with the special (erigraafik) schedule."),
 max_ltv_pct=F(85, P, "Derived from 15% minimum down payment."),
 max_ltv_with_eis_pct=F(90, P),
 usual_max_ltv_pct=F(85, BIGBANK_INSIDER, "Standard maximum LTV is usually 85%."),
 regional_ltv_rules=F("Region usually does not change the LTV.", BIGBANK_INSIDER),
 property_condition_ltv=F("The condition of the property can lower the LTV.", BIGBANK_INSIDER),
 construction_ltv_stages=F([
     {"stage": "land_plot", "max_ltv_pct": 50, "basis": "value of the land plot", "qualifier": "usually"},
     {"stage": "building_closed", "max_ltv_pct": 70, "condition": "walls, roof, windows and doors installed"},
     {"stage": "building_95_percent_complete", "max_ltv_pct": 85},
   ], BIGBANK_INSIDER, "Construction loan (ehituslaen). LTV starts at usually 50% of the value of the land plot; once the building is closed (walls, roof, windows and doors installed) the LTV increases to 70%; once the building is 95% complete the LTV increases to 85%."),
 max_term_years=F(30, P),
 eis_participation=F(True, P),
 eis_programs=F(None, P, "Bigbank's page describes the EIS (KredEx) guarantee but does not itemise target groups. EIS lists Bigbank among the eight banks that issue the guarantee, so all six groups can be used; Bigbank does not set them out. The rural guarantee is a separate product."),
 eis_rural=F(False, EIS_RURAL, "EIS says the rural guarantee is offered by Coop Pank and Citadele only. Bigbank accepts the MES rural co-loan (kaaslaen) up to 50% of the need."),
 green_discount=F(None, P, "No energy-class discount published."),
 young_buyer_offer=F(None, P, "None published beyond EIS."),
 worked_example=dict(
   loan_amount_eur=F(135200, PT), term_months=F(307, PT), rate_type=F("variable (margin + 6M Euribor)", PT),
   margin_pct=F(None, PT, "Not split out in the example."), euribor_pct=F(None, PT, "Not stated."), euribor_date=F(None, PT, "Not stated."),
   nominal_rate_pct=F(4.697, PT), apr_pct=F(4.91, PT), contract_fee_eur=F(540.80, PT), monthly_payment_eur=F(762.54, PT),
   total_repayments_eur=F(234096.47, PT), total_payable_eur=F(234096.47, PT, "Bank states total payable equal to repayments total."),
   total_cost_of_credit_eur=F(None, PT), example_date=F(None, PT, "Undated. A second example for the interest-only schedule (€217,000, 316 months, 4.707%, APR 4.91%) is on the same tab.")),
 income_rules=F("Regular official income in euros at least €600/month; two borrowers together at least €950/month; age 18+, Estonian residence address", P),
 dsti_max_pct=F(None, P, "Not stated on page; Eesti Pank rule caps all loan payments at 50% of net income (6% stress rate)."),
 digital_application=F("Online application form on product page; bank then contacts applicant", P),
 account_requirement=F(None, P, "Not stated."),
))

# ---------- Citadele ----------
P = "https://www.citadele.ee/et/private/mortgage/"
banks.append(dict(
 id="citadele", bank_name="AS Citadele banka Eesti filiaal",
 product_url_et=F(P, P), product_url_en=F("https://www.citadele.ee/en/private/mortgage/", P),
 loan_types=F(["kodulaen", "roheline kodulaen", "kodu refinantseerimislaen", "hüpoteeklaen (up to 75% LTV)", "paindlik laen"], P),
 rate_basis=F("Fixed margin + 6M Euribor (variable); fixed rate also offered", P),
 margin=F("individual", P, "Worked example margin 1.8%."),
 promo_rates=F(["€0 contract fee when buying new home directly from a developer (to 31.12.2026)", "Families with 3+ children: €0 contract fee, valuation reimbursed up to €450 (applications 01.02–31.12.2026)", "Refinancing: notary and valuation costs reimbursed up to €600 (applications to 31.12.2026)"], P),
 contract_fee=F("Up to 1% of loan amount, min €200", P),
 valuation_fee=F(None, P, "Set by valuer (bank publishes accepted valuers)."),
 amendment_fee=F("Other contract amendments 0.75% of balance, min €200; payment date/account change once a year free, then €75", P),
 early_repayment_fee=F("3 months' interest; not applied with 3 months' notice", P),
 min_loan_amount_eur=F(None, P, "Not published."),
 min_down_payment_pct=F(None, P, "Standard down payment not stated; EIS: 10% (5% large families)."),
 max_ltv_pct=F(None, P, "Standard LTV not stated on page."),
 max_ltv_with_eis_pct=F(95, P, "Up to 95% for large families with EIS; 90% for families with children, young specialists, energy-efficient homes."),
 max_term_years=F(30, P),
 eis_participation=F(True, P),
 eis_programs=F(["young_family", "young_specialist", "energy_efficient", "large_family", "veteran", "returned_dwelling_tenant", "rural"], P),
 eis_rural=F(True, EIS_RURAL),
 green_discount=F("Better loan terms for A or B energy class homes (amount not published)", P),
 young_buyer_offer=F(None, P, "No age-based offer; family offer for 3+ children."),
 worked_example=dict(
   loan_amount_eur=F(120000, P), term_months=F(360, P), rate_type=F("variable", P), margin_pct=F(1.8, P), euribor_pct=F(2.820, P), euribor_date=F("2026-09-11", P),
   nominal_rate_pct=F(4.620, P), apr_pct=F(4.79, P, "With €0 promotional fee. Same page gives APR 4.88% with a €1,200 fee (total €224,447.18)."),
   contract_fee_eur=F(0, P), monthly_payment_eur=F(622.15, P), total_repayments_eur=F(223247.18, P), total_payable_eur=F(223247.18, P),
   total_cost_of_credit_eur=F(None, P), example_date=F("2026-09-11", P, "Date of Euribor used.")),
 income_rules=F(None, P, "No written minimum; the calculator accepts net income from €750/month."),
 dsti_max_pct=F(None, P),
 digital_application=F("Online via Citadele internet bank; non-clients log in with Smart-ID or Mobile-ID", P),
 account_requirement=F(None, P, "Some terms apply only if borrowers use Citadele as main bank (wording on page)."),
))

# ---------- Coop ----------
P = "https://www.cooppank.ee/eraklient/kodu/kodulaen"; PL = "https://res30f.cooppank.ee/image/upload/dokumendid/est/hinnakiri_eraklient_0101.pdf"
banks.append(dict(
 id="coop", bank_name="Coop Pank AS",
 product_url_et=F(P, P), product_url_en=F("https://www.cooppank.ee/en/private/home/home-loan", P),
 loan_types=F(["kodulaen", "õpetaja kodulaen", "kodukaitsja kodulaen", "ehituslaen", "refinancing", "kinnisvara tagatisel laen"], P),
 rate_basis=F("Individual margin + 6M Euribor; fixing for a longer period possible", P),
 margin=F("individual", P, "Worked example margin 1.600%."),
 promo_rates=F(["A energy class: rate from 1.49% (as worded on page)"], P),
 contract_fee=F("Up to 1% of loan amount, min €100 (construction loan min €350)", PL, "Price list section valid from 16.03.2026."),
 valuation_fee=F(None, P, "Valuation by bank-accepted firm; fee set by valuer."),
 amendment_fee=F("Margin change up to 0.5% of balance, min €200; rate-type change 1.5%, min €350; payment holiday €75; other amendments from €200", PL),
 early_repayment_fee=F("Variable rate: 3 months' interest on amount repaid, none with 3 months' written notice; fixed rate: up to 1%", PL),
 min_loan_amount_eur=F(10000, P),
 min_down_payment_pct=F(15, P, "Lower with EIS; MES co-loan accepted as down payment; additional collateral accepted."),
 max_ltv_pct=F(85, P, "Derived from 15% minimum down payment."),
 max_ltv_with_eis_pct=F(None, P, "Not stated on page; EIS rule is 90% (95% large families)."),
 max_term_years=F(30, P),
 eis_participation=F(True, P),
 eis_programs=F(None, P, "Page says 'teeme koostööd EISiga' without itemising target groups; EIS lists Coop among issuing banks."),
 eis_rural=F(True, EIS_RURAL),
 green_discount=F("A energy class: rate from 1.49%", P),
 young_buyer_offer=F(None, P, "None published; separate teacher and home-defence (kodukaitsja) loans exist."),
 worked_example=dict(
   loan_amount_eur=F(115000, P), term_months=F(360, P), rate_type=F("variable", P), margin_pct=F(1.600, P), euribor_pct=F(2.706, P), euribor_date=F("2026-08-01", P),
   nominal_rate_pct=F(4.306, P, "Computed: margin + Euribor (bank does not state the sum)."), apr_pct=F(4.306, P, "Bank-stated APR. Equals the computed nominal rate — possible inconsistency in the bank's example (Open)."),
   contract_fee_eur=F(100, P), monthly_payment_eur=F(None, P), total_repayments_eur=F(205223.72, P), total_payable_eur=F(205324.25, P),
   total_cost_of_credit_eur=F(None, P), example_date=F("2026-08-01", P, "Date of Euribor used.")),
 income_rules=F("Minimum net income €700/month; Estonian citizen or resident permit holder; age at loan end max 75; no active payment defaults", P),
 dsti_max_pct=F(None, P),
 digital_application=F("Online application; 'first offer within a minute'", P),
 account_requirement=F(None, P),
))

# ---------- Holm ----------
P = "https://www.holmbank.ee/et/eraklient/laenud/holm-kodulaen"; PL = "https://www.holmbank.ee/et/eraklient/hinnakiri"
banks.append(dict(
 id="holm", bank_name="Holm Bank AS",
 product_url_et=F(P, P), product_url_en=F("https://www.holmbank.ee/en/private-individual/loans/holm-home-loan", P),
 loan_types=F(["kodulaen (purchase, build, extend, renovate; incl. summer house)", "hüpoteeklaen"], P),
 rate_basis=F("6M Euribor + personal margin; negative Euribor floored at 0", P),
 margin=F("individual", P, "Worked example margin 4%."),
 promo_rates=F(None, P, "None shown."),
 contract_fee=F("1% of loan amount, min €150", P),
 valuation_fee=F(None, P, "Set by valuer; Lahe Kinnisvara gives Holm clients 10% off."),
 amendment_fee=F("1% of loan amount, min €150 (price list line 'contract conclusion and amendment')", PL, "Price list valid from 09.03.2026."),
 early_repayment_fee=F("3 months' interest; not applied with 3 months' notice", PL),
 min_loan_amount_eur=F(25000, P),
 min_down_payment_pct=F(15, P, "10% with EIS; 0% with additional collateral."),
 max_ltv_pct=F(85, P), max_ltv_with_eis_pct=F(90, P), max_term_years=F(30, P),
 eis_participation=F(True, P),
 eis_programs=F(None, P, "Page refers to EIS terms without itemising target groups."),
 eis_rural=F(False, EIS_RURAL),
 green_discount=F(None, P, "None published."),
 young_buyer_offer=F(None, P, "None published."),
 worked_example=dict(
   loan_amount_eur=F(70000, P), term_months=F(300, P), rate_type=F("variable", P), margin_pct=F(4.0, P), euribor_pct=F(2.244, P), euribor_date=F("2025-04-11", P),
   nominal_rate_pct=F(6.244, P, "Computed: margin + Euribor."), apr_pct=F(6.63, P), contract_fee_eur=F(700, P), monthly_payment_eur=F(None, P),
   total_repayments_eur=F(139324.67, P), total_payable_eur=F(140024.67, P), total_cost_of_credit_eur=F(None, P),
   example_date=F("2025-04-11", P, "Euribor date is about 19 months old as of 2026-11-09.")),
 income_rules=F("Regular income adequate in the bank's assessment; all loan payments max 50% of regular monthly income", P),
 dsti_max_pct=F(50, P),
 digital_application=F("Holm self-service (iseteenindus); valuation report needed before signing, not at application", P),
 account_requirement=F(None, P),
))

# ---------- LHV ----------
P = "https://www.lhv.ee/et/kodulaen"
banks.append(dict(
 id="lhv", bank_name="AS LHV Pank",
 product_url_et=F(P, P), product_url_en=F("https://www.lhv.ee/en/home-loan", P),
 loan_types=F(["kodulaen", "noorte kodulaen (age ≤30)", "üürikodu laen", "koduvahetus", "ehituse finantseerimine", "refinancing", "laen kodu ostuks välismaal"], P),
 rate_basis=F("Individual margin + 6M Euribor", P),
 margin=F("individual", P, "Worked example margin 1.6%."),
 promo_rates=F(["New A/B energy class home: from 1.49% + 6M Euribor", "Rental home loan: from 1.89% + 6M Euribor", "Developer partner offers (e.g. Merko): €0 contract fee to 31.12.2026"], P),
 contract_fee=F("0.5–0.9% of loan amount, min €300", P),
 valuation_fee=F("LHV internal valuation for apartments €150; expert valuation per valuer's price list", P),
 amendment_fee=F("From €100", P),
 early_repayment_fee=F("Free (page: 'Laenu ennetähtaegne tagastamine tasuta'; contract termination free)", P),
 min_loan_amount_eur=F(20000, P),
 min_down_payment_pct=F(15, P, "10% with EIS (KredEx); 5% for large families; calculator also requires at least €10,000."),
 max_ltv_pct=F(85, P), max_ltv_with_eis_pct=F(90, P, "95% for large families (5% down payment)."),
 max_term_years=F(30, P, "Up to 35 years for borrowers aged up to 30 at application."),
 eis_participation=F(True, P),
 eis_programs=F(["young_family", "young_specialist", "energy_efficient", "large_family", "veteran"], P),
 eis_rural=F(False, EIS_RURAL),
 green_discount=F("New A/B energy class home: from 1.49% + 6M Euribor", P),
 young_buyer_offer=F("Noorte kodulaen (age ≤30): €0 contract fee, term up to 35 years, personal loan manager, may apply with a parent", P),
 worked_example=dict(
   loan_amount_eur=F(170000, P), term_months=F(360, P), rate_type=F("variable", P), margin_pct=F(1.6, P), euribor_pct=F(None, P, "Not stated; implied 3.0% (4.60 − 1.6)."), euribor_date=F(None, P, "Not stated."),
   nominal_rate_pct=F(4.60, P), apr_pct=F(4.711, P), contract_fee_eur=F(300, P), monthly_payment_eur=F(None, P),
   total_repayments_eur=F(None, P), total_payable_eur=F(314016.63, P, "Bank calls it 'kogukulu'; treated as total payable."), total_cost_of_credit_eur=F(None, P), example_date=F(None, P, "Undated.")),
 income_rules=F("Loan and leasing payments together up to 50% of net income; actual max depends on income and family size", P),
 dsti_max_pct=F(50, P),
 digital_application=F("Online application; first offer within 24 hours; LHV account not required", P),
 account_requirement=F(None, P, "Non-clients submit 6 months of digitally signed statements."),
))

# ---------- Luminor ----------
P = "https://luminor.ee/era/kodulaen"; LU = "https://luminor.ee/era/kodulaenu-uldinfo"; PL = "https://luminor.ee/s3fs-public/pricelists/pricelist_58_private_et-ee.pdf"
banks.append(dict(
 id="luminor", bank_name="Luminor Bank AS",
 product_url_et=F(P, P, "JavaScript-rendered; read with a headless browser."), product_url_en=F("https://luminor.ee/retail/mortgage-loan", P),
 loan_types=F(["kodulaen", "koduvahetuslaen", "refinancing", "maa ost ja maja ehitus", "kinnisvara välismaal", "ideelaen"], P),
 rate_basis=F("Margin + 3, 6 or 12 month Euribor", P),
 margin=F("individual", P, "Calculator footnote: bank margin on home loan 1.45% + 6M Euribor; worked example margin 1.45%."),
 promo_rates=F(["Black Friday: new loans from 1.30% + 3/6/12M Euribor and €0 contract fee, applications 30.10.2026–01.12.2026", "Education workers: 1.39% + Euribor, €0 fee", "Developer partner listings: lower fee, free valuation for many developments"], P),
 contract_fee=F("1% of loan amount, min €100", PL, "Price list valid from 01.10.2026. An older 2024 price list PDF is still online at a different URL."),
 valuation_fee=F(None, P, "Set by valuer."),
 amendment_fee=F("Contract amendment €200 (complex up to 0.2% of balance); payment-difficulty amendment €100; payment date change free once a year, then €20", PL),
 early_repayment_fee=F("Variable rate: free with at least 3 months' notice, otherwise up to 3 months' interest; fixed rate: formula", PL),
 min_loan_amount_eur=F(10000, P),
 min_down_payment_pct=F(15, LU, "From 15%; with EIS from 10% (large families from 5%); can be replaced by additional collateral."),
 max_ltv_pct=F(85, LU, "Luminor general info page: 'kuni 85% tagatise väärtusest'. No regional variation published; see regional_ltv_rules."),
 max_ltv_with_eis_pct=F(95, LU, "Luminor: 'EIS käendusel finantseerime kuni 90–95%, lisatagatisel kuni 100%'. 95% applies to the EIS large-family group; up to 100% only with additional collateral."),
 regional_ltv_rules=F({"outside_harju_and_tartu_county": {"max_ltv_pct": 80, "max_ltv_with_eis_pct": 90}, "harju_and_tartu_county": None},
   "Information from a former member of Luminor's housing loan team (not publicly published by Luminor), 2026-11-09",
   "Reported by founder Sander Seppik on 2026-11-09. Not found on Luminor pages (era/kodulaen, era/kodulaenu-uldinfo, era/laenud-kodu-voi-muu-kinnisvara-ostmiseks, price list), comparison sites (hüpoteek.ee, intressid.ee, referent.ee) or news checked 2026-11-09; those state 85% without regional split. No public source found for a separate Harju/Tartu figure, so that value is left null."),
 max_term_years=F(30, P),
 eis_participation=F(True, P),
 eis_programs=F(["young_family", "young_specialist", "large_family", "veteran", "energy_efficient"], P),
 eis_rural=F(False, EIS_RURAL),
 green_discount=F("Final rate may depend on the property's energy class (no figure)", P),
 young_buyer_offer=F(None, P, "None beyond EIS."),
 worked_example=dict(
   loan_amount_eur=F(145000, P), term_months=F(360, P), rate_type=F("variable", P), margin_pct=F(1.45, P), euribor_pct=F(2.970, P), euribor_date=F("2026-10-16", P),
   nominal_rate_pct=F(4.42, P), apr_pct=F(4.629, P), contract_fee_eur=F(1450, P), monthly_payment_eur=F(None, P),
   total_repayments_eur=F(262014.25, P), total_payable_eur=F(263932.25, P, "Includes €1.30/month package fee."), total_cost_of_credit_eur=F(None, P), example_date=F("2026-10-16", P, "Date of Euribor used.")),
 income_rules=F(None, P, "Not published."),
 dsti_max_pct=F(None, P),
 digital_application=F("Online application for clients and non-clients; also PDF by e-mail; contracts signed digitally", P),
 account_requirement=F("Current account at Luminor required (price list); package fee €1.30/month in example", PL),
))

# ---------- SEB ----------
P = "https://www.seb.ee/eraklient/laenud/kodulaen"
banks.append(dict(
 id="seb", bank_name="AS SEB Pank",
 product_url_et=F(P, P), product_url_en=F("https://www.seb.ee/en/private/loans/home-loan", P),
 loan_types=F(["kodulaen", "roheline kodulaen", "koduvahetuslaen", "hüpoteeklaen"], P),
 rate_basis=F("3, 6 or 12 month Euribor + client-specific margin; longer fixing possible", P),
 margin=F("individual", P, "Worked example margin 1.40%."),
 promo_rates=F(["A/B energy class purchase: from 1.35% + Euribor (applications 01.10–31.12.2026)", "Refinancing A/B home over €100k: SEB pays notary fees (2026)"], P),
 contract_fee=F("0.4% of loan amount, min €190", P),
 valuation_fee=F(None, P, "Set by valuer."),
 amendment_fee=F("Up to 0.4% of balance, min €190; payment date/account change and principal holiday free", P),
 early_repayment_fee=F("Variable rate: max 3 months' interest, none with 3 months' notice; fixed rate: compensation per contract", P, "From pre-contract information on page."),
 min_loan_amount_eur=F(15000, P),
 min_down_payment_pct=F(15, P, "Lower with EIS; additional collateral accepted."),
 max_ltv_pct=F(85, P, "Derived; 60% if the property is not the borrower's home."),
 max_ltv_with_eis_pct=F(None, P, "Not stated; EIS rule is 90%."),
 max_term_years=F(30, P),
 eis_participation=F(True, P),
 eis_programs=F(["young_specialist", "young_family", "energy_efficient", "large_family", "veteran"], P),
 eis_rural=F(False, EIS_RURAL, "Works with MES (Maaelu Edendamise Sihtasutus)."),
 green_discount=F("A/B energy class: from 1.35% + Euribor (to 31.12.2026); 'roheline kodulaen' product", P),
 young_buyer_offer=F(None, P, "None published beyond EIS."),
 worked_example=dict(
   loan_amount_eur=F(150000, P), term_months=F(312, P), rate_type=F("variable", P), margin_pct=F(1.40, P), euribor_pct=F(2.114, P), euribor_date=F(None, P, "Not stated."),
   nominal_rate_pct=F(3.514, P, "Computed: margin + Euribor."), apr_pct=F(3.66, P), contract_fee_eur=F(600, P), monthly_payment_eur=F(None, P),
   total_repayments_eur=F(230295.34, P), total_payable_eur=F(230988.94, P, "Includes €0.30/month account fee."), total_cost_of_credit_eur=F(None, P), example_date=F(None, P, "Undated; 2.114% Euribor suggests an older example.")),
 income_rules=F(None, P, "Max payment depends on income, obligations and family size; no figure."),
 dsti_max_pct=F(None, P),
 digital_application=F("Online application ('Esitan taotluse'); remote solutions and digital signing", P),
 account_requirement=F("SEB current account required; bank may require all income to be paid into SEB", P),
))

# ---------- Swedbank ----------
P = "https://www.swedbank.ee/private/credit/loans/home"
banks.append(dict(
 id="swedbank", bank_name="Swedbank AS",
 product_url_et=F(P, P), product_url_en=F("https://www.swedbank.ee/private/credit/loans/home?language=ENG", P),
 loan_types=F(["kodulaen", "kodukapitalilaen", "koduvahetus", "refinancing", "maja ehitus"], P),
 rate_basis=F("Individual margin + 6M Euribor (variable), or 5-year fixed (5-year EUR swap + margin)", P),
 margin=F("individual", P, "Worked example margin 1.5%."),
 promo_rates=F(["Refinancing balance over €100k: €0 contract fee and notary costs paid (applications to 31.12.2026)"], P),
 contract_fee=F("0.3% of loan amount, min €190 (construction min €400)", P, "Price list valid from 31.08.2026. Young and gold clients: -30%."),
 valuation_fee=F(None, P, "Independent valuer required; fee set by valuer."),
 amendment_fee=F("Contract amendment €190; principal payment holiday €95; payment date/account change free online; rate reduction 0.3% of balance, min €190", P),
 early_repayment_fee=F("Per contract terms (price list); the price list also shows '1 month's interest' next to early repayment via internet bank, which it says does not apply to fixed-rate loans", P, "Wording ambiguous; confirm in contract or pre-contract information."),
 min_loan_amount_eur=F(20000, P),
 min_down_payment_pct=F(15, P, "10% with EIS; 0% with additional property as collateral."),
 max_ltv_pct=F(85, P), max_ltv_with_eis_pct=F(90, P), max_term_years=F(30, P),
 eis_participation=F(True, P),
 eis_programs=F(["energy_efficient", "young_family", "large_family", "veteran", "young_specialist"], P),
 eis_rural=F(False, EIS_RURAL),
 green_discount=F(None, P, "No energy-class rate discount published (EIS energy-efficient guarantee only)."),
 young_buyer_offer=F("Young clients: contract fee -30% (age limit not stated on page)", P),
 worked_example=dict(
   loan_amount_eur=F(145000, P), term_months=F(360, P), rate_type=F("variable", P), margin_pct=F(1.5, P), euribor_pct=F(2.051, P), euribor_date=F("2025-07-09", P),
   nominal_rate_pct=F(3.551, P), apr_pct=F(3.671, P), contract_fee_eur=F(190, P), monthly_payment_eur=F(None, P),
   total_repayments_eur=F(237417.39, P), total_payable_eur=F(237607.39, P), total_cost_of_credit_eur=F(92607.39, P),
   example_date=F("2025-07-09", P, "Euribor date about 16 months old; current 6M Euribor is ~3.0%, so the example APR understates today's cost.")),
 income_rules=F("Proven net income at least €1,000/month alone; €1,300 for two borrowers; €1,500 alone with 2+ dependants; all loan payments up to 50% of income", P),
 dsti_max_pct=F(50, P),
 digital_application=F("Online application; automatic first offer even before choosing a home", P),
 account_requirement=F(None, P),
))

for b in banks:
    if "regional_ltv_rules" not in b:
        b["regional_ltv_rules"] = F(None, None, "No regional LTV rule published or reported.")
SHORT={"bigbank":"Bigbank","citadele":"Citadele","coop":"Coop Pank","holm":"Holm Bank","lhv":"LHV","luminor":"Luminor","seb":"SEB","swedbank":"Swedbank"}
nb=[]
for b in banks:
    legal=b.pop("bank_name"); i=b.pop("id")
    nb.append({"id":i,"bank_name":SHORT[i],"legal_name":legal,**b})
banks=nb
banks.sort(key=lambda b: b["bank_name"].lower())

meta = {
 "dataset": "Estonian bank housing-loan terms (published information)",
 "version": "0.1.0", "updated": "2026-11-10", "language_of_source_pages": "et",
 "ordering": "alphabetical by bank_name; ordering carries no meaning",
 "neutrality": "Published terms only. No ranking, scoring or recommendation. Not financial advice. Each bank decides on its own assessment.",
 "license": "CC BY 4.0 for this compilation (proposed; facts belong to the banks)",
 "field_format": "Each field is {value, unit?, note, source, checked}. value null = not published or not found on the cited page.",
}
json.dump({"meta": meta, "banks": banks}, open(ROOT / "data" / "banks.json", "w"), ensure_ascii=False, indent=2)

# CSV flatten
rows = []; cols = []
def add(row, key, f):
    v = f["value"]
    if isinstance(v, list) and any(isinstance(item, (dict, list)) for item in v):
        v = json.dumps(v, ensure_ascii=False)
    elif isinstance(v, list): v = " | ".join(map(str, v))
    if isinstance(v, bool): v = str(v).lower()
    if isinstance(v, dict): v = json.dumps(v, ensure_ascii=False)
    row[key] = "" if v is None else v
    row[key + "__note"] = f["note"] or ""
    row[key + "__source"] = f["source"] or ""
for b in banks:
    r = {"id": b["id"], "bank_name": b["bank_name"], "legal_name": b["legal_name"], "checked": D}
    for k, v in b.items():
        if k in ("id", "bank_name", "legal_name"): continue
        if k == "worked_example":
            for kk, ff in v.items(): add(r, "example_" + kk, ff)
        else: add(r, k, v)
    rows.append(r)
    for k in r:
        if k not in cols: cols.append(k)
with open(ROOT / "data" / "banks.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(len(banks), "banks;", len(cols), "csv columns")
