#!/usr/bin/env python3
"""Build the Kodulaen static site from data/*.json into dist/.

Content is rendered to HTML. JavaScript only reorders the comparison table.
Banks stay in alphabetical order in the HTML source.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIST = ROOT / "dist"
ET = json.loads((Path(__file__).parent / "translations.json").read_text(encoding="utf-8"))

BASE = os.environ.get("BASE_PATH", "/Kodulaen").rstrip("/")
ORIGIN = os.environ.get("SITE_ORIGIN", "https://hastitore.github.io").rstrip("/")
SITE = ORIGIN + BASE

PAGE_ROUTES = []
PAGE_MODIFIED = ""
STALE_DAYS = 14
STALE_PP = Decimal("0.01")
TENOR_ORDER = ["1M", "3M", "6M", "12M"]
INSIDER_EN = "industry insider information, not published by the bank"
INSIDER_ET = "tööstusharu siseteave, pank ei ole seda avaldanud"

MISSING: list[str] = []

REGION = {
    "outside_harju_and_tartu_county": {
        "et": "Väljaspool Harju ja Tartu maakonda",
        "en": "Outside Harju and Tartu county",
    },
    "harju_and_tartu_county": {
        "et": "Harju ja Tartu maakond",
        "en": "Harju and Tartu county",
    },
}

PROGRAM_ORDER = [
    "young_family",
    "young_specialist",
    "large_family",
    "energy_efficient",
    "veteran",
    "returned_dwelling_tenant",
    "rural",
]

BANK_FIELDS = [
    ("product_url_et", "url"),
    ("product_url_en", "url"),
    ("loan_types", "list"),
    ("rate_basis", "text"),
    ("margin", "text"),
    ("promo_rates", "list"),
    ("contract_fee", "text"),
    ("valuation_fee", "text"),
    ("amendment_fee", "text"),
    ("early_repayment_fee", "text"),
    ("min_loan_amount_eur", "money"),
    ("min_down_payment_pct", "pct"),
    ("max_ltv_pct", "pct"),
    ("max_ltv_with_eis_pct", "pct"),
    ("usual_max_ltv_pct", "pct"),
    ("regional_ltv_rules", "regional"),
    ("property_condition_ltv", "text"),
    ("construction_ltv_stages", "stages"),
    ("max_term_years", "years"),
    ("eis_participation", "bool"),
    ("eis_programs", "programs"),
    ("eis_rural", "bool"),
    ("green_discount", "text"),
    ("young_buyer_offer", "text"),
    ("income_rules", "text"),
    ("dsti_max_pct", "pct"),
    ("digital_application", "text"),
    ("account_requirement", "text"),
]

EXAMPLE_FIELDS = [
    ("loan_amount_eur", "money"),
    ("term_months", "months"),
    ("rate_type", "text"),
    ("margin_pct", "pct"),
    ("euribor_pct", "pct"),
    ("euribor_date", "date"),
    ("nominal_rate_pct", "pct"),
    ("apr_pct", "pct"),
    ("contract_fee_eur", "money"),
    ("monthly_payment_eur", "money"),
    ("total_repayments_eur", "money"),
    ("total_payable_eur", "money"),
    ("total_cost_of_credit_eur", "money"),
    ("example_date", "date"),
]

UI = {
    "skip": {"et": "Sisu juurde", "en": "Skip to content"},
    "tagline": {
        "et": "Kaheksa Eesti panga avaldatud kodulaenu tingimused. Tasuta, erapooletu, tähestikulises järjekorras.",
        "en": "Published housing-loan terms of eight Estonian banks. Free, neutral, and listed alphabetically.",
    },
    "nav_label": {"et": "Peamine", "en": "Primary"},
    "nav_home": {"et": "Ülevaade", "en": "Overview"},
    "nav_rules": {"et": "Eesti Pank ja EIS", "en": "Eesti Pank and EIS"},
    "nav_euribor": {"et": "Euribor", "en": "Euribor"},
    "nav_market": {"et": "Keskmine intress", "en": "Average rate"},
    "nav_about": {"et": "Meetod ja hoiatus", "en": "Method and disclaimer"},
    "nav_questions": {"et": "Küsimused", "en": "Questions"},
    "nav_compare": {"et": "Kõrvutus", "en": "Side by side"},
    "nav_changes": {"et": "Muudatused", "en": "What changed"},
    "page_updated": {"et": "Leht uuendatud", "en": "Page updated"},
    "lang_label": {"et": "Keel", "en": "Language"},
    "terms_checked": {"et": "Tingimused kontrollitud", "en": "Terms checked"},
    "euribor_fetched": {"et": "Euribor tõmmatud", "en": "Euribor fetched"},
    "disclaimer_title": {"et": "Ainult teave", "en": "Information only"},
    "disclaimer": {
        "et": "See ei ole finantsnõuanne, laenupakkumine ega krediidi vahendamine. Kodulaen ei saa pankadelt makseid ega hinda, kas laen kellelegi sobib. Iga väärtuse juures on allikas ja kontrolli kuupäev. Kui väärtust ei ole avaldatud, on kirjas „avaldamata“. Enne otsust kontrolli tingimused pangast.",
        "en": "This is not financial advice, a loan offer, or credit intermediation. Kodulaen receives no payments from banks and does not judge whether a loan suits anyone. Every value has a source and a check date. Where a value is not published, the page says “not published”. Check the terms with the bank before you decide.",
    },
    "footer_blurb": {
        "et": "Kodulaen on avaldatud tingimuste kogumik. Pangad on tähestikulises järjekorras. Järjekord ei ole hinnang.",
        "en": "Kodulaen is a compilation of published terms. Banks are in alphabetical order. The order is not a judgement.",
    },
    "footer_data": {"et": "Andmefailid", "en": "Data files"},
    "footer_banks": {"et": "Pangad", "en": "Banks"},
    "license_line": {
        "et": "Kogumikule on pakutud litsents CC BY 4.0. Faktid kuuluvad viidatud pankadele ja asutustele.",
        "en": "The compilation is proposed under CC BY 4.0. The underlying facts belong to the banks and public bodies cited.",
    },
    "home_h1": {
        "et": "Eesti pankade kodulaenu tingimused",
        "en": "Housing-loan terms of Estonian banks",
    },
    "home_lead": {
        "et": "Kodulaen koondab kaheksa eluasemelaenu väljastava panga avaldatud tingimused. Võrdlus on tasuta ja erapooletu. See leht on mõeldud nii lugejale kui ka keelemudelile, kes vastab küsimustele Eesti kodulaenu kohta.",
        "en": "Kodulaen brings together the published housing-loan terms of the eight banks that issue home loans in Estonia. The comparison is free and neutral. The pages are written for people and for language models answering questions about Estonian home loans.",
    },
    "home_read_title": {"et": "Kuidas tabelit lugeda", "en": "How to read the table"},
    "read_alpha": {
        "et": "Vaikimisi on pangad tähestikulises järjekorras. Järjestuse muutmine muudab ainult lugemise järjekorda.",
        "en": "Banks are alphabetical unless you change the order. Changing the order only changes the reading order.",
    },
    "read_cell": {
        "et": "Igas lahtris on avaldatud väärtus, link allikale ja kontrolli kuupäev. Pikem märkus on avatav. Kõik väljad on panga lehel.",
        "en": "Each cell has the published value, a link to the source, and the check date. A longer note can be opened. Every field is on the bank’s page.",
    },
    "read_null": {
        "et": "„Avaldamata“ tähendab, et pank ei ole väärtust avaldanud või seda ei leitud viidatud lehelt. See ei tähenda nulli.",
        "en": "“Not published” means the bank has not published the value, or it was not found on the cited page. It does not mean zero.",
    },
    "read_promo": {
        "et": "Tähtajalised kampaaniad on panga lehel väljal „Kampaaniad“. Neid ei tõsteta siin esile.",
        "en": "Time-limited promotions are on each bank page under “Promotions”. They are not highlighted here.",
    },
    "sort_key": {"et": "Järjestus", "en": "Order"},
    "sort_dir": {"et": "Suund", "en": "Direction"},
    "sort_help": {
        "et": "See ei ole edetabel. Tühjad väärtused jäävad lõppu.",
        "en": "This is not a ranking. Empty values stay last.",
    },
    "sort_bank": {"et": "Panga nimi", "en": "Bank name"},
    "sort_min_loan": {"et": "Minimaalne laenusumma", "en": "Minimum loan amount"},
    "sort_down": {"et": "Minimaalne omafinantseering", "en": "Minimum down payment"},
    "sort_ltv": {"et": "Maksimaalne LTV", "en": "Maximum LTV"},
    "sort_ltv_eis": {"et": "Maksimaalne LTV EIS-iga", "en": "Maximum LTV with EIS"},
    "sort_term": {"et": "Maksimaalne tähtaeg", "en": "Maximum term"},
    "sort_nominal": {"et": "Näite nominaalintress", "en": "Example nominal rate"},
    "sort_apr": {"et": "Näite krediidi kulukuse määr", "en": "Example APR"},
    "sort_euribor_date": {"et": "Näite Euribori kuupäev", "en": "Example Euribor date"},
    "dir_asc": {"et": "Kasvav (A–Z, väiksem ees)", "en": "Ascending (A–Z, smaller first)"},
    "dir_desc": {"et": "Kahanev (Z–A, suurem ees)", "en": "Descending (Z–A, larger first)"},
    "sort_status_label": {"et": "Praegune järjestus", "en": "Current order"},
    "noscript": {
        "et": "Ilma JavaScriptita jääb tabel tähestikulisse järjekorda.",
        "en": "Without JavaScript the table stays in alphabetical order.",
    },
    "scroll_hint": {
        "et": "Tabel on lai. Keri küljele. Panga nimi jääb paigale.",
        "en": "The table is wide. Scroll sideways. The bank name stays put.",
    },
    "caption_compare": {
        "et": "Kaheksa eluasemelaenu väljastava panga avaldatud tingimused. Järjekord on tähestikuline ega ole hinnang.",
        "en": "Published terms of the eight banks that issue housing loans. Alphabetical order is not a judgement.",
    },
    "col_bank": {"et": "Pank", "en": "Bank"},
    "col_rate": {"et": "Intressi alus", "en": "Rate basis"},
    "col_margin": {"et": "Marginaal", "en": "Margin"},
    "col_fee": {"et": "Lepingutasu", "en": "Contract fee"},
    "col_min_loan": {"et": "Min laen", "en": "Min loan"},
    "col_down": {"et": "Min omafinantseering", "en": "Min down payment"},
    "col_ltv": {"et": "Max LTV", "en": "Max LTV"},
    "col_ltv_eis": {"et": "Max LTV EIS-iga", "en": "Max LTV with EIS"},
    "col_regional": {"et": "Piirkondlik LTV", "en": "Regional LTV"},
    "col_term": {"et": "Max tähtaeg", "en": "Max term"},
    "col_nominal": {"et": "Näite nominaal", "en": "Example nominal"},
    "col_apr": {"et": "Näite KKM", "en": "Example APR"},
    "col_uniform": {"et": "Samamäärane kuumakse", "en": "Same-rate payment"},
    "col_example_euribor": {"et": "Näite Euribor", "en": "Example Euribor"},
    "col_eis": {"et": "EIS", "en": "EIS"},
    "not_published": {"et": "avaldamata", "en": "not published"},
    "yes": {"et": "jah", "en": "yes"},
    "no": {"et": "ei", "en": "no"},
    "source": {"et": "Allikas", "en": "Source"},
    "note": {"et": "Märkus", "en": "Note"},
    "checked": {"et": "Kontrollitud", "en": "Checked"},
    "value": {"et": "Väärtus", "en": "Value"},
    "no_source": {"et": "Allikat ei ole märgitud", "en": "No source recorded"},
    "insider": {"et": INSIDER_ET, "en": INSIDER_EN},
    "with_eis": {"et": "EIS-iga", "en": "with EIS"},
    "details": {"et": "Märkus", "en": "Note"},
    "machines_title": {"et": "Andmed masinatele", "en": "Data for machines"},
    "machines_lead": {
        "et": "Sama andmestik on staatiliste failidena. null tähendab avaldamata. Skeem on schema.json failis ja meetodi lehel.",
        "en": "The same dataset is available as static files. null means not published. The schema is in schema.json and on the method page.",
    },
    "euribor_home_title": {"et": "Tänane Euribor", "en": "Euribor today"},
    "attribution": {
        "et": "Allikas: euribor-rates.eu, mis avaldab EMMI Euribori 24-tunnise viitega. Haldaja: European Money Markets Institute (EMMI).",
        "en": "Source: euribor-rates.eu, which republishes EMMI Euribor with a 24-hour delay. Administrator: European Money Markets Institute (EMMI).",
    },
    "licensing": {
        "et": "Euribori taaskasutamise EMMI litsents on läbivaatamisel. See ei ole juriidiline nõuanne.",
        "en": "EMMI licensing for republishing Euribor is under review. This is not legal advice.",
    },
    "value_date_label": {"et": "Väärtuspäev", "en": "Value date"},
    "open_rules": {"et": "Eesti Panga piirangud ja EIS-i käendus", "en": "Eesti Pank limits and the EIS guarantee"},
    "open_euribor": {"et": "Euribori leht ja pankade näited", "en": "Euribor page and the banks’ examples"},
    "field_product_url_et": {"et": "Panga leht (eesti)", "en": "Bank page (Estonian)"},
    "field_product_url_en": {"et": "Panga leht (inglise)", "en": "Bank page (English)"},
    "field_loan_types": {"et": "Laenutooted", "en": "Loan products"},
    "field_rate_basis": {"et": "Intressi alus", "en": "Rate basis"},
    "field_margin": {"et": "Marginaal", "en": "Margin"},
    "field_promo_rates": {"et": "Kampaaniad", "en": "Promotions"},
    "field_contract_fee": {"et": "Lepingutasu", "en": "Contract fee"},
    "field_valuation_fee": {"et": "Hindamistasu", "en": "Valuation fee"},
    "field_amendment_fee": {"et": "Muutmistasu", "en": "Amendment fee"},
    "field_early_repayment_fee": {"et": "Ennetähtaegne tagastamine", "en": "Early repayment"},
    "field_min_loan_amount_eur": {"et": "Minimaalne laenusumma", "en": "Minimum loan amount"},
    "field_min_down_payment_pct": {"et": "Minimaalne omafinantseering", "en": "Minimum down payment"},
    "field_max_ltv_pct": {"et": "Maksimaalne LTV", "en": "Maximum LTV"},
    "field_max_ltv_with_eis_pct": {"et": "Maksimaalne LTV EIS-i käendusega", "en": "Maximum LTV with the EIS guarantee"},
    "field_regional_ltv_rules": {"et": "Piirkondlikud LTV reeglid", "en": "Regional LTV rules"},
    "field_usual_max_ltv_pct": {"et": "Tavaline maksimaalne LTV", "en": "Usual maximum LTV"},
    "field_property_condition_ltv": {"et": "Vara seisukord ja LTV", "en": "Property condition and LTV"},
    "field_construction_ltv_stages": {"et": "Ehituslaenu LTV etapid", "en": "Construction-loan LTV stages"},
    "stage_col": {"et": "Etapp", "en": "Stage"},
    "stage_detail": {"et": "Täpsustus", "en": "Detail"},
    "stage_land_plot": {"et": "Maatükk", "en": "Land plot"},
    "stage_building_closed": {"et": "Hoone kinni", "en": "Building closed"},
    "stage_building_95": {"et": "Hoone 95% valmis", "en": "Building 95% complete"},
    "usually_word": {"et": "tavaliselt", "en": "usually"},
    "field_max_term_years": {"et": "Maksimaalne tähtaeg", "en": "Maximum term"},
    "field_eis_participation": {"et": "EIS-i eluasemelaenu käendus", "en": "EIS housing-loan guarantee"},
    "field_eis_programs": {"et": "Panga nimetatud EIS-i sihtrühmad", "en": "EIS target groups named by the bank"},
    "field_eis_rural": {"et": "EIS-i maapiirkonna käendus", "en": "EIS rural guarantee"},
    "field_green_discount": {"et": "Energiaklassi tingimus", "en": "Energy-class terms"},
    "field_young_buyer_offer": {"et": "Noore laenuvõtja tingimus", "en": "Young-buyer terms"},
    "field_income_rules": {"et": "Sissetuleku tingimused", "en": "Income rules"},
    "field_dsti_max_pct": {"et": "Maksimaalne võlateeninduse määr (DSTI)", "en": "Maximum debt-service ratio (DSTI)"},
    "field_digital_application": {"et": "Digitaalne taotlus", "en": "Digital application"},
    "field_account_requirement": {"et": "Konto nõue", "en": "Account requirement"},
    "ex_loan_amount_eur": {"et": "Laenusumma", "en": "Loan amount"},
    "ex_term_months": {"et": "Tähtaeg", "en": "Term"},
    "ex_rate_type": {"et": "Intressi tüüp", "en": "Rate type"},
    "ex_margin_pct": {"et": "Marginaal", "en": "Margin"},
    "ex_euribor_pct": {"et": "Euribor näites", "en": "Euribor in the example"},
    "ex_euribor_date": {"et": "Euribori kuupäev", "en": "Euribor date"},
    "ex_nominal_rate_pct": {"et": "Nominaalintress", "en": "Nominal rate"},
    "ex_apr_pct": {"et": "Krediidi kulukuse määr (KKM)", "en": "Annual percentage rate (APR)"},
    "ex_contract_fee_eur": {"et": "Lepingutasu näites", "en": "Contract fee in the example"},
    "ex_monthly_payment_eur": {"et": "Kuumakse", "en": "Monthly payment"},
    "ex_total_repayments_eur": {"et": "Tagasimaksed kokku", "en": "Total repayments"},
    "ex_total_payable_eur": {"et": "Tasumisele kuuluv kokku", "en": "Total payable"},
    "ex_total_cost_of_credit_eur": {"et": "Krediidi kogukulu", "en": "Total cost of credit"},
    "ex_example_date": {"et": "Näite kuupäev", "en": "Example date"},
    "example_title": {"et": "Panga avaldatud tüüpnäide", "en": "Worked example published by the bank"},
    "example_intro": {
        "et": "Need arvud on panga avaldatud tüüpnäide. Kodulaen ei ole neid muutnud. Need ei ole Kodulaenu pakkumine ega hinnang.",
        "en": "These figures are the worked example the bank published. Kodulaen has not changed them. They are not an offer from Kodulaen and not a judgement.",
    },
    "euribor_note_title": {"et": "Näite Euribor ja tänane määr", "en": "The example Euribor and today’s fixing"},
    "illustration_title": {"et": "Kodulaenu samamäärane näide, mitte panga pakkumine", "en": "Kodulaen same-rate example, not the bank’s offer"},
    "stale": {"et": "Näite Euribor on varasem kui tänane määr", "en": "The example Euribor is older than today’s fixing"},
    "in_line": {"et": "Näite Euribor on tänase määraga kooskõlas", "en": "The example Euribor is in line with today’s fixing"},
    "below_curve": {
        "et": "Näites avaldatud Euribor on madalam kui kõik tänased tähtajad. Näide ei nimeta tähtaega, seepärast kuumakset ümber ei arvutata.",
        "en": "The Euribor published in the example is below every current tenor. The example does not name the tenor, so the monthly payment is not recalculated.",
    },
    "unknown_status": {
        "et": "Näite Euribori määra või kuupäeva ei saa tänase määraga võrrelda, sest pank ei ole seda avaldanud. Kuumakset ümber ei arvutata.",
        "en": "The example’s Euribor rate or date cannot be compared with today’s fixing because the bank has not published it. The monthly payment is not recalculated.",
    },
    "formula": {
        "et": "Valem on tavaline annuiteet: kuumakse = P × r × (1+r)^n / ((1+r)^n − 1), kus r on aasta nominaalintress / 12 ja n on kuude arv. Tulemus on ümardatud sendini (harilik ümardamine).",
        "en": "The formula is a standard annuity: payment = P × r × (1+r)^n / ((1+r)^n − 1), where r is the annual nominal rate / 12 and n is the number of months. The result is rounded to the cent (half up).",
    },
    "formula_excludes": {
        "et": "Arvutus ei sisalda lepingutasu, kontohooldust ega muid tasusid. See ei ole panga maksegraafik. Sama valem panga enda avaldatud kuumaksega ei pruugi kokku langeda.",
        "en": "The calculation excludes the contract fee, account fees, and other charges. It is not the bank’s repayment schedule. The same formula may not reproduce a monthly payment the bank published.",
    },
    "basis_example": {"et": "Näite Euribor + näite marginaal", "en": "Example Euribor + example margin"},
    "basis_today": {"et": "Tänane Euribor + näite marginaal", "en": "Today’s Euribor + example margin"},
    "basis_published_payment": {"et": "Panga avaldatud kuumakse", "en": "Monthly payment published by the bank"},
    "who_formula_example": {
        "et": "Kodulaenu valem. Intress on andmestikus panga näite juures.",
        "en": "Kodulaen formula. The rate is the one recorded for the bank’s example.",
    },
    "who_illustration": {
        "et": "Kodulaenu illustratsioon. Mitte panga pakkumine.",
        "en": "Kodulaen illustration. Not the bank’s offer.",
    },
    "who_bank": {"et": "Panga avaldatud arv.", "en": "Figure published by the bank."},
    "nominal_computed": {
        "et": "Andmestik on selle nominaalintressi arvutanud marginaali ja näite Euribori summana. Pank summat eraldi ei avalda.",
        "en": "The dataset computed this nominal rate as margin plus the example Euribor. The bank does not state the sum.",
    },
    "col_basis": {"et": "Alus", "en": "Basis"},
    "col_who": {"et": "Kes arvutas", "en": "Who calculated it"},
    "crumb_label": {"et": "Asukoht", "en": "Location"},
    "rules_h1": {"et": "Eesti Panga reeglid ja EIS-i käendus", "en": "Eesti Pank rules and the EIS guarantee"},
    "rules_lead": {
        "et": "Siin on Eesti Panga eluasemelaenu piirangud ja Ettevõtluse ja Innovatsiooni Sihtasutuse (EIS) käenduse tingimused, sealhulgas esmakordsete ostjate ja noorte perede jaoks. Need on avalikud reeglid, mitte hinnang, kas inimene laenu saab.",
        "en": "This page sets out Eesti Pank’s housing-loan limits and the guarantee terms of the Estonian Business and Innovation Agency (EIS), including points that matter for first-time buyers and young families. These are public rules, not a judgement of whether a person can borrow.",
    },
    "rules_buyer_title": {"et": "Esmakordsed ostjad ja noored pered", "en": "First-time buyers and young families"},
    "rules_buyer": {
        "et": "Eesti Panga piirangud kehtivad pankadele. Need ei ole lubadus, et laenuvõtja saab laenu kuni piirini. EIS-i eluasemelaenu käenduse tingimustel on minimaalne omafinantseering 10% ja lasterikkal perel 5%. Käendust taotletakse panga kaudu. EISile eraldi avaldust ei saadeta. Kodulaen ei otsusta, kas inimene sihtrühma kuulub.",
        "en": "Eesti Pank’s limits apply to banks. They are not a promise that a borrower can borrow up to the limit. Under the EIS housing-loan guarantee the minimum down payment is 10%, and 5% for a large family. The guarantee is requested through the bank. There is no separate application to EIS. Kodulaen does not decide whether a person belongs to a target group.",
    },
    "ep_title": {"et": "Eesti Panga eluasemelaenu piirangud", "en": "Eesti Pank housing-loan limits"},
    "ep_ltv": {"et": "Maksimaalne LTV", "en": "Maximum LTV"},
    "ep_ltv_guarantee": {"et": "Maksimaalne LTV riigi käendusega", "en": "Maximum LTV with a state guarantee"},
    "ep_dsti": {"et": "Maksimaalne võlateeninduse määr", "en": "Maximum debt-service ratio"},
    "ep_stress": {"et": "Stressimäär ujuva intressi korral", "en": "Stress rate for variable-rate loans"},
    "ep_term": {"et": "Maksimaalne tähtaeg", "en": "Maximum term"},
    "ep_exception": {"et": "Erand", "en": "Exception"},
    "ep_since": {"et": "Kehtib alates", "en": "In force since"},
    "eis_title": {"et": "EIS-i eluasemelaenu käendus", "en": "EIS housing-loan guarantee"},
    "eis_apply": {"et": "Kuidas taotleda", "en": "How to apply"},
    "eis_banks": {"et": "EIS-i nimetatud väljastavad pangad", "en": "Issuing banks named by EIS"},
    "eis_down": {"et": "Minimaalne omafinantseering", "en": "Minimum down payment"},
    "eis_down_large": {"et": "Minimaalne omafinantseering lasterikkal perel", "en": "Minimum down payment for a large family"},
    "eis_size": {"et": "Käenduse suurus", "en": "Guarantee size"},
    "eis_cap": {"et": "Laenusumma ülempiir", "en": "Loan amount cap"},
    "eis_fee": {"et": "Tasu", "en": "Fee"},
    "eis_over30": {"et": "Tingimused, kui tähtaeg on üle 30 aasta", "en": "Conditions if the term exceeds 30 years"},
    "eis_no_home": {"et": "Teise eluaseme reegel", "en": "Rule on another home"},
    "eis_holiday": {"et": "Maksepuhkus", "en": "Payment holiday"},
    "eis_groups_title": {"et": "EIS-i sihtrühmad", "en": "EIS target groups"},
    "group_young_family": {"et": "Noor pere", "en": "Young family"},
    "group_young_specialist": {"et": "Noor spetsialist", "en": "Young specialist"},
    "group_large_family": {"et": "Lasterikas pere", "en": "Large family"},
    "group_energy_efficient": {"et": "Energiatõhus", "en": "Energy-efficient"},
    "group_veteran": {"et": "Veteran", "en": "Veteran"},
    "group_returned_dwelling_tenant": {"et": "Tagastatud eluruumi üürnik", "en": "Tenant of a returned dwelling"},
    "group_rural": {"et": "Maapiirkond", "en": "Rural"},
    "named_title": {"et": "Millised sihtrühmad pank oma lehel nimetab", "en": "Which target groups the bank names on its own page"},
    "named_note": {
        "et": "„Nimetab“ tähendab, et kood on panga lehel loetletud. „Ei nimeta“ tähendab, et pank loetleb sihtrühmi, aga seda koodi seal ei ole. „Ei loetle“ tähendab, et pank ei kirjuta sihtrühmi lahti. See ei tähenda, et käendust ei pakuta. EIS loetleb kõik kaheksa panka väljastajate hulgas.",
        "en": "“Names” means the code is listed on the bank’s page. “Does not name” means the bank lists target groups but not this code. “Does not itemise” means the bank does not set the groups out. It does not mean the guarantee is unavailable. EIS lists all eight banks as issuers.",
    },
    "names": {"et": "nimetab", "en": "names"},
    "does_not_name": {"et": "ei nimeta", "en": "does not name"},
    "does_not_itemise": {"et": "ei loetle", "en": "does not itemise"},
    "rural_title": {"et": "EIS-i maapiirkonna eluasemelaenu käendus", "en": "EIS rural housing-loan guarantee"},
    "rural_banks": {"et": "Pangad EIS-i lehel", "en": "Banks on the EIS page"},
    "rural_down": {"et": "Minimaalne omafinantseering", "en": "Minimum down payment"},
    "rural_guarantee": {"et": "Käendus", "en": "Guarantee"},
    "rural_cap": {"et": "Laenu ülempiir", "en": "Loan cap"},
    "rural_fee": {"et": "Tasu", "en": "Fee"},
    "stats_title": {"et": "Uute eluasemelaenude keskmine Eestis", "en": "Average new housing loans in Estonia"},
    "stats_note": {
        "et": "Need on Eesti Panga koostatud keskmised. Keskmine ei ole pankade võrdluse siht ega hinnang.",
        "en": "These are averages compiled by Eesti Pank. The average is not a target for comparing banks and not a judgement.",
    },
    "stats_avg": {"et": "Keskmine intress, uus äri (kõik fikseerimisperioodid)", "en": "Average rate, new business (all fixation periods)"},
    "stats_var": {"et": "Keskmine intress, ujuv kuni 1 aasta", "en": "Average rate, variable up to 1 year"},
    "stats_vol": {"et": "Uute laenude maht, mln € (ilma refinantseerimiseta)", "en": "Volume of pure new loans, € million (excludes renegotiations)"},
    "stats_next": {"et": "Järgmine avaldamine", "en": "Next release"},
    "month": {"et": "Kuu", "en": "Month"},
    "euribor_h1": {"et": "Euribor", "en": "Euribor"},
    "euribor_lead": {
        "et": "Kodulaenu leht näitab 1, 3, 6 ja 12 kuu Euriborit allikast euribor-rates.eu. Enamik Eesti kodulaene kasutab panga avaldatud tingimuste järgi individuaalset marginaali pluss 6 kuu Euriborit. Marginaal on individuaalne.",
        "en": "Kodulaen shows 1-month, 3-month, 6-month and 12-month Euribor from euribor-rates.eu. On the banks’ published terms, most Estonian housing loans use an individual margin plus 6-month Euribor. The margin is individual.",
    },
    "current_title": {"et": "Viimati tõmmatud määrad", "en": "Latest fetched fixings"},
    "tenor": {"et": "Tähtaeg", "en": "Tenor"},
    "rate": {"et": "Määr", "en": "Rate"},
    "compare_title": {"et": "Pankade tüüpnäidete Euribor", "en": "Euribor in the banks’ worked examples"},
    "compare_note": {
        "et": "Näide on vana, kui sama tähtaja määr erineb tänasest rohkem kui 0,01 protsendipunkti või näite kuupäev on tänasest väärtuspäevast rohkem kui 14 päeva varasem. Kui tähtaega ei ole nimetatud, kuumakset ümber ei arvutata.",
        "en": "An example is treated as older when the rate for the same tenor differs from today’s fixing by more than 0.01 percentage points, or the example date is more than 14 days before today’s value date. If the tenor is not named, the monthly payment is not recalculated.",
    },
    "col_example_rate": {"et": "Näite Euribor", "en": "Example Euribor"},
    "col_example_date": {"et": "Näite kuupäev", "en": "Example date"},
    "col_tenor": {"et": "Tähtaeg näites", "en": "Tenor in the example"},
    "col_today": {"et": "Tänane sama tähtaeg", "en": "Today’s same tenor"},
    "col_status": {"et": "Võrdlus", "en": "Comparison"},
    "tenor_unnamed": {"et": "nimetamata", "en": "not named"},
    "history_title": {"et": "6 kuu Euribori kontrollitud lõik", "en": "Checked slice of 6-month Euribor"},
    "history_note": {
        "et": "See lõik on allikate failist. Tööpäevane tõmbaja seda automaatselt ei uuenda. Tänased neli tähtaega tulevad failist euribor.json.",
        "en": "This slice comes from the sources file and is not updated by the weekday fetcher. The four current tenors come from euribor.json.",
    },
    "col_field": {"et": "Väli", "en": "Field"},
    "cross_title": {"et": "Ristkontroll", "en": "Cross-check"},
    "about_h1": {"et": "Meetod, erapooletus ja hoiatus", "en": "Method, neutrality, and disclaimer"},
    "about_lead": {
        "et": "Kodulaen on avatud kogumik pankade avaldatud eluasemelaenu tingimustest. Leht ei vahenda krediiti ega anna nõu.",
        "en": "Kodulaen is an open compilation of housing-loan terms that banks have published. The site does not intermediate credit and does not give advice.",
    },
    "faq_title": {"et": "Küsimused", "en": "Questions"},
    "not_found_h1": {"et": "Lehte ei ole", "en": "Page not found"},
    "not_found": {
        "et": "Seda aadressi ei ole. Ülevaade on avalehel.",
        "en": "This address does not exist. The overview is on the home page.",
    },
    "loan_ld_desc": {
        "et": "{legal} avaldatud kodulaenu tingimused Kodulaenu kogumikus. See ei ole pakkumine ega soovitus. Kontrollitud {updated}.",
        "en": "Published housing-loan terms of {legal}, compiled by Kodulaen. Not an offer and not a recommendation. Checked {updated}.",
    },
    "apr_ld_desc": {
        "et": "Krediidi kulukuse määr panga avaldatud tüüpnäites. See ei ole isiklik pakkumine ega järjestuse alus.",
        "en": "APR from the worked example published by the bank. Not a personal offer and not a basis for ranking.",
    },
    "dataset_desc": {
        "et": "Eesti pankade avaldatud eluasemelaenu tingimused. null tähendab avaldamata. Pangad on tähestikulises järjekorras. Kogumikule on pakutud CC BY 4.0; faktid kuuluvad viidatud allikatele.",
        "en": "Published housing-loan terms of Estonian banks. null means not published. Banks are alphabetical. CC BY 4.0 is proposed for the compilation; the facts belong to the cited sources.",
    },
    "status_stale_short": {"et": "varasem Euribor", "en": "older Euribor"},
    "status_current_short": {"et": "tänasega kooskõlas", "en": "in line with today"},
    "status_below_short": {"et": "madalam kui tänased tähtajad", "en": "below today’s tenors"},
    "status_unknown_short": {"et": "võrrelda ei saa", "en": "cannot compare"},
    "version_label": {"et": "Andmestiku versioon", "en": "Dataset version"},
    "see_page": {"et": "Panga leht", "en": "Bank page"},
    "region_ltv": {"et": "Max LTV", "en": "Max LTV"},
    "region_ltv_eis": {"et": "Max LTV EIS-iga", "en": "Max LTV with EIS"},
    "caption_facts": {
        "et": "{bank} avaldatud kodulaenu tingimused",
        "en": "Published housing-loan terms of {bank}",
    },
    "caption_example": {
        "et": "{bank} avaldatud tüüpnäide",
        "en": "Worked example published by {bank}",
    },
    "caption_illus": {
        "et": "Kodulaenu annuiteedi illustratsioon. See ei ole panga maksegraafik ega pakkumine.",
        "en": "Kodulaen annuity illustration. This is not the bank’s schedule or offer.",
    },
    "market_h1": {
        "et": "Keskmine kodulaenu intress Eestis",
        "en": "Average housing-loan interest rate in Estonia",
    },
    "market_lead": {
        "et": "{month} oli Eesti Panga andmetel uute eluasemelaenude keskmine intress {latest}. Aasta varem samal kuul oli see {prior}. Keskmine hõlmab kõiki fikseerimisperioode ega ole ühegi panga marginaal ega pakkumine.",
        "en": "In {month}, Eesti Pank data put the average interest rate on new housing loans at {latest}. A year earlier it was {prior}. The average covers all fixation periods and is not any bank’s margin or offer.",
    },
    "market_desc": {
        "et": "Eesti Panga andmed: uute eluasemelaenude keskmine intress oli {latest} ({month}), aasta varem {prior}. Kuuandmed, marginaali ja Euribori vahe ning kulu 100 000 € laenul.",
        "en": "Eesti Pank data: the average rate on new housing loans was {latest} in {month}, against {prior} a year earlier. Monthly figures, the margin–Euribor gap, and the cost on a €100,000 loan.",
    },
    "market_trend_title": {"et": "Keskmine intress kuude kaupa", "en": "Average rate by month"},
    "market_trend_note": {
        "et": "Read on uus äri: uued ja refinantseeritud laenud kokku. „Ujuv kuni 1 aasta“ tähendab, et intress on fikseeritud kuni aastaks. Keskmine ei ole pankade võrdluse siht.",
        "en": "The rows are new business: new and renegotiated loans together. “Variable up to 1 year” means the rate is fixed for up to a year. The average is not a target for comparing banks.",
    },
    "market_col_avg": {"et": "Keskmine intress", "en": "Average rate"},
    "market_col_var": {"et": "Ujuv kuni 1 aasta", "en": "Variable up to 1 year"},
    "market_volume_note": {
        "et": "Uute laenude maht ilma refinantseerimiseta: {jul} mln € juulis, {aug} mln € augustis ja {sep} mln € septembris.",
        "en": "Pure new lending, excluding renegotiations: €{jul}m in July, €{aug}m in August and €{sep}m in September.",
    },
    "market_margin_title": {"et": "Marginaal ja Euribor", "en": "Margin and Euribor"},
    "market_margin_note": {
        "et": "Pangad avaldavad kodulaenu intressi kujul „individuaalne marginaal + 6 kuu Euribor“. 6 kuu Euribor oli {date} seisuga {euribor}. Kui lahutada see {latest} keskmisest, jääb {diff} protsendipunkti.",
        "en": "Banks publish the housing-loan rate as “an individual margin plus 6-month Euribor”. On {date} the 6-month Euribor was {euribor}. Subtracting it from the {latest} average leaves {diff} percentage points.",
    },
    "market_margin_caveat": {
        "et": "See vahe on aritmeetika, mitte avaldatud marginaal. Keskmine sisaldab ka fikseeritud intressiga laene ja eri Euribori tähtaegu, seega tegelik keskmine marginaal erineb. Pankade avaldatud marginaalid on individuaalsed.",
        "en": "That difference is arithmetic, not a published margin. The average also includes fixed-rate loans and different Euribor tenors, so the real average margin differs. The margins banks publish are individual.",
    },
    "market_tenth_title": {"et": "Mida 0,1 protsendipunkt maksab", "en": "What 0.1 percentage point costs"},
    "market_tenth_text": {
        "et": "100 000 € laenul 25 aastaks (300 kuud, annuiteet) maksab 0,1 protsendipunkti intressi {monthly} kuus ja {total} kogu tähtaja jooksul. Arvutus kasutab Kodulaenu annuiteedivalemit ega sisalda tasusid.",
        "en": "On a €100,000 loan for 25 years (300 months, annuity), 0.1 percentage point of interest costs {monthly} a month and {total} over the full term. The calculation uses Kodulaen’s annuity formula and excludes fees.",
    },
    "market_cost_title": {"et": "Kogukulu 100 000 € laenul", "en": "Total cost on a €100,000 loan"},
    "market_cost_note": {
        "et": "Sama summa ja tähtaeg, igakuine annuiteetmakse. Intressimäärad on valitud näitlikult ümber septembri keskmise. Arvutus ei sisalda lepingutasu, kindlustust ega muid tasusid; panga maksegraafik võib erineda.",
        "en": "Same amount and term, monthly annuity payment. The rates are illustrative, chosen around the September average. The calculation excludes the contract fee, insurance and other charges; the bank’s schedule may differ.",
    },
    "market_col_rate": {"et": "Intress", "en": "Rate"},
    "market_col_payment": {"et": "Kuumakse", "en": "Monthly payment"},
    "market_col_total": {"et": "Kokku tagasi maksta", "en": "Total repaid"},
    "market_col_extra": {"et": "Vahe madalaimaga", "en": "Difference from lowest"},
    "market_cost_caveat": {
        "et": "Tabel on arvutus, mitte panga pakkumine. Tegeliku intressi määrab pank igale kliendile eraldi.",
        "en": "The table is a calculation, not a bank offer. The actual rate is set by the bank for each borrower.",
    },
    "market_why_title": {"et": "Miks siin ei ole „head marginaali“", "en": "Why there is no “good margin” here"},
    "market_why_text": {
        "et": "Pangad ei avalda, millise marginaali nad kliendile andsid. Avalikku allikat selle kohta ei ole, seega Kodulaen ei ütle, mis marginaal on hea või halb. Keskmine intress on ainus avalik võrdlusalus, aga ka see ei ütle, kas konkreetne pakkumine on Sinu jaoks mõistlik.",
        "en": "Banks do not publish the margin they gave a borrower. No public source exists for it, so Kodulaen does not say what margin is good or bad. The average rate is the only public reference point, and even it does not tell you whether a particular offer is reasonable for you.",
    },
    "market_source_title": {"et": "Allikas ja värskus", "en": "Source and freshness"},
    "market_source_text": {
        "et": "Read on Eesti Panga koostatud rahaloomeasutuste intressistatistikast, mille avaldab Euroopa Keskpanga andmeportaal. Seeria {series}. Kontrollitud {checked}.",
        "en": "The rows come from the MFI interest-rate statistics compiled by Eesti Pank and published through the European Central Bank data portal. Series {series}. Checked {checked}.",
    },
    "market_link_from_rules": {
        "et": "Keskmine intress ja kulu 100 000 € laenul",
        "en": "Average rate and the cost on a €100,000 loan",
    },
    "market_also_title": {"et": "Vaata ka", "en": "See also"},
    "market_link_from_euribor": {
        "et": "Keskmine kodulaenu intress Eestis",
        "en": "Average housing-loan rate in Estonia",
    },
    "market_faq_q1": {
        "et": "Kui suur on keskmine kodulaenu intress Eestis?",
        "en": "What is the average housing-loan interest rate in Estonia?",
    },
    "market_faq_a1": {
        "et": "{month} oli uute eluasemelaenude keskmine intress Eesti Panga andmetel {latest}. Aasta varem oli see {prior}.",
        "en": "In {month}, the average interest rate on new housing loans was {latest} according to Eesti Pank. A year earlier it was {prior}.",
    },
    "market_faq_q2": {
        "et": "Kas keskmine intress on panga marginaal?",
        "en": "Is the average rate a bank’s margin?",
    },
    "market_faq_a2": {
        "et": "Ei. Keskmine sisaldab kõiki fikseerimisperioode ja ka refinantseeritud laene. Panga marginaal on individuaalne ega ole avalik.",
        "en": "No. The average covers all fixation periods and renegotiated loans too. A bank’s margin is individual and not public.",
    },
}


def T(lang: str, key: str) -> str:
    try:
        return UI[key][lang]
    except KeyError as error:
        raise SystemExit(f"Missing UI string {key} for {lang}") from error


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def tr(text, lang: str) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    if lang == "en":
        return text
    found = ET.get(text)
    if found is None:
        MISSING.append(text)
        return text
    return found


def url_for(lang: str, rel: str = "") -> str:
    parts = []
    if BASE:
        parts.append(BASE.strip("/"))
    if lang == "en":
        parts.append("en")
    if rel:
        parts.append(rel.strip("/"))
    if not parts:
        return "/"
    return "/" + "/".join(parts) + "/"


def absolute(path: str) -> str:
    if path.startswith("http"):
        return path
    return ORIGIN + path


def asset(name: str) -> str:
    prefix = BASE if BASE else ""
    return f"{prefix}/assets/{name}"


def data_url(name: str) -> str:
    prefix = BASE if BASE else ""
    return f"{prefix}/data/{name}"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fmt_pct(number, lang: str) -> str:
    dec = number if isinstance(number, Decimal) else Decimal(str(number))
    text = f"{dec:.4f}".rstrip("0").rstrip(".")
    if lang == "et":
        text = text.replace(".", ",")
    return text + "%"


def fmt_money(number, lang: str) -> str:
    dec = number if isinstance(number, Decimal) else Decimal(str(number))
    if dec == dec.to_integral_value():
        whole = int(dec)
        if lang == "et":
            return f"{whole:,}".replace(",", "\u00a0") + "\u00a0€"
        return f"€{whole:,}"
    quantized = dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if lang == "et":
        text = f"{quantized:,.2f}".replace(",", "\u00a0").replace(".", ",")
        return text + "\u00a0€"
    return f"€{quantized:,.2f}"


def fmt_months(number, lang: str) -> str:
    months = int(number)
    years, rest = divmod(months, 12)
    if lang == "et":
        base = f"{months} kuud"
        extra = f"{years} aastat" if rest == 0 else f"{years} aastat ja {rest} kuud"
    else:
        base = f"{months} months"
        extra = f"{years} years" if rest == 0 else f"{years} years and {rest} months"
    return f"{base} ({extra})"


def fmt_years(number, lang: str) -> str:
    if lang == "et":
        return f"{int(number)} aastat"
    return f"{int(number)} years"


ET_MONTHS = ["jaanuar", "veebruar", "märts", "aprill", "mai", "juuni",
             "juuli", "august", "september", "oktoober", "november", "detsember"]
ET_MONTHS_IN = ["jaanuaris", "veebruaris", "märtsis", "aprillis", "mais", "juunis",
                "juulis", "augustis", "septembris", "oktoobris", "novembris", "detsembris"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]


def month_label(month: str, lang: str) -> str:
    """'2026-09' -> '2026. aasta septembris' (et) / 'September 2026' (en)."""
    year, number = month.split("-")
    index = int(number) - 1
    if lang == "et":
        return f"{year}. aasta {ET_MONTHS_IN[index]}"
    return f"{EN_MONTHS[index]} {year}"


def month_short(month: str, lang: str) -> str:
    """'2026-09' -> 'sept 2026' (et) / 'Sep 2026' (en)."""
    year, number = month.split("-")
    index = int(number) - 1
    name = ET_MONTHS[index] if lang == "et" else EN_MONTHS[index][:3]
    return f"{name} {year}"


def annuity(principal, annual_pct, months) -> Decimal:
    principal_d = Decimal(str(principal))
    annual = Decimal(str(annual_pct))
    count = int(months)
    monthly = annual / Decimal(100) / Decimal(12)
    if monthly == 0:
        payment = principal_d / Decimal(count)
    else:
        factor = (1 + monthly) ** count
        payment = principal_d * monthly * factor / (factor - 1)
    return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def tenors_in(text: str) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    found: list[str] = []

    def add(code: str) -> None:
        if code not in found and code in TENOR_ORDER:
            found.append(code)

    for match in re.finditer(r"\b(12|6|3|1)\s*m\b", lowered):
        add(match.group(1) + "M")
    for match in re.finditer(r"\b(12|6|3|1)\s*-?\s*(?:month|kuu)", lowered):
        add(match.group(1) + "M")
    listed = re.search(
        r"\b((?:\d{1,2}\s*,\s*)+\d{1,2})\s*(?:or|või)\s*(\d{1,2})\s*(?:month|kuu)",
        lowered,
    )
    if listed:
        for number in re.findall(r"\d{1,2}", listed.group(0)):
            add(number + "M")
    return found


def tenor_of(bank: dict) -> str | None:
    example = bank["worked_example"]
    bits = [bank["margin"].get("note") or ""]
    for key in ("rate_type", "margin_pct", "euribor_pct", "euribor_date", "nominal_rate_pct"):
        field = example[key]
        if isinstance(field.get("value"), str):
            bits.append(field["value"])
        bits.append(field.get("note") or "")
    found = tenors_in(" ".join(bits))
    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        return None
    basis = f"{bank['rate_basis'].get('value') or ''} {bank['rate_basis'].get('note') or ''}"
    found = tenors_in(basis)
    if len(found) == 1:
        return found[0]
    return None


def number_or_none(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def assess(bank: dict, euribor: dict) -> dict:
    tenor = tenor_of(bank)
    example = bank["worked_example"]
    margin = number_or_none(example["margin_pct"]["value"])
    example_rate = number_or_none(example["euribor_pct"]["value"])
    example_date = example["euribor_date"]["value"] if isinstance(example["euribor_date"]["value"], str) else None
    nominal = number_or_none(example["nominal_rate_pct"]["value"])
    current = euribor["rates"].get(tenor) if tenor else None
    status = "unknown"
    if current and example_rate is not None:
        rate_gap = abs(Decimal(str(example_rate)) - Decimal(str(current["rate_pct"])))
        date_stale = True
        if example_date:
            from datetime import date

            date_stale = (date.fromisoformat(current["value_date"]) - date.fromisoformat(example_date)).days > STALE_DAYS
        status = "stale" if rate_gap > STALE_PP or date_stale else "current"
    elif example_rate is not None and tenor is None:
        current_rates = [Decimal(str(euribor["rates"][code]["rate_pct"])) for code in TENOR_ORDER]
        if Decimal(str(example_rate)) < min(current_rates) - STALE_PP:
            status = "below_curve"
    result = {
        "tenor": tenor,
        "margin": margin,
        "example_euribor": example_rate,
        "example_date": example_date,
        "status": status,
        "illustrate": False,
        "current_rate": current["rate_pct"] if current else None,
        "current_date": current["value_date"] if current else None,
        "nominal_today": None,
        "pay_today": None,
        "pay_at_example": None,
        "example_nominal": nominal,
        "example_nominal_computed": "computed" in (example["nominal_rate_pct"].get("note") or "").lower(),
        "published_payment": number_or_none(example["monthly_payment_eur"]["value"]),
        "amount": number_or_none(example["loan_amount_eur"]["value"]),
        "months": number_or_none(example["term_months"]["value"]),
    }
    if status == "stale" and margin is not None and current and result["amount"] is not None and result["months"]:
        nominal_today = Decimal(str(margin)) + Decimal(str(current["rate_pct"]))
        result["illustrate"] = True
        result["nominal_today"] = nominal_today
        result["pay_today"] = annuity(result["amount"], nominal_today, result["months"])
        if nominal is not None:
            result["pay_at_example"] = annuity(result["amount"], nominal, result["months"])
    return result


ILLUSTRATIVE = None
ILLUSTRATIVE_MARGIN = Decimal("2.0")
ILLUSTRATIVE_AMOUNT = 100000
ILLUSTRATIVE_MONTHS = 360


def dmy(iso_date: str) -> str:
    year, month, day = iso_date.split("-")
    return f"{day}.{month}.{year}"


def build_illustrative_example() -> dict:
    fixing = EURIBOR["rates"]["6M"]
    euribor = Decimal(str(fixing["rate_pct"]))
    nominal = (ILLUSTRATIVE_MARGIN + euribor).quantize(Decimal("0.001"))
    payment = annuity(ILLUSTRATIVE_AMOUNT, nominal, ILLUSTRATIVE_MONTHS)
    return {
        "label": "Kodulaen illustrative same-rate example, not a bank offer",
        "uniform": True,
        "margin_pct": 2.0,
        "margin_assumption": "Assumed 2.0% margin so every bank is shown on equal terms. Real margins are set individually by the bank. This is not a bank offer.",
        "euribor_tenor": "6M",
        "euribor_pct": float(euribor),
        "euribor_value_date": fixing["value_date"],
        "euribor_source_url": fixing["source_url"],
        "nominal_rate_pct": float(nominal),
        "loan_amount_eur": ILLUSTRATIVE_AMOUNT,
        "term_months": ILLUSTRATIVE_MONTHS,
        "repayment_type": "annuity",
        "monthly_payment_eur": float(payment),
        "fees_included": False,
        "fee_note": "The monthly payment excludes fees. The bank's published contract fee is stored separately and may differ.",
    }


def attach_illustrative_examples() -> None:
    global ILLUSTRATIVE
    ILLUSTRATIVE = build_illustrative_example()
    for bank in BANKS:
        fee = bank["contract_fee"]
        bank["illustrative_example"] = {
            **ILLUSTRATIVE,
            "bank_published_contract_fee": {
                "value": fee.get("value"),
                "note": fee.get("note"),
                "source": fee.get("source"),
                "checked": fee.get("checked"),
            },
        }


def uniform_rate_label(lang: str) -> str:
    example = ILLUSTRATIVE
    euribor = fmt_pct(example["euribor_pct"], lang)
    nominal = fmt_pct(example["nominal_rate_pct"], lang)
    if lang == "et":
        margin = "2,0%"
        return f"{margin} + 6 kuu Euribor ({euribor} seisuga {dmy(example['euribor_value_date'])}) = {nominal}"
    return f"2.0% + 6-month Euribor ({euribor} on {example['euribor_value_date']}) = {nominal}"


def uniform_assumption_note(lang: str) -> str:
    if lang == "et":
        return "Marginaal 2,0% on oletatud illustratsioon, et panku saaks võrrelda samadel tingimustel. Tegeliku marginaali määrab pank igale kliendile eraldi."
    return "The 2.0% margin is an assumed illustration so the banks can be compared on equal terms. The real margin is set individually by the bank."


def is_url(value) -> bool:
    return isinstance(value, str) and value.startswith("http")


def is_insider(source) -> bool:
    return isinstance(source, str) and source.strip() != "" and not source.startswith("http")


def missing_html(lang: str) -> str:
    return f'<span class="missing">{esc(T(lang, "not_published"))}</span>'


def render_construction_stages(value, lang: str) -> str:
    if not isinstance(value, list):
        return missing_html(lang)
    stage_names = {
        "land_plot": T(lang, "stage_land_plot"),
        "building_closed": T(lang, "stage_building_closed"),
        "building_95_percent_complete": T(lang, "stage_building_95"),
    }
    rows = []
    for item in value:
        if not isinstance(item, dict):
            continue
        label = stage_names.get(item.get("stage"), item.get("stage") or "")
        pct = item.get("max_ltv_pct")
        pct_html = esc(fmt_pct(pct, lang)) if pct is not None else missing_html(lang)
        if item.get("qualifier") == "usually":
            pct_html = esc(T(lang, "usually_word")) + " " + pct_html
        detail = item.get("condition") or item.get("basis") or ""
        detail_html = esc(tr(detail, lang)) if detail else ""
        rows.append(f"<tr><th scope=\"row\">{esc(label)}</th><td>{pct_html}</td><td>{detail_html}</td></tr>")
    return (
        "<table class=\"nested\">"
        f"<caption>{esc(T(lang, 'field_construction_ltv_stages'))}</caption>"
        "<thead><tr>"
        f"<th scope=\"col\">{esc(T(lang, 'stage_col'))}</th>"
        f"<th scope=\"col\">{esc(T(lang, 'region_ltv'))}</th>"
        f"<th scope=\"col\">{esc(T(lang, 'stage_detail'))}</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_regional_table(value, lang: str) -> str:
    rows = []
    for key, labels in REGION.items():
        item = value.get(key) if isinstance(value, dict) else None
        if not isinstance(item, dict):
            ltv = missing_html(lang)
            eis = missing_html(lang)
        else:
            ltv = esc(fmt_pct(item["max_ltv_pct"], lang)) if item.get("max_ltv_pct") is not None else missing_html(lang)
            eis = esc(fmt_pct(item["max_ltv_with_eis_pct"], lang)) if item.get("max_ltv_with_eis_pct") is not None else missing_html(lang)
        rows.append(
            f"<tr><th scope=\"row\">{esc(labels[lang])}</th><td>{ltv}</td><td>{eis}</td></tr>"
        )
    return (
        "<table class=\"nested\">"
        f"<caption>{esc(T(lang, 'field_regional_ltv_rules'))}</caption>"
        "<thead><tr>"
        f"<th scope=\"col\">{esc(T(lang, 'col_regional'))}</th>"
        f"<th scope=\"col\">{esc(T(lang, 'region_ltv'))}</th>"
        f"<th scope=\"col\">{esc(T(lang, 'region_ltv_eis'))}</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_value(value, lang: str, kind: str) -> str:
    if value is None:
        return missing_html(lang)
    if kind == "bool":
        return esc(T(lang, "yes" if value else "no"))
    if kind == "url":
        if not is_url(value):
            return missing_html(lang)
        return f'<a href="{esc(value)}">{esc(value)}</a>'
    if kind == "list":
        if not value:
            return missing_html(lang)
        items = "".join(f"<li>{esc(tr(item, lang))}</li>" for item in value)
        return f"<ul class=\"clean\">{items}</ul>"
    if kind == "programs":
        if not value:
            return missing_html(lang)
        items = "".join(f"<li>{esc(tr(item, lang))}</li>" for item in value)
        return f"<ul class=\"clean\">{items}</ul>"
    if kind == "regional":
        if isinstance(value, str):
            return esc(tr(value, lang))
        return render_regional_table(value, lang)
    if kind == "stages":
        return render_construction_stages(value, lang)
    if kind == "money":
        return esc(fmt_money(value, lang))
    if kind == "pct":
        return esc(fmt_pct(value, lang))
    if kind == "years":
        return esc(fmt_years(value, lang))
    if kind == "months":
        return esc(fmt_months(value, lang))
    if kind == "date":
        return f"<time datetime=\"{esc(value)}\">{esc(value)}</time>"
    if isinstance(value, str):
        return esc(tr(value, lang))
    return esc(value)


def source_html(source, lang: str) -> str:
    if is_insider(source):
        sentence = f'<span lang="en">{esc(source)}</span>' if lang == "et" else esc(source)
        return f'<strong class="badge">{esc(T(lang, "insider"))}</strong> {sentence}'
    if is_url(source):
        return f'<a href="{esc(source)}">{esc(T(lang, "source"))}</a>'
    return esc(T(lang, "no_source"))


def fact_rows(pairs, lang: str) -> str:
    rows = []
    for field_id, label, value_html, note, source, checked in pairs:
        note_html = esc(tr(note, lang)) if note else ""
        checked_html = f'<time datetime="{esc(checked)}">{esc(checked)}</time>' if checked else ""
        rows.append(
            f'<tr id="{esc(field_id)}">'
            f'<th scope="row">{esc(label)}</th>'
            f'<td data-label="{esc(T(lang, "value"))}">{value_html}</td>'
            f'<td data-label="{esc(T(lang, "note"))}">{note_html}</td>'
            f'<td data-label="{esc(T(lang, "source"))}">{source_html(source, lang)}</td>'
            f'<td data-label="{esc(T(lang, "checked"))}">{checked_html}</td>'
            "</tr>"
        )
    return "".join(rows)


def fact_table(caption: str, body: str, lang: str) -> str:
    return (
        '<div class="table-wrap"><table class="facts">'
        f"<caption>{esc(caption)}</caption>"
        "<thead><tr>"
        f"<th scope=\"col\">{esc(T(lang, 'col_field'))}</th>"
        f"<th scope=\"col\">{esc(T(lang, 'value'))}</th>"
        f"<th scope=\"col\">{esc(T(lang, 'note'))}</th>"
        f"<th scope=\"col\">{esc(T(lang, 'source'))}</th>"
        f"<th scope=\"col\">{esc(T(lang, 'checked'))}</th>"
        "</tr></thead><tbody>"
        f"{body}</tbody></table></div>"
    )


def field_tuple(field_id: str, field: dict, lang: str, kind: str, label_key: str):
    return (
        field_id,
        T(lang, label_key),
        render_value(field.get("value"), lang, kind),
        field.get("note"),
        field.get("source"),
        field.get("checked"),
    )


def regional_summary(value, lang: str) -> str:
    if not isinstance(value, dict):
        return missing_html(lang)
    parts = []
    for key, labels in REGION.items():
        item = value.get(key)
        if not isinstance(item, dict):
            parts.append(f"{labels[lang]}: {T(lang, 'not_published')}")
            continue
        ltv = fmt_pct(item["max_ltv_pct"], lang) if item.get("max_ltv_pct") is not None else T(lang, "not_published")
        eis = fmt_pct(item["max_ltv_with_eis_pct"], lang) if item.get("max_ltv_with_eis_pct") is not None else T(lang, "not_published")
        parts.append(f"{labels[lang]}: LTV {ltv}, {T(lang, 'with_eis')} {eis}")
    return esc(". ".join(parts)) + "."


def compact_value(field: dict, lang: str, kind: str) -> str:
    value_html = render_value(field.get("value"), lang, kind)
    bits = [f'<div class="value">{value_html}</div>']
    if is_insider(field.get("source")):
        bits.append(f'<p class="prov"><strong class="badge">{esc(T(lang, "insider"))}</strong></p>')
    note = field.get("note")
    if note:
        bits.append(
            f"<details><summary>{esc(T(lang, 'details'))}</summary>"
            f"<p class=\"note\">{esc(tr(note, lang))}</p></details>"
        )
    bits.append(f'<p class="prov">{source_html(field.get("source"), lang)} ')
    checked = field.get("checked")
    if checked:
        bits.append(f'<time datetime="{esc(checked)}">{esc(checked)}</time>')
    bits.append("</p>")
    return "".join(bits)


def status_short(status: str, lang: str) -> str:
    return {
        "stale": T(lang, "status_stale_short"),
        "current": T(lang, "status_current_short"),
        "below_curve": T(lang, "status_below_short"),
        "unknown": T(lang, "status_unknown_short"),
    }[status]


def tenor_label(code: str | None, lang: str) -> str:
    labels = {
        "et": {"1M": "1 kuu", "3M": "3 kuud", "6M": "6 kuud", "12M": "12 kuud"},
        "en": {"1M": "1 month", "3M": "3 months", "6M": "6 months", "12M": "12 months"},
    }
    if code is None:
        return T(lang, "tenor_unnamed")
    return labels[lang][code]


def sort_attr(value) -> str:
    if value is None or isinstance(value, bool):
        return ""
    return str(value)


def jsonld_script(payload) -> str:
    raw = json.dumps(payload, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{raw}</script>'


def organisation() -> dict:
    return {
        "@type": "Organization",
        "name": "Kodulaen",
        "url": SITE + "/",
        "description": "Neutral compilation of published Estonian housing-loan terms. Not a lender and not a credit intermediary.",
    }


def breadcrumb(lang: str, crumbs: list[tuple[str, str]]) -> dict:
    items = []
    for index, (name, path) in enumerate(crumbs, start=1):
        items.append({"@type": "ListItem", "position": index, "name": name, "item": absolute(path)})
    return {"@type": "BreadcrumbList", "itemListElement": items}


def render_document(lang, rel, title, description, body, current, jsonld, et_rel, en_rel, scripts="") -> str:
    et_url = absolute(url_for("et", et_rel))
    en_url = absolute(url_for("en", en_rel))
    page_url = et_url if lang == "et" else en_url
    full_title = title if title.endswith("Kodulaen") else f"{title} — Kodulaen"
    locale = "et_EE" if lang == "et" else "en_GB"
    nav = [
        ("", T(lang, "nav_home"), "home"),
        ("vorlus" if lang == "et" else "compare", T(lang, "nav_compare"), "compare"),
        ("kusimused" if lang == "et" else "questions", T(lang, "nav_questions"), "questions"),
        ("reeglid" if lang == "et" else "rules", T(lang, "nav_rules"), "rules"),
        ("euribor", T(lang, "nav_euribor"), "euribor"),
        ("turg" if lang == "et" else "market", T(lang, "nav_market"), "market"),
        ("muudatused" if lang == "et" else "changes", T(lang, "nav_changes"), "changes"),
        ("meist" if lang == "et" else "about", T(lang, "nav_about"), "about"),
    ]
    # nav hrefs are language-specific rels already. url_for adds /en for English,
    # so pass rel without a second prefix. The tuples above include the full rel
    # under that language. url_for(lang, rel) would double the prefix if rel is
    # already "rules" while lang is en — that is correct (en + rules). For ET,
    # rel is reeglid. Good.
    nav_html = []
    for rel_item, label, key in nav:
        href = url_for(lang, rel_item)
        current_attr = ' aria-current="page"' if key == current else ""
        nav_html.append(f'<a href="{esc(href)}"{current_attr}>{esc(label)}</a>')
    head_links = (
        f'<link rel="canonical" href="{esc(page_url)}">'
        f'<link rel="alternate" hreflang="et" href="{esc(et_url)}">'
        f'<link rel="alternate" hreflang="en" href="{esc(en_url)}">'
        f'<link rel="alternate" hreflang="x-default" href="{esc(et_url)}">'
        f'<link rel="alternate" type="application/json" href="{esc(absolute(data_url("banks.json")))}" title="banks.json">'
    )
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index, follow">
{verify_meta()}
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(page_url)}">
<meta property="og:locale" content="{locale}">
<meta property="og:locale:alternate" content="{"en_GB" if lang == "et" else "et_EE"}">
<meta property="article:modified_time" content="{esc(PAGE_MODIFIED)}">
<link rel="alternate" type="text/markdown" href="{esc(page_url.rstrip('/') + '/index.md' if rel else page_url + 'index.md')}">
{head_links}
<link rel="icon" href="{esc(asset('favicon.svg'))}" type="image/svg+xml">
<link rel="stylesheet" href="{esc(asset('style.css'))}">
{jsonld_script({"@context": "https://schema.org", "@graph": [{"@type": "WebSite", "name": "Kodulaen", "url": SITE + "/", "inLanguage": ["et", "en"]}, organisation(), {"@type": "WebPage", "url": page_url, "name": full_title, "description": description, "dateModified": PAGE_MODIFIED, "inLanguage": lang}]})}
{jsonld_script(jsonld) if jsonld else ""}
</head>
<body>
<a class="skip" href="#sisu">{esc(T(lang, "skip"))}</a>
<header>
  <div class="wrap bar">
    <div>
      <p class="site-name"><a href="{esc(url_for(lang, ""))}">Kodulaen</a></p>
      <p class="tagline">{esc(T(lang, "tagline"))}</p>
    </div>
    <div class="tools">
      <nav class="lang" aria-label="{esc(T(lang, "lang_label"))}">
        <a href="{esc(url_for("et", et_rel))}" hreflang="et" lang="et"{' aria-current="true"' if lang == "et" else ""}>ET</a>
        <a href="{esc(url_for("en", en_rel))}" hreflang="en" lang="en"{' aria-current="true"' if lang == "en" else ""}>EN</a>
      </nav>
      <p><span>{esc(T(lang, "page_updated"))}</span> <time datetime="{esc(PAGE_MODIFIED)}">{esc(PAGE_MODIFIED)}</time></p>
      <p><span>{esc(T(lang, "terms_checked"))}</span> <time datetime="{esc(TERMS_UPDATED)}">{esc(TERMS_UPDATED)}</time></p>
      <p><span>{esc(T(lang, "euribor_fetched"))}</span> <time datetime="{esc(EURIBOR_FETCHED)}">{esc(EURIBOR_FETCHED)}</time></p>
    </div>
  </div>
  <div class="wrap">
    <nav class="primary" aria-label="{esc(T(lang, "nav_label"))}">{"".join(nav_html)}</nav>
  </div>
</header>
<main id="sisu" class="wrap">
  <aside class="disclaimer" role="note"><strong>{esc(T(lang, "disclaimer_title"))}</strong> {esc(T(lang, "disclaimer"))}</aside>
  {body}
</main>
<footer>
  <div class="wrap">
    <p>{esc(T(lang, "footer_blurb"))}</p>
    <p>{esc(T(lang, "disclaimer"))}</p>
    <p>{esc(T(lang, "license_line"))}</p>
    <p>{esc(T(lang, "version_label"))} {esc(VERSION)}. {esc(T(lang, "terms_checked"))} <time datetime="{esc(TERMS_UPDATED)}">{esc(TERMS_UPDATED)}</time>.</p>
    <p>{esc(T(lang, "footer_data"))}</p>
    <ul>
      <li><a href="{esc(data_url("banks.json"))}">banks.json</a></li>
      <li><a href="{esc(data_url("banks.csv"))}">banks.csv</a></li>
      <li><a href="{esc(data_url("euribor.json"))}">euribor.json</a></li>
      <li><a href="{esc(data_url("sources.json"))}">sources.json</a></li>
      <li><a href="{esc(data_url("schema.json"))}">schema.json</a></li>
      <li><a href="{esc((BASE or "") + "/llms.txt")}">llms.txt</a></li>
      <li><a href="{esc((BASE or "") + "/llms-full.txt")}">llms-full.txt</a></li>
    </ul>
    <p>{esc(T(lang, "footer_banks"))}</p>
    <ul>
      {"".join(f'<li><a href="{esc(url_for(lang, ("pangad/" if lang == "et" else "banks/") + bank["id"]))}">{esc(bank["bank_name"])}</a></li>' for bank in BANKS)}
    </ul>
  </div>
</footer>
{scripts}
<script data-goatcounter="https://hastitore.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""


def crumbs_html(lang, items):
    parts = []
    for index, (label, href) in enumerate(items):
        if index:
            parts.append(" / ")
        if href:
            parts.append(f'<a href="{esc(href)}">{esc(label)}</a>')
        else:
            parts.append(f"<span>{esc(label)}</span>")
    return f'<nav class="crumbs" aria-label="{esc(T(lang, "crumb_label"))}">{"".join(parts)}</nav>'


def euribor_strip(lang: str) -> str:
    items = []
    for code in TENOR_ORDER:
        rate = EURIBOR["rates"][code]
        items.append(
            "<li>"
            f'<span class="tenor">{esc(tenor_label(code, lang))} Euribor</span>'
            f'<span class="rate">{esc(fmt_pct(rate["rate_pct"], lang))}</span>'
            f'<span class="small">{esc(T(lang, "value_date_label"))} <time datetime="{esc(rate["value_date"])}">{esc(rate["value_date"])}</time></span>'
            "</li>"
        )
    return (
        f'<section class="panel" aria-labelledby="euribor-now">'
        f'<h2 id="euribor-now">{esc(T(lang, "euribor_home_title"))}</h2>'
        f'<ul class="euribor-now">{"".join(items)}</ul>'
        f'<p class="small">{esc(T(lang, "attribution"))} '
        f'<a href="{esc(EURIBOR["source_url"])}">euribor-rates.eu</a>. '
        f'<a href="https://www.emmi-benchmarks.eu/">EMMI</a>.</p>'
        f'<p class="small">{esc(T(lang, "licensing"))} {esc(tr(EURIBOR["licensing_note"], lang))}</p>'
        f'<p><a href="{esc(url_for(lang, "euribor"))}">{esc(T(lang, "open_euribor"))}</a></p>'
        "</section>"
    )


def comparison_section(lang: str) -> str:
    headers = [
        ("col_bank", None),
        ("col_rate", None),
        ("col_margin", None),
        ("col_fee", None),
        ("col_min_loan", None),
        ("col_down", None),
        ("col_ltv", None),
        ("col_ltv_eis", None),
        ("col_regional", None),
        ("col_term", None),
        ("col_nominal", None),
        ("col_apr", None),
        ("col_uniform", None),
        ("col_example_euribor", None),
        ("col_eis", None),
    ]
    head = "".join(f'<th scope="col">{esc(T(lang, key))}</th>' for key, _ in headers)
    rows = []
    for bank in BANKS:
        info = ASSESS[bank["id"]]
        example = bank["worked_example"]
        bank_href = url_for(lang, ("pangad/" if lang == "et" else "banks/") + bank["id"])
        euribor_bits = []
        if example["euribor_pct"]["value"] is None and example["euribor_date"]["value"] is None:
            euribor_bits.append(missing_html(lang))
        else:
            if example["euribor_pct"]["value"] is not None:
                euribor_bits.append(esc(fmt_pct(example["euribor_pct"]["value"], lang)))
            else:
                euribor_bits.append(missing_html(lang))
            if example["euribor_date"]["value"]:
                euribor_bits.append(f' <time datetime="{esc(example["euribor_date"]["value"])}">{esc(example["euribor_date"]["value"])}</time>')
            else:
                euribor_bits.append(" " + missing_html(lang))
        euribor_bits.append(f' <span class="flag">{esc(status_short(info["status"], lang))}</span>')
        euribor_bits.append(f'<p class="prov">{source_html(example["euribor_pct"].get("source"), lang)} ')
        if example["euribor_pct"].get("checked"):
            euribor_bits.append(f'<time datetime="{esc(example["euribor_pct"]["checked"])}">{esc(example["euribor_pct"]["checked"])}</time>')
        euribor_bits.append("</p>")
        cells = [
            compact_value(bank["rate_basis"], lang, "text"),
            compact_value(bank["margin"], lang, "text"),
            compact_value(bank["contract_fee"], lang, "text"),
            compact_value(bank["min_loan_amount_eur"], lang, "money"),
            compact_value(bank["min_down_payment_pct"], lang, "pct"),
            compact_value(bank["max_ltv_pct"], lang, "pct"),
            compact_value(bank["max_ltv_with_eis_pct"], lang, "pct"),
            compact_value(bank["regional_ltv_rules"], lang, "text")
            if not isinstance(bank["regional_ltv_rules"].get("value"), dict)
            else (
                f'<div class="value">{regional_summary(bank["regional_ltv_rules"]["value"], lang)}</div>'
                + (f'<p class="prov"><strong class="badge">{esc(T(lang, "insider"))}</strong></p>' if is_insider(bank["regional_ltv_rules"].get("source")) else "")
                + (f'<details><summary>{esc(T(lang, "details"))}</summary><p class="note">{esc(tr(bank["regional_ltv_rules"].get("note"), lang))}</p></details>' if bank["regional_ltv_rules"].get("note") else "")
                + f'<p class="prov">{source_html(bank["regional_ltv_rules"].get("source"), lang)} '
                + (f'<time datetime="{esc(bank["regional_ltv_rules"]["checked"])}">{esc(bank["regional_ltv_rules"]["checked"])}</time>' if bank["regional_ltv_rules"].get("checked") else "")
                + "</p>"
            ),
            compact_value(bank["max_term_years"], lang, "years"),
            compact_value(example["nominal_rate_pct"], lang, "pct"),
            compact_value(example["apr_pct"], lang, "pct"),
            (
                f'<div class="value">{esc(fmt_money(ILLUSTRATIVE["monthly_payment_eur"], lang))}</div>'
                f'<p class="small">{esc(uniform_rate_label(lang))}</p>'
                f'<p class="small">{esc(uniform_assumption_note(lang))}</p>'
            ),
            "".join(euribor_bits),
            compact_value(bank["eis_participation"], lang, "bool"),
        ]
        attrs = {
            "bank": bank["bank_name"],
            "min-loan": sort_attr(bank["min_loan_amount_eur"]["value"]),
            "down": sort_attr(bank["min_down_payment_pct"]["value"]),
            "ltv": sort_attr(bank["max_ltv_pct"]["value"]),
            "ltv-eis": sort_attr(bank["max_ltv_with_eis_pct"]["value"]),
            "term": sort_attr(bank["max_term_years"]["value"]),
            "nominal": sort_attr(example["nominal_rate_pct"]["value"]),
            "apr": sort_attr(example["apr_pct"]["value"]),
            "euribor-date": example["euribor_date"]["value"] or "",
        }
        attr_html = " ".join(f'data-{key}="{esc(val)}"' for key, val in attrs.items())
        td = "".join(f"<td>{cell}</td>" for cell in cells)
        rows.append(
            f"<tr {attr_html}><th scope=\"row\"><a href=\"{esc(bank_href)}\">{esc(bank['bank_name'])}</a>"
            f"<span class=\"legal\">{esc(bank['legal_name'])}</span></th>{td}</tr>"
        )
    options = [
        ("bank", "sort_bank"),
        ("min-loan", "sort_min_loan"),
        ("down", "sort_down"),
        ("ltv", "sort_ltv"),
        ("ltv-eis", "sort_ltv_eis"),
        ("term", "sort_term"),
        ("nominal", "sort_nominal"),
        ("apr", "sort_apr"),
        ("euribor-date", "sort_euribor_date"),
    ]
    option_html = "".join(f'<option value="{esc(value)}">{esc(T(lang, key))}</option>' for value, key in options)
    return f"""
<section aria-labelledby="compare-title">
  <h2 id="compare-title">{esc(T(lang, "nav_home"))}</h2>
  <div class="controls">
    <div>
      <label for="sort-key">{esc(T(lang, "sort_key"))}</label>
      <select id="sort-key">{option_html}</select>
    </div>
    <div>
      <label for="sort-dir">{esc(T(lang, "sort_dir"))}</label>
      <select id="sort-dir">
        <option value="asc">{esc(T(lang, "dir_asc"))}</option>
        <option value="desc">{esc(T(lang, "dir_desc"))}</option>
      </select>
    </div>
    <p id="sort-status" class="small" aria-live="polite">{esc(T(lang, "sort_bank"))}, {esc(T(lang, "dir_asc"))}</p>
  </div>
  <p class="small">{esc(T(lang, "sort_help"))}</p>
  <noscript><p>{esc(T(lang, "noscript"))}</p></noscript>
  <p class="small">{esc(T(lang, "scroll_hint"))}</p>
  <p class="small">{esc(uniform_rate_label(lang))}. {esc(uniform_assumption_note(lang))} {esc(fmt_money(ILLUSTRATIVE["loan_amount_eur"], lang))}, {esc(fmt_months(ILLUSTRATIVE["term_months"], lang))}, annuiteet. {esc(ILLUSTRATIVE["fee_note"] if lang == "en" else "Kuumakse ei sisalda tasusid. Panga avaldatud lepingutasu on eraldi ja võib erineda.")}</p>
  <div class="table-wrap">
    <table class="compare" id="compare">
      <caption>{esc(T(lang, "caption_compare"))}</caption>
      <thead><tr>{head}</tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
  </div>
</section>
"""


def home_body(lang: str) -> str:
    questions = "kusimused" if lang == "et" else "questions"
    compare = "vorlus" if lang == "et" else "compare"
    changes = "muudatused" if lang == "et" else "changes"
    market = "turg" if lang == "et" else "market"
    return f"""
{euribor_strip(lang)}
<h1>{esc(T(lang, "home_h1"))}</h1>
<p class="lead">{esc(T(lang, "home_lead"))}</p>
<p><a href="{esc(url_for(lang, market))}">{esc(T(lang, "nav_market"))}</a> · <a href="{esc(url_for(lang, compare))}">{esc(T(lang, "nav_compare"))}</a> · <a href="{esc(url_for(lang, questions))}">{esc(T(lang, "nav_questions"))}</a> · <a href="{esc(url_for(lang, changes))}">{esc(T(lang, "nav_changes"))}</a></p>
<section aria-labelledby="how">
  <h2 id="how">{esc(T(lang, "home_read_title"))}</h2>
  <ul>
    <li>{esc(T(lang, "read_alpha"))}</li>
    <li>{esc(T(lang, "read_cell"))}</li>
    <li>{esc(T(lang, "read_null"))}</li>
    <li>{esc(T(lang, "read_promo"))}</li>
  </ul>
  <p><a href="{esc(url_for(lang, "reeglid" if lang == "et" else "rules"))}">{esc(T(lang, "open_rules"))}</a></p>
</section>
{comparison_section(lang)}
<section class="panel" aria-labelledby="machines">
  <h2 id="machines">{esc(T(lang, "machines_title"))}</h2>
  <p>{esc(T(lang, "machines_lead"))}</p>
  <ul>
    <li><a href="{esc(data_url("banks.json"))}">/data/banks.json</a></li>
    <li><a href="{esc(data_url("banks.csv"))}">/data/banks.csv</a></li>
    <li><a href="{esc(data_url("euribor.json"))}">/data/euribor.json</a></li>
    <li><a href="{esc(data_url("sources.json"))}">/data/sources.json</a></li>
    <li><a href="{esc(data_url("schema.json"))}">/data/schema.json</a></li>
    <li><a href="{esc((BASE or "") + "/llms.txt")}">/llms.txt</a></li>
    <li><a href="{esc((BASE or "") + "/llms-full.txt")}">/llms-full.txt</a></li>
  </ul>
</section>
"""


def illustration_html(bank, info, lang) -> str:
    example = ILLUSTRATIVE
    payment = fmt_money(example["monthly_payment_eur"], lang)
    fee = plain_value(bank["contract_fee"], lang, "text")
    if lang == "et":
        inputs = (
            f"Ühtne sisend kõigil pankadel: laenusumma {fmt_money(example['loan_amount_eur'], lang)}, "
            f"tähtaeg {fmt_months(example['term_months'], lang)}, tagasimakse annuiteet, intress {uniform_rate_label(lang)}. "
            f"Kuumakse selle valemiga on {payment}. Lepingutasu ei ole kuumakse sees. "
            f"Panga avaldatud lepingutasu, mis võib erineda: {fee}."
        )
    else:
        inputs = (
            f"Uniform inputs for every bank: loan amount {fmt_money(example['loan_amount_eur'], lang)}, "
            f"term {fmt_months(example['term_months'], lang)}, annuity repayment, rate {uniform_rate_label(lang)}. "
            f"The payment on that formula is {payment}. The contract fee is not inside the payment. "
            f"The bank's published contract fee, which may differ: {fee}."
        )
    stale = ""
    if info["status"] == "stale":
        stale = f'<p class="flag">{esc(T(lang, "stale"))}</p>'
    elif info["status"] == "below_curve":
        stale = f"<p>{esc(T(lang, 'below_curve'))}</p>"
    elif info["status"] == "unknown":
        stale = f"<p>{esc(T(lang, 'unknown_status'))}</p>"
    elif info["status"] == "current":
        stale = f"<p>{esc(T(lang, 'in_line'))}</p>"
    return (
        f'<section class="illustration" id="illustratsioon" aria-labelledby="illus-title">'
        f'<h2 id="illus-title">{esc(T(lang, "illustration_title"))}</h2>'
        f"<p>{esc(uniform_assumption_note(lang))}</p>"
        f"<p>{esc(inputs)}</p>"
        f"{stale}"
        f"<p>{esc(T(lang, 'formula'))}</p>"
        f"<p>{esc(T(lang, 'formula_excludes'))}</p>"
        f'<p class="prov">{source_html(bank["contract_fee"].get("source"), lang)} '
        f'<time datetime="{esc(bank["contract_fee"].get("checked") or "")}">{esc(bank["contract_fee"].get("checked") or "")}</time> · '
        f'<a href="{esc(example["euribor_source_url"])}">euribor-rates.eu</a> '
        f'<time datetime="{esc(example["euribor_value_date"])}">{esc(example["euribor_value_date"])}</time></p>'
        "</section>"
    )


def bank_search_title(bank, lang: str) -> str:
    year = TERMS_UPDATED[:4]
    if lang == "et":
        return f"{bank['bank_name']} kodulaen: tingimused, intress, sissemakse ja LTV ({year})"
    return f"{bank['bank_name']} housing loan: terms, interest, down payment and LTV ({year})"


def plain_value(field, lang: str, kind: str) -> str:
    if not field or field.get("value") is None:
        return T(lang, "not_published")
    value = field["value"]
    if kind == "pct" and isinstance(value, (int, float)) and not isinstance(value, bool):
        return fmt_pct(value, lang)
    if kind == "money" and isinstance(value, (int, float)) and not isinstance(value, bool):
        return fmt_money(value, lang)
    if kind == "years" and isinstance(value, (int, float)) and not isinstance(value, bool):
        return fmt_years(value, lang)
    if kind == "bool" and isinstance(value, bool):
        return T(lang, "yes" if value else "no")
    if isinstance(value, list):
        return ", ".join(tr(item, lang) if isinstance(item, str) else json.dumps(item, ensure_ascii=False) for item in value)
    if isinstance(value, str):
        return tr(value, lang)
    return str(value)


def bank_summary(bank, lang: str) -> str:
    checked = bank["rate_basis"].get("checked") or TERMS_UPDATED
    bits = {
        "rate": plain_value(bank["rate_basis"], lang, "text"),
        "margin": plain_value(bank["margin"], lang, "text"),
        "fee": plain_value(bank["contract_fee"], lang, "text"),
        "down": plain_value(bank["min_down_payment_pct"], lang, "pct"),
        "ltv": plain_value(bank["max_ltv_pct"], lang, "pct"),
        "eis": plain_value(bank["max_ltv_with_eis_pct"], lang, "pct"),
        "term": plain_value(bank["max_term_years"], lang, "years"),
        "nominal": plain_value(bank["worked_example"]["nominal_rate_pct"], lang, "pct"),
        "apr": plain_value(bank["worked_example"]["apr_pct"], lang, "pct"),
    }
    if lang == "et":
        text = (
            f"{bank['bank_name']} ({bank['legal_name']}) avaldab kodulaenu tingimused oma lehel. "
            f"Intressi alus: {bits['rate']}. Marginaal: {bits['margin']}. Lepingutasu: {bits['fee']}. "
            f"Minimaalne sissemakse: {bits['down']}. Maksimaalne LTV: {bits['ltv']}. "
            f"Maksimaalne LTV EIS-i käendusega: {bits['eis']}. Maksimaalne tähtaeg: {bits['term']}. "
            f"Tüüpnäite nominaalintress (panga avaldatud): {bits['nominal']}. Tüüpnäite krediidi kulukuse määr (panga avaldatud): {bits['apr']}. "
            f"Kodulaenu samamäärane näide, mitte panga pakkumine: {uniform_rate_label(lang)}, kuumakse {fmt_money(ILLUSTRATIVE['monthly_payment_eur'], lang)} "
            f"laenusummal {fmt_money(ILLUSTRATIVE['loan_amount_eur'], lang)} ja tähtajal {fmt_months(ILLUSTRATIVE['term_months'], lang)}. "
            f"Kontrollitud {checked}. Allikad on allolevas tabelis."
        )
    else:
        text = (
            f"{bank['bank_name']} ({bank['legal_name']}) publishes its housing-loan terms on its own page. "
            f"Rate basis: {bits['rate']}. Margin: {bits['margin']}. Contract fee: {bits['fee']}. "
            f"Minimum down payment: {bits['down']}. Maximum LTV: {bits['ltv']}. "
            f"Maximum LTV with the EIS guarantee: {bits['eis']}. Maximum term: {bits['term']}. "
            f"Worked-example nominal rate (published by the bank): {bits['nominal']}. Worked-example APR (published by the bank): {bits['apr']}. "
            f"Kodulaen same-rate example, not a bank offer: {uniform_rate_label(lang)}, payment {fmt_money(ILLUSTRATIVE['monthly_payment_eur'], lang)} "
            f"on {fmt_money(ILLUSTRATIVE['loan_amount_eur'], lang)} over {fmt_months(ILLUSTRATIVE['term_months'], lang)}. "
            f"Checked {checked}. Sources are in the table below."
        )
    if is_insider(bank.get("regional_ltv_rules", {}).get("source")) or "construction_ltv_stages" in bank:
        if lang == "et":
            text += " Osa LTV üksikasju on tööstusharu siseteave, mitte panga lehel avaldatud tingimus."
        else:
            text += " Some LTV detail is industry insider information, not a term published on the bank's website."
    return text


def bank_body(bank, lang: str) -> str:
    pairs = [
        field_tuple(key, bank[key], lang, kind, "field_" + key)
        for key, kind in BANK_FIELDS
        if key in bank
    ]
    example_pairs = [
        field_tuple("example-" + key, bank["worked_example"][key], lang, kind, "ex_" + key)
        for key, kind in EXAMPLE_FIELDS
    ]
    info = ASSESS[bank["id"]]
    page_rel = ("pangad/" if lang == "et" else "banks/") + bank["id"]
    title = bank_search_title(bank, lang)
    return (
        crumbs_html(lang, [("Kodulaen", url_for(lang, "")), (bank["bank_name"], None)])
        + f"<h1>{esc(title)}</h1>"
        + f"<p class=\"lead\">{esc(bank_summary(bank, lang))}</p>"
        + f"<p class=\"small\">{esc(T(lang, 'page_updated'))} <time datetime=\"{esc(PAGE_MODIFIED)}\">{esc(PAGE_MODIFIED)}</time>. "
        + f"{esc(T(lang, 'terms_checked'))} <time datetime=\"{esc(TERMS_UPDATED)}\">{esc(TERMS_UPDATED)}</time>.</p>"
        + fact_table(T(lang, "caption_facts").format(bank=bank["legal_name"]), fact_rows(pairs, lang), lang)
        + f'<h2 id="tuupnaide">{esc(T(lang, "example_title"))}</h2>'
        + f"<p>{esc(T(lang, 'example_intro'))}</p>"
        + fact_table(T(lang, "caption_example").format(bank=bank["bank_name"]), fact_rows(example_pairs, lang), lang)
        + illustration_html(bank, info, lang)
    )


def rules_body(lang: str) -> str:
    rules = SOURCES["eesti_pank_lending_rules"]
    eis = SOURCES["eis_housing_loan_guarantee"]
    rural = SOURCES["eis_rural_housing_loan_guarantee"]
    stats = SOURCES["eesti_pank_new_housing_loans"]

    def row(label, value_html):
        return f"<tr><th scope=\"row\">{esc(label)}</th><td>{value_html}</td></tr>"

    ep_rows = "".join([
        row(T(lang, "ep_ltv"), esc(fmt_pct(rules["max_ltv_pct"], lang))),
        row(T(lang, "ep_ltv_guarantee"), esc(fmt_pct(rules["max_ltv_state_guaranteed_pct"], lang))),
        row(T(lang, "ep_dsti"), esc(fmt_pct(rules["max_dsti_pct"], lang))),
        row(T(lang, "ep_stress"), esc(tr(rules["dsti_stress_rate"], lang))),
        row(T(lang, "ep_term"), esc(fmt_years(rules["max_term_years"], lang))),
        row(T(lang, "ep_exception"), esc(tr(rules["exception"], lang))),
        row(T(lang, "ep_since"), f'<time datetime="{esc(rules["in_force_since"])}">{esc(rules["in_force_since"])}</time>'),
    ])
    eis_rows = "".join([
        row(T(lang, "eis_apply"), esc(tr(eis["how_to_apply"], lang))),
        row(T(lang, "eis_banks"), "<ul class=\"clean\">" + "".join(f"<li>{esc(name)}</li>" for name in eis["issuing_banks"]) + "</ul>"),
        row(T(lang, "eis_down"), esc(fmt_pct(eis["min_down_payment_pct"], lang))),
        row(T(lang, "eis_down_large"), esc(fmt_pct(eis["min_down_payment_large_family_pct"], lang))),
        row(T(lang, "eis_size"), esc(tr(eis["guarantee_size"], lang))),
        row(T(lang, "eis_cap"), esc(tr(eis["loan_amount_cap"], lang))),
        row(T(lang, "eis_fee"), esc(tr(eis["fee"], lang))),
        row(T(lang, "eis_over30"), esc(tr(eis["term_over_30y_conditions"], lang))),
        row(T(lang, "eis_no_home"), esc(tr(eis["no_other_home_rule"], lang))),
        row(T(lang, "eis_holiday"), esc(tr(eis["payment_holiday"], lang))),
    ])
    group_rows = []
    for code in PROGRAM_ORDER:
        if code == "rural":
            continue
        group_rows.append(
            f'<tr><th scope="row">{esc(T(lang, "group_" + code))}</th><td>{esc(tr(eis["target_groups"][code], lang))}</td></tr>'
        )
    head_banks = "".join(f'<th scope="col">{esc(bank["bank_name"])}</th>' for bank in BANKS)
    matrix_rows = []
    for code in PROGRAM_ORDER:
        if code == "rural":
            continue
        cells = []
        for bank in BANKS:
            programs = bank["eis_programs"]["value"]
            if programs is None:
                label = T(lang, "does_not_itemise")
            elif code in programs:
                label = T(lang, "names")
            else:
                label = T(lang, "does_not_name")
            cells.append(f"<td>{esc(label)}</td>")
        matrix_rows.append(f'<tr><th scope="row">{esc(T(lang, "group_" + code))}</th>{"".join(cells)}</tr>')
    rural_rows = "".join([
        row(T(lang, "rural_banks"), "<ul class=\"clean\">" + "".join(f"<li>{esc(name)}</li>" for name in rural["banks"]) + "</ul>"),
        row(T(lang, "rural_down"), esc(tr(rural["min_down_payment_pct"], lang))),
        row(T(lang, "rural_guarantee"), esc(tr(rural["guarantee"], lang))),
        row(T(lang, "rural_cap"), esc(tr(rural["loan_cap"], lang))),
        row(T(lang, "rural_fee"), esc(tr(rural["fee"], lang))),
    ])

    def series_table(title, points, value_key, as_pct):
        body = []
        for point in points:
            shown = fmt_pct(point[value_key], lang) if as_pct else fmt_money(point[value_key] * 1_000_000, lang).replace("\u00a0€", "").strip()
            if not as_pct:
                shown = str(point[value_key])
            body.append(f'<tr><th scope="row"><time datetime="{esc(point["month"])}">{esc(point["month"])}</time></th><td>{esc(shown if as_pct else str(point[value_key]))}</td></tr>')
        unit = "%" if as_pct else "mln €"
        return (
            f"<h3>{esc(title)}</h3>"
            '<div class="table-wrap"><table><thead><tr>'
            f'<th scope="col">{esc(T(lang, "month"))}</th><th scope="col">{esc(unit)}</th>'
            "</tr></thead><tbody>"
            + "".join(body)
            + "</tbody></table></div>"
        )

    return (
        crumbs_html(lang, [("Kodulaen", url_for(lang, "")), (T(lang, "nav_rules"), None)])
        + f'<h1>{esc(T(lang, "rules_h1"))}</h1>'
        + f'<p class="lead">{esc(T(lang, "rules_lead"))}</p>'
        + f'<h2>{esc(T(lang, "rules_buyer_title"))}</h2>'
        + f'<p>{esc(T(lang, "rules_buyer"))}</p>'
        + f'<h2>{esc(T(lang, "ep_title"))}</h2>'
        + '<div class="table-wrap"><table><caption>'
        + esc(T(lang, "ep_title"))
        + "</caption><tbody>"
        + ep_rows
        + "</tbody></table></div>"
        + f'<p class="prov"><a href="{esc(rules["source"])}">{esc(T(lang, "source"))}</a> <time datetime="{esc(rules["checked"])}">{esc(rules["checked"])}</time></p>'
        + f'<h2>{esc(T(lang, "eis_title"))}</h2>'
        + '<div class="table-wrap"><table><caption>'
        + esc(T(lang, "eis_title"))
        + "</caption><tbody>"
        + eis_rows
        + "</tbody></table></div>"
        + f'<p class="prov"><a href="{esc(eis["source"])}">{esc(T(lang, "source"))}</a> <time datetime="{esc(eis["checked"])}">{esc(eis["checked"])}</time></p>'
        + f'<h2>{esc(T(lang, "eis_groups_title"))}</h2>'
        + '<div class="table-wrap"><table><caption>'
        + esc(T(lang, "eis_groups_title"))
        + "</caption><tbody>"
        + "".join(group_rows)
        + "</tbody></table></div>"
        + f'<h2>{esc(T(lang, "named_title"))}</h2>'
        + f'<p>{esc(T(lang, "named_note"))}</p>'
        + '<div class="table-wrap"><table class="compare"><thead><tr><th scope="col">'
        + esc(T(lang, "eis_groups_title"))
        + "</th>"
        + head_banks
        + "</tr></thead><tbody>"
        + "".join(matrix_rows)
        + "</tbody></table></div>"
        + f'<h2>{esc(T(lang, "rural_title"))}</h2>'
        + '<div class="table-wrap"><table><caption>'
        + esc(T(lang, "rural_title"))
        + "</caption><tbody>"
        + rural_rows
        + "</tbody></table></div>"
        + f'<p class="prov"><a href="{esc(rural["source"])}">{esc(T(lang, "source"))}</a> <time datetime="{esc(rural["checked"])}">{esc(rural["checked"])}</time></p>'
        + f'<h2>{esc(T(lang, "stats_title"))}</h2>'
        + f'<p>{esc(tr(stats["description"], lang))}</p>'
        + f'<p>{esc(T(lang, "stats_note"))}</p>'
        + series_table(T(lang, "stats_avg"), stats["avg_rate_new_business_pct"], "pct", True)
        + f'<p class="small"><code>{esc(stats["avg_rate_new_business_series"])}</code></p>'
        + series_table(T(lang, "stats_var"), stats["avg_rate_variable_upto_1y_pct"], "pct", True)
        + f'<p class="small"><code>{esc(stats["avg_rate_variable_series"])}</code></p>'
        + series_table(T(lang, "stats_vol"), stats["volume_pure_new_loans_eur_million"], "value", False)
        + f'<p class="small"><code>{esc(stats["volume_series"])}</code></p>'
        + f'<h3>{esc(T(lang, "stats_next"))}</h3><p>{esc(tr(stats["next_release"], lang))}</p>'
        + f'<p class="prov"><a href="{esc(stats["source"])}">{esc(T(lang, "source"))}</a> · <a href="{esc(stats["eesti_pank_stats_page"])}">Eesti Pank</a> <time datetime="{esc(stats["checked"])}">{esc(stats["checked"])}</time></p>'
        + f'<p><a href="{esc(url_for(lang, "turg" if lang == "et" else "market"))}">{esc(T(lang, "market_link_from_rules"))}</a></p>'
    )


def euribor_body(lang: str) -> str:
    rate_rows = []
    for code in TENOR_ORDER:
        item = EURIBOR["rates"][code]
        rate_rows.append(
            "<tr>"
            f'<th scope="row">{esc(tenor_label(code, lang))}</th>'
            f'<td>{esc(fmt_pct(item["rate_pct"], lang))}</td>'
            f'<td><time datetime="{esc(item["value_date"])}">{esc(item["value_date"])}</time></td>'
            f'<td><a href="{esc(item["source_url"])}">{esc(T(lang, "source"))}</a></td>'
            "</tr>"
        )
    compare_rows = []
    for bank in BANKS:
        info = ASSESS[bank["id"]]
        href = url_for(lang, ("pangad/" if lang == "et" else "banks/") + bank["id"])
        example_rate = missing_html(lang) if info["example_euribor"] is None else esc(fmt_pct(info["example_euribor"], lang))
        example_date = missing_html(lang) if not info["example_date"] else f'<time datetime="{esc(info["example_date"])}">{esc(info["example_date"])}</time>'
        today = missing_html(lang) if info["current_rate"] is None else esc(fmt_pct(info["current_rate"], lang))
        compare_rows.append(
            "<tr>"
            f'<th scope="row"><a href="{esc(href)}">{esc(bank["bank_name"])}</a></th>'
            f"<td>{example_rate}</td><td>{example_date}</td>"
            f'<td>{esc(tenor_label(info["tenor"], lang))}</td>'
            f"<td>{today}</td>"
            f'<td>{esc(status_short(info["status"], lang))}</td>'
            "</tr>"
        )
    history = SOURCES["euribor_6m"]
    history_rows = "".join(
        f'<tr><th scope="row"><time datetime="{esc(point["date"])}">{esc(point["date"])}</time></th><td>{esc(fmt_pct(point["pct"], lang))}</td></tr>'
        for point in history["recent"]
    )
    return (
        crumbs_html(lang, [("Kodulaen", url_for(lang, "")), ("Euribor", None)])
        + f'<h1>{esc(T(lang, "euribor_h1"))}</h1>'
        + f'<p class="lead">{esc(T(lang, "euribor_lead"))}</p>'
        + f'<aside class="disclaimer" role="note"><strong>{esc(T(lang, "licensing"))}</strong> {esc(tr(EURIBOR["licensing_note"], lang))}</aside>'
        + f'<h2>{esc(T(lang, "current_title"))}</h2>'
        + f'<p>{esc(T(lang, "attribution"))}</p>'
        + '<div class="table-wrap"><table><caption>Euribor</caption><thead><tr>'
        + f'<th scope="col">{esc(T(lang, "tenor"))}</th>'
        + f'<th scope="col">{esc(T(lang, "rate"))}</th>'
        + f'<th scope="col">{esc(T(lang, "value_date_label"))}</th>'
        + f'<th scope="col">{esc(T(lang, "source"))}</th>'
        + "</tr></thead><tbody>"
        + "".join(rate_rows)
        + "</tbody></table></div>"
        + f'<p class="small">{esc(T(lang, "euribor_fetched"))} <time datetime="{esc(EURIBOR_FETCHED)}">{esc(EURIBOR_FETCHED)}</time>. '
        + f'{esc(EURIBOR["source_type"])}</p>'
        + f'<h2>{esc(T(lang, "compare_title"))}</h2>'
        + f'<p>{esc(T(lang, "compare_note"))}</p>'
        + '<div class="table-wrap"><table><thead><tr>'
        + f'<th scope="col">{esc(T(lang, "col_bank"))}</th>'
        + f'<th scope="col">{esc(T(lang, "col_example_rate"))}</th>'
        + f'<th scope="col">{esc(T(lang, "col_example_date"))}</th>'
        + f'<th scope="col">{esc(T(lang, "col_tenor"))}</th>'
        + f'<th scope="col">{esc(T(lang, "col_today"))}</th>'
        + f'<th scope="col">{esc(T(lang, "col_status"))}</th>'
        + "</tr></thead><tbody>"
        + "".join(compare_rows)
        + "</tbody></table></div>"
        + f'<h2>{esc(T(lang, "history_title"))}</h2>'
        + f'<p>{esc(T(lang, "history_note"))}</p>'
        + '<div class="table-wrap"><table><thead><tr>'
        + f'<th scope="col">{esc(T(lang, "value_date_label"))}</th><th scope="col">6 {esc(T(lang, "tenor"))}</th>'
        + "</tr></thead><tbody>"
        + history_rows
        + "</tbody></table></div>"
        + f'<p class="prov"><a href="{esc(history["source"])}">{esc(T(lang, "source"))}</a> <time datetime="{esc(history["checked"])}">{esc(history["checked"])}</time></p>'
        + f'<h2>{esc(T(lang, "cross_title"))}</h2>'
        + f'<p>{esc(tr(history["cross_check"], lang))}</p>'
        + f'<p><a href="{esc(url_for(lang, "turg" if lang == "et" else "market"))}">{esc(T(lang, "market_link_from_euribor"))}</a></p>'
    )


def market_numbers(lang: str) -> dict:
    """The computed pieces the market page and its answers share."""
    stats = SOURCES["eesti_pank_new_housing_loans"]
    avg = stats["avg_rate_new_business_pct"]
    latest = avg[-1]
    year_ago_month = str(int(latest["month"][:4]) - 1) + latest["month"][4:]
    prior = next((point["pct"] for point in avg if point["month"] == year_ago_month), None)
    euribor = EURIBOR["rates"]["6M"]
    diff = (Decimal(str(latest["pct"])) - Decimal(str(euribor["rate_pct"]))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    base = Decimal(str(latest["pct"]))
    payment = annuity(100000, base, 300)
    payment_up = annuity(100000, base + Decimal("0.1"), 300)
    tenth_month = payment_up - payment
    return {
        "stats": stats,
        "latest": latest,
        "prior": prior,
        "euribor": euribor,
        "diff": diff,
        "payment": payment,
        "tenth_month": tenth_month,
        "tenth_total": (tenth_month * 300).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    }


def market_body(lang: str) -> str:
    info = market_numbers(lang)
    stats = info["stats"]
    latest = info["latest"]
    avg = stats["avg_rate_new_business_pct"]
    var = {point["month"]: point["pct"] for point in stats["avg_rate_variable_upto_1y_pct"]}
    volumes = {point["month"]: point["value"] for point in stats["volume_pure_new_loans_eur_million"]}

    def num(value, places, lang):
        quantized = Decimal(str(value)).quantize(Decimal("1." + "0" * places), rounding=ROUND_HALF_UP)
        text = f"{quantized:.{places}f}"
        return text.replace(".", ",") if lang == "et" else text

    latest_text = fmt_pct(latest["pct"], lang)
    prior_text = fmt_pct(info["prior"], lang) if info["prior"] is not None else T(lang, "not_published")
    month = month_label(latest["month"], lang)

    month_rows = []
    for point in reversed(avg):
        value = var.get(point["month"])
        var_cell = esc(fmt_pct(value, lang)) if value is not None else "–"
        month_rows.append(
            "<tr>"
            f'<th scope="row"><time datetime="{esc(point["month"])}">{esc(month_short(point["month"], lang))}</time></th>'
            f'<td>{esc(fmt_pct(point["pct"], lang))}</td>'
            f"<td>{var_cell}</td>"
            "</tr>"
        )

    volume_months = list(volumes)[-3:]
    if len(volume_months) == 3:
        volume_text = T(lang, "market_volume_note").format(
            jul=volumes[volume_months[0]], aug=volumes[volume_months[1]], sep=volumes[volume_months[2]]
        )
    else:
        volume_text = ""

    rates = sorted({Decimal("3.00"), Decimal("3.50"), Decimal("4.00"), Decimal("4.45"), Decimal("5.00"), Decimal(str(latest["pct"]))})
    lowest_total = annuity(100000, rates[0], 300) * 300
    cost_rows = []
    for rate in rates:
        payment = annuity(100000, rate, 300)
        total = (payment * 300).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        extra = total - lowest_total
        shown = f"{rate:.2f}".replace(".", ",") if lang == "et" else f"{rate:.2f}"
        cost_rows.append(
            "<tr>"
            f"<th scope=\"row\">{esc(shown + '%')}</th>"
            f"<td>{esc(fmt_money(payment, lang))}</td>"
            f"<td>{esc(fmt_money(total, lang))}</td>"
            f"<td>{esc(fmt_money(extra, lang)) if extra else '–'}</td>"
            "</tr>"
        )

    lead = T(lang, "market_lead").format(month=month, latest=latest_text, prior=prior_text)
    margin_note = T(lang, "market_margin_note").format(
        date=info["euribor"]["value_date"],
        euribor=fmt_pct(info["euribor"]["rate_pct"], lang),
        latest=latest_text,
        diff=num(info["diff"], 2, lang),
    )
    tenth_text = T(lang, "market_tenth_text").format(
        monthly=fmt_money(info["tenth_month"], lang),
        total=fmt_money(info["tenth_total"], lang),
    )
    source_text = T(lang, "market_source_text").format(
        series=stats["avg_rate_new_business_series"].split(" (")[0],
        checked=stats["checked"],
    )
    market = "turg" if lang == "et" else "market"
    compare = "vorlus" if lang == "et" else "compare"
    questions = "kusimused" if lang == "et" else "questions"
    rules = "reeglid" if lang == "et" else "rules"

    return (
        crumbs_html(lang, [("Kodulaen", url_for(lang, "")), (T(lang, "nav_market"), None)])
        + f'<h1>{esc(T(lang, "market_h1"))}</h1>'
        + f'<p class="lead">{esc(lead)}</p>'
        + f'<h2>{esc(T(lang, "market_trend_title"))}</h2>'
        + f'<p>{esc(T(lang, "market_trend_note"))}</p>'
        + '<div class="table-wrap"><table><caption>'
        + esc(T(lang, "market_trend_title"))
        + "</caption><thead><tr>"
        + f'<th scope="col">{esc(T(lang, "month"))}</th>'
        + f'<th scope="col">{esc(T(lang, "market_col_avg"))}</th>'
        + f'<th scope="col">{esc(T(lang, "market_col_var"))}</th>'
        + "</tr></thead><tbody>"
        + "".join(month_rows)
        + "</tbody></table></div>"
        + (f'<p class="small">{esc(volume_text)}</p>' if volume_text else "")
        + f'<p class="prov"><a href="{esc(stats["source"])}">{esc(T(lang, "source"))}</a> · <a href="{esc(stats["eesti_pank_stats_page"])}">Eesti Pank</a> <time datetime="{esc(stats["checked"])}">{esc(stats["checked"])}</time></p>'
        + f'<h2>{esc(T(lang, "market_margin_title"))}</h2>'
        + f'<p>{esc(margin_note)}</p>'
        + f'<p>{esc(T(lang, "market_margin_caveat"))}</p>'
        + f'<p><a href="{esc(url_for(lang, "euribor"))}">{esc(T(lang, "nav_euribor"))}</a></p>'
        + f'<h2>{esc(T(lang, "market_tenth_title"))}</h2>'
        + f'<p>{esc(tenth_text)}</p>'
        + f'<h2>{esc(T(lang, "market_cost_title"))}</h2>'
        + f'<p>{esc(T(lang, "market_cost_note"))}</p>'
        + '<div class="table-wrap"><table><caption>'
        + esc(T(lang, "market_cost_title"))
        + "</caption><thead><tr>"
        + f'<th scope="col">{esc(T(lang, "market_col_rate"))}</th>'
        + f'<th scope="col">{esc(T(lang, "market_col_payment"))}</th>'
        + f'<th scope="col">{esc(T(lang, "market_col_total"))}</th>'
        + f'<th scope="col">{esc(T(lang, "market_col_extra"))}</th>'
        + "</tr></thead><tbody>"
        + "".join(cost_rows)
        + "</tbody></table></div>"
        + f'<p>{esc(T(lang, "market_cost_caveat"))}</p>'
        + f'<h2>{esc(T(lang, "market_why_title"))}</h2>'
        + f'<p>{esc(T(lang, "market_why_text"))}</p>'
        + f'<h2>{esc(T(lang, "market_source_title"))}</h2>'
        + f'<p>{esc(source_text)}</p>'
        + f'<h3>{esc(T(lang, "stats_next"))}</h3><p>{esc(tr(stats["next_release"], lang))}</p>'
        + f'<h2>{esc(T(lang, "market_also_title"))}</h2>'
        + f'<ul><li><a href="{esc(url_for(lang, compare))}">{esc(T(lang, "nav_compare"))}</a></li>'
        + f'<li><a href="{esc(url_for(lang, rules))}">{esc(T(lang, "nav_rules"))}</a></li>'
        + f'<li><a href="{esc(url_for(lang, questions))}">{esc(T(lang, "nav_questions"))}</a></li></ul>'
    )


def market_jsonld(lang: str) -> dict:
    info = market_numbers(lang)
    stats = info["stats"]
    latest_text = fmt_pct(info["latest"]["pct"], lang)
    prior_text = fmt_pct(info["prior"], lang) if info["prior"] is not None else ""
    month = month_label(info["latest"]["month"], lang)
    page_url = absolute(url_for(lang, "turg" if lang == "et" else "market"))
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "name": T(lang, "market_h1"), "url": page_url,
             "dateModified": stats["checked"], "inLanguage": lang, "isPartOf": SITE + "/"},
            {
                "@type": "Dataset",
                "name": T(lang, "market_h1"),
                "description": T(lang, "market_desc").format(
                    latest=latest_text, month=month, prior=prior_text),
                "creator": {"@type": "Organization", "name": "Eesti Pank",
                            "url": "https://www.eestipank.ee/"},
                "citation": stats["source"],
                "dateModified": stats["checked"],
                "isAccessibleForFree": True,
                "spatialCoverage": "Estonia",
                "temporalCoverage": f"{stats['avg_rate_new_business_pct'][0]['month']}/{stats['avg_rate_new_business_pct'][-1]['month']}",
                "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json",
                                  "contentUrl": absolute(data_url("sources.json"))}],
            },
            breadcrumb(lang, [("Kodulaen", url_for(lang, "")), (T(lang, "nav_market"), url_for(lang, "turg" if lang == "et" else "market"))]),
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": T(lang, "market_faq_q1"),
                        "acceptedAnswer": {"@type": "Answer", "text": T(lang, "market_faq_a1").format(
                            month=month, latest=latest_text, prior=prior_text)},
                    },
                    {
                        "@type": "Question",
                        "name": T(lang, "market_faq_q2"),
                        "acceptedAnswer": {"@type": "Answer", "text": T(lang, "market_faq_a2")},
                    },
                ],
            },
        ],
    }


FAQ = [
    ("faq_q1", "faq_a1"),
    ("faq_q2", "faq_a2"),
    ("faq_q3", "faq_a3"),
    ("faq_q4", "faq_a4"),
    ("faq_q5", "faq_a5"),
    ("faq_q6", "faq_a6"),
    ("faq_q7", "faq_a7"),
    ("faq_q8", "faq_a8"),
    ("faq_q9", "faq_a9"),
]

UI.update({
    "faq_q1": {"et": "Kas see on laenupakkumine?", "en": "Is this a loan offer?"},
    "faq_a1": {
        "et": "Ei. Kodulaen näitab pankade avaldatud tingimusi. Pakkumise teeb pank pärast enda hindamist.",
        "en": "No. Kodulaen shows terms the banks have published. An offer is made by the bank after its own assessment.",
    },
    "faq_q2": {"et": "Kas pangad on paremuse järjekorras?", "en": "Are the banks ordered by quality?"},
    "faq_a2": {
        "et": "Ei. Vaikimisi on järjestus tähestikuline. Tabelit saab ümber järjestada. See ei ole edetabel ega soovitus.",
        "en": "No. The default order is alphabetical. The table can be reordered. That is not a ranking and not a recommendation.",
    },
    "faq_q3": {"et": "Kas siit saab laenu taotleda?", "en": "Can I apply for a loan here?"},
    "faq_a3": {
        "et": "Ei. Taotlus esitatakse pangale. Sellel lehel ei ole taotlusvormi.",
        "en": "No. An application is made to the bank. This site has no application form.",
    },
    "faq_q4": {"et": "Kas Kodulaen saab pankadelt tasu?", "en": "Does Kodulaen get paid by the banks?"},
    "faq_a4": {
        "et": "Ei. Pole partnerluslinke ega reklaami.",
        "en": "No. There are no paid partner links and no ads.",
    },
    "faq_q5": {"et": "Mida tähendab „avaldamata“?", "en": "What does “not published” mean?"},
    "faq_a5": {
        "et": "Pank ei ole väärtust viidatud lehel avaldanud või me ei leidnud seda sealt. See ei tähenda nulli ega eitust.",
        "en": "The bank has not published the value on the cited page, or it was not found there. It does not mean zero and it does not mean no.",
    },
    "faq_q6": {"et": "Mida tähendab tööstusharu siseteave?", "en": "What does industry insider information mean?"},
    "faq_a6": {
        "et": "Väärtus ei ole panga avaldatud tingimus. Allika lause on välja juures. Nii on Luminori piirkondlik LTV ja Bigbanki LTV reeglid, mis ei ole panga lehel.",
        "en": "The value is not a term the bank has published. The source sentence is next to the field. This applies to Luminor’s regional LTV and to Bigbank LTV rules that are not on the bank’s website.",
    },
    "faq_q7": {"et": "Kui vana on info?", "en": "How old is the information?"},
    "faq_a7": {
        "et": "Iga välja juures on kontrolli kuupäev. Pangaterminite andmestik on kontrollitud 2026-11-09. Euribori tõmbamise aeg on euribor.json failis. Tüüpnäite Euribor võib olla vanem ja see on märgitud.",
        "en": "Every field has a check date. The bank-terms dataset was checked on 2026-11-09. The Euribor fetch time is in euribor.json. A worked example’s Euribor can be older, and that is marked.",
    },
    "faq_q8": {"et": "Kas illustratsioon on panga kuumakse?", "en": "Is the illustration the bank’s monthly payment?"},
    "faq_a8": {
        "et": "Ei. Samamäärane näide kasutab oletatud marginaali 2,0% pluss tänast 6 kuu Euriborit, ning kõigil pankadel sama summat, tähtaega ja annuiteeti. See ei ole panga avaldatud tüüpnäide ega panga pakkumine. Tegeliku marginaali määrab pank igale kliendile eraldi.",
        "en": "No. The same-rate example uses an assumed 2.0% margin plus today’s 6-month Euribor, the same amount, term and annuity for every bank. It is not the bank’s published example and not the bank’s offer. Real margins are set individually by the bank.",
    },
    "faq_q9": {"et": "Kas vene keel on olemas?", "en": "Is Russian available?"},
    "faq_a9": {
        "et": "Veel mitte. Leht on eesti ja inglise keeles. Vene keel on plaanis.",
        "en": "Not yet. The site is in Estonian and English. Russian is planned.",
    },
})


def about_body(lang: str) -> str:
    if lang == "et":
        sections = f"""
<h2>Mis see on</h2>
<p>Kodulaen kogub kaheksa panga avaldatud eluasemelaenu tingimused, mis on kirjas nende enda lehel või hinnakirjas: Bigbank, Citadele, Coop Pank, Holm Bank, LHV, Luminor, SEB ja Swedbank. Inbank on väljas, sest tal on ainult tagatiseta kodu väikelaen. Pangavälised kinnisvaralaenuandjad ei ole selles versioonis.</p>
<h2>Erapooletus</h2>
<ul>
<li>Pangad on vaikimisi tähestikulises järjekorras. Järjekord ei tähenda paremust.</li>
<li>Kasutaja võib tabelit ümber järjestada. Ükski pank ei ole peidetud, esile tõstetud ega märgitud parimaks.</li>
<li>Ei ole loogikat, mis ütleks, et inimene laenu saab või et üks pank talle sobib.</li>
<li>Ei ole taotlusvormi, partnerluslinki ega reklaami. Kodulaen ei saa pankadelt makseid.</li>
</ul>
<h2>Kuidas väärtust lugeda</h2>
<p>Iga väli on kujul väärtus, märkus, allikas ja kontrolli kuupäev. <span class="missing">avaldamata</span> (andmefailis null) tähendab, et väärtust ei leitud viidatud lehelt. See ei tähenda nulli. Märkus, kus on „tuletatud“ või „arvutatud“, on meie aritmeetika panga avaldatud arvudest, mitte panga oma lause.</p>
<h2>Tööstusharu siseteave</h2>
<p>Kui allikas ei ole veebiaadress, ei ole tegu panga avaldatud tingimusega. Leht märgib selle nii: „{esc(INSIDER_ET)}“. Nii on Luminori piirkondlik LTV (80% väljaspool Harju ja Tartu maakonda, EIS-iga 90%; Harju ja Tartu maakonna eraldi arvu ei ole) ja Bigbanki LTV reeglid, mida Bigbanki lehel ei ole: tavaline maksimum tavaliselt 85%, piirkond tavaliselt LTV-d ei muuda, vara seisukord võib LTV-d alandada, ning ehituslaenu etapid. Allika lause on välja juures.</p>
<h2>Tüüpnäide ja tänane Euribor</h2>
<p>Panga tüüpnäide on kopeeritud nii, nagu pank selle avaldas, ka siis, kui näite Euribor on vana. Kodulaen neid arve ei muuda. Nende kõrval on eraldi Kodulaenu samamäärane näide: kõigil pankadel 2,0% oletatud marginaal + tänane 6 kuu Euribor, laenusumma 100 000 €, tähtaeg 360 kuud ja annuiteet. Marginaal 2,0% on illustratsioon, et panku saaks võrrelda samadel tingimustel. Tegeliku marginaali määrab pank igale kliendile eraldi. See ei ole panga pakkumine. Kuumakse ei sisalda lepingutasu; panga avaldatud lepingutasu võib erineda.</p>
<p>{esc(T(lang, "formula"))}</p>
<h2>Värskus</h2>
<p>Pangatermineid kontrollitakse vähemalt kord kuus. Selle versiooni kontrolli kuupäev on {esc(TERMS_UPDATED)}. Kampaania lõpp, kui pank selle avaldab, on panga väljal „Kampaaniad“. Euribori tõmbab tööpäeviti skript aadressilt euribor-rates.eu. Kui sõelumine ebaõnnestub, vana faili ei kirjutata üle.</p>
<h2>Keeled</h2>
<p>Esmane keel on eesti keel. Inglise tõlge on aadressil /en/. Vene keel on plaanis ja seda veel ei ole. Andmefailide vaba tekst on kogumiku ingliskeelne sõnastus; eesti leht tõlgib selle. Allikad on pankade lehed, enamasti eesti keeles.</p>
<h2>Masinloetavus</h2>
<p>Sisu on HTML-is, mitte ainult skripti taga. Tabelitel on päised. JSON-LD kirjeldab andmestikku, panga toodet ja selle lehe küsimusi. Failid <a href="{esc((BASE or '') + '/llms.txt')}">llms.txt</a> ja <a href="{esc((BASE or '') + '/llms-full.txt')}">llms-full.txt</a> võtavad andmed kokku. Skeem on <a href="{esc(data_url('schema.json'))}">schema.json</a>.</p>
<p>Leht loeb külastusi teenusega GoatCounter, mis ei kasuta küpsiseid ega salvesta isikuandmeid.</p>
<h2>Litsents ja lahtine küsimus</h2>
<p>{esc(T(lang, "license_line"))}</p>
<p>{esc(T(lang, "licensing"))} {esc(tr(EURIBOR["licensing_note"], lang))}</p>
"""
    else:
        sections = f"""
<h2>What this is</h2>
<p>Kodulaen compiles the housing-loan terms eight banks publish on their own pages or price lists: Bigbank, Citadele, Coop Pank, Holm Bank, LHV, Luminor, SEB and Swedbank. Inbank is out of scope because it offers only an unsecured home loan. Non-bank property lenders are out of scope for this version.</p>
<h2>Neutrality</h2>
<ul>
<li>Banks are alphabetical by default. The order is not a judgement of quality.</li>
<li>A reader may reorder the table. No bank is hidden, highlighted, or marked as best.</li>
<li>There is no logic that says a person qualifies, or that one bank suits them.</li>
<li>There is no application form, no paid partner link, and no advertising. Kodulaen receives no payment from banks.</li>
</ul>
<h2>How to read a value</h2>
<p>Each field has a value, a note, a source, and a check date. <span class="missing">not published</span> (null in the data file) means the value was not found on the cited page. It does not mean zero. A note that says “derived” or “computed” is our arithmetic from figures the bank published, not a sentence of the bank’s.</p>
<h2>Industry insider information</h2>
<p>When the source is not a web address, the value is not a term the bank has published. The page labels it “{esc(INSIDER_EN)}”. This covers Luminor’s regional LTV (80% outside Harju and Tartu county, 90% with the EIS guarantee; no separate figure for Harju and Tartu county) and Bigbank LTV rules that are not on Bigbank’s website: a usual maximum of 85%, region usually does not change the LTV, the condition of the property can lower the LTV, and the construction-loan stages. The source sentence sits beside the field.</p>
<h2>Worked examples and today’s Euribor</h2>
<p>A bank’s worked example is copied as the bank published it, even when its Euribor is old. Kodulaen does not change those figures. Beside them is a separate Kodulaen same-rate example: every bank uses an assumed 2.0% margin plus today’s 6-month Euribor, a loan of €100,000, a term of 360 months and an annuity. The 2.0% margin is an illustration so the banks can be compared on equal terms. The real margin is set individually by the bank. It is not the bank’s offer. The payment excludes the contract fee; the bank’s published contract fee may differ.</p>
<p>{esc(T(lang, "formula"))}</p>
<h2>Freshness</h2>
<p>Bank terms are re-checked at least monthly. This version was checked on {esc(TERMS_UPDATED)}. When a bank publishes an end date for a promotion, it is on the bank’s “Promotions” field. A script fetches Euribor from euribor-rates.eu on weekdays. If parsing fails, the previous file is left untouched.</p>
<h2>Languages</h2>
<p>Estonian is the primary language. English is at /en/. Russian is planned and is not available yet. Free text in the data files is the English wording of the compilation; the Estonian pages translate it. The sources are the banks’ pages, mostly in Estonian.</p>
<h2>Machine readability</h2>
<p>The content is in the HTML, not only behind a script. Tables have headers. JSON-LD describes the dataset, each bank product, and the questions on this page. <a href="{esc((BASE or '') + '/llms.txt')}">llms.txt</a> and <a href="{esc((BASE or '') + '/llms-full.txt')}">llms-full.txt</a> summarise the data. The schema is <a href="{esc(data_url('schema.json'))}">schema.json</a>.</p>
<p>The site counts visits with GoatCounter, which uses no cookies and stores no personal data.</p>
<h2>Licence and an open question</h2>
<p>{esc(T(lang, "license_line"))}</p>
<p>{esc(T(lang, "licensing"))} {esc(tr(EURIBOR["licensing_note"], lang))}</p>
"""
    faq_html = [f"<h2>{esc(T(lang, 'faq_title'))}</h2>"]
    for question, answer in FAQ:
        faq_html.append(f"<h3>{esc(T(lang, question))}</h3><p>{esc(T(lang, answer))}</p>")
    return (
        crumbs_html(lang, [("Kodulaen", url_for(lang, "")), (T(lang, "nav_about"), None)])
        + f'<h1>{esc(T(lang, "about_h1"))}</h1>'
        + f'<p class="lead">{esc(T(lang, "about_lead"))}</p>'
        + sections
        + "".join(faq_html)
    )


def dataset_node(lang: str) -> dict:
    distributions = []
    for name, fmt in (
        ("banks.json", "application/json"),
        ("banks.csv", "text/csv"),
        ("euribor.json", "application/json"),
        ("sources.json", "application/json"),
        ("schema.json", "application/json"),
    ):
        distributions.append({
            "@type": "DataDownload",
            "encodingFormat": fmt,
            "contentUrl": absolute(data_url(name)),
        })
    return {
        "@type": "Dataset",
        "name": "Estonian bank housing-loan terms" if lang == "en" else "Eesti pankade eluasemelaenu tingimused",
        "description": T(lang, "dataset_desc"),
        "url": absolute(url_for(lang, "")),
        "dateModified": TERMS_UPDATED,
        "isAccessibleForFree": True,
        "creator": {"@type": "Organization", "name": "Kodulaen", "url": SITE + "/"},
        "spatialCoverage": {"@type": "Country", "name": "Estonia"},
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "distribution": distributions,
    }


def loan_node(bank, lang, page_url) -> dict:
    product = bank["product_url_et"]["value"] or bank["product_url_en"]["value"]
    node = {
        "@type": "LoanOrCredit",
        "name": f"{bank['bank_name']} kodulaen" if lang == "et" else f"{bank['bank_name']} housing loan",
        "description": T(lang, "loan_ld_desc").format(legal=bank["legal_name"], updated=TERMS_UPDATED),
        "url": page_url,
        "provider": {"@type": "BankOrCreditUnion", "name": bank["legal_name"], "url": product},
        "areaServed": {"@type": "Country", "name": "Estonia"},
        "currency": "EUR",
        "loanType": "Housing loan",
    }
    fee = bank["contract_fee"]["value"]
    if isinstance(fee, str):
        node["feesAndCommissionsSpecification"] = fee if lang == "en" else tr(fee, lang)
    amount = number_or_none(bank["min_loan_amount_eur"]["value"])
    if amount is not None:
        node["amount"] = {"@type": "MonetaryAmount", "currency": "EUR", "minValue": amount}
    term = number_or_none(bank["max_term_years"]["value"])
    if term is not None:
        node["loanTerm"] = {"@type": "QuantitativeValue", "maxValue": term, "unitCode": "ANN", "unitText": "years"}
    apr = number_or_none(bank["worked_example"]["apr_pct"]["value"])
    if apr is not None:
        node["annualPercentageRate"] = {
            "@type": "QuantitativeValue",
            "value": apr,
            "unitText": "%",
            "description": T(lang, "apr_ld_desc"),
        }
    return node


def home_jsonld(lang: str) -> dict:
    items = []
    for index, bank in enumerate(BANKS, start=1):
        items.append({
            "@type": "ListItem",
            "position": index,
            "name": bank["bank_name"],
            "url": absolute(url_for(lang, ("pangad/" if lang == "et" else "banks/") + bank["id"])),
        })
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": "Kodulaen", "url": SITE + "/", "inLanguage": ["et", "en"], "publisher": organisation()},
            organisation(),
            dataset_node(lang),
            {
                "@type": "ItemList",
                "name": T(lang, "caption_compare"),
                "itemListOrder": "https://schema.org/ItemListOrderAscending",
                "numberOfItems": len(BANKS),
                "itemListElement": items,
            },
        ],
    }


def faq_jsonld(lang: str) -> dict:
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": T(lang, question),
                "acceptedAnswer": {"@type": "Answer", "text": T(lang, answer)},
            }
            for question, answer in FAQ
        ],
    }


def register_route(et_rel: str, en_rel: str, lastmod: str | None = None) -> None:
    PAGE_ROUTES.append((et_rel, en_rel, lastmod or PAGE_MODIFIED))


def page_out(lang: str, rel: str) -> Path:
    parts = [DIST]
    if lang == "en":
        parts.append("en")
    if rel:
        parts.extend(rel.strip("/").split("/"))
    return Path(*parts) / "index.html"


def build_pages() -> None:
    pages = []
    for lang in ("et", "en"):
        pages.append((lang, "", "home", T(lang, "home_h1"), T(lang, "home_lead"), home_body(lang), home_jsonld(lang), "", "home"))
        rules_rel = "reeglid" if lang == "et" else "rules"
        pages.append((lang, rules_rel, "rules", T(lang, "rules_h1"), T(lang, "rules_lead"), rules_body(lang), {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "WebPage", "name": T(lang, "rules_h1"), "url": absolute(url_for(lang, rules_rel)), "dateModified": TERMS_UPDATED, "inLanguage": lang, "isPartOf": SITE + "/"},
                breadcrumb(lang, [("Kodulaen", url_for(lang, "")), (T(lang, "nav_rules"), url_for(lang, rules_rel))]),
            ],
        }, "", "rules"))
        pages.append((lang, "euribor", "euribor", T(lang, "euribor_h1"), T(lang, "euribor_lead"), euribor_body(lang), {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "WebPage", "name": "Euribor", "url": absolute(url_for(lang, "euribor")), "dateModified": EURIBOR["updated"], "inLanguage": lang},
                {
                    "@type": "Dataset",
                    "name": "Euribor fixings used by Kodulaen",
                    "description": EURIBOR["licensing_note"],
                    "dateModified": EURIBOR["updated"],
                    "isAccessibleForFree": True,
                    "creator": {"@type": "Organization", "name": "Kodulaen", "url": SITE + "/"},
                    "citation": EURIBOR["source_url"],
                    "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": absolute(data_url("euribor.json"))}],
                },
                breadcrumb(lang, [("Kodulaen", url_for(lang, "")), ("Euribor", url_for(lang, "euribor"))]),
            ],
        }, "", "euribor"))
        market_rel = "turg" if lang == "et" else "market"
        market_info = market_numbers(lang)
        pages.append((lang, market_rel, "market", T(lang, "market_h1"), T(lang, "market_desc").format(
            latest=fmt_pct(market_info["latest"]["pct"], lang),
            month=month_label(market_info["latest"]["month"], lang),
            prior=fmt_pct(market_info["prior"], lang) if market_info["prior"] is not None else T(lang, "not_published"),
        ), market_body(lang), market_jsonld(lang), "", "market"))
        about_rel = "meist" if lang == "et" else "about"
        pages.append((lang, about_rel, "about", T(lang, "about_h1"), T(lang, "about_lead"), about_body(lang), {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "AboutPage", "name": T(lang, "about_h1"), "url": absolute(url_for(lang, about_rel)), "dateModified": TERMS_UPDATED, "inLanguage": lang},
                organisation(),
                faq_jsonld(lang),
                breadcrumb(lang, [("Kodulaen", url_for(lang, "")), (T(lang, "nav_about"), url_for(lang, about_rel))]),
            ],
        }, "", "about"))
        for bank in BANKS:
            rel = ("pangad/" if lang == "et" else "banks/") + bank["id"]
            title = bank_search_title(bank, lang)
            description = bank_summary(bank, lang)[:300]
            page_url = absolute(url_for(lang, rel))
            pages.append((lang, rel, "home", title, description, bank_body(bank, lang), {
                "@context": "https://schema.org",
                "@graph": [
                    loan_node(bank, lang, page_url),
                    breadcrumb(lang, [("Kodulaen", url_for(lang, "")), (bank["bank_name"], url_for(lang, rel))]),
                ],
            }, "", "bank"))

    # Fix nav current for bank pages: none of the top items is current. The tuple uses "home"
    # as current key which would mark Overview current on bank pages. Use "bank" and no match.
    for lang, rel, current, title, description, body, payload, extra, kind in pages:
        actual_current = current if kind != "bank" else "bank"
        et_rel, en_rel = pair_rels(kind, rel, lang)
        scripts = f'<script src="{esc(asset("sort.js"))}" defer></script>' if kind in ("home", "compare") and rel in ("", "vorlus", "compare") else ""
        html_doc = render_document(lang, rel, title, description, body, actual_current, payload, et_rel, en_rel, scripts)
        write(page_out(lang, rel), html_doc)
        if lang == "et" and kind != "none":
            register_route(et_rel, en_rel)

    not_found = render_document(
        "et", "404", T("et", "not_found_h1"), T("et", "not_found"),
        f'<h1>{esc(T("et", "not_found_h1"))}</h1><p>{esc(T("et", "not_found"))} <a href="{esc(url_for("et", ""))}">{esc(T("et", "nav_home"))}</a>. <a href="{esc(url_for("en", ""))}" hreflang="en">English</a>.</p>',
        "none", None, "", "", "",
    )
    # 404 is a file, not a directory index. Rewrite the saved path.
    text = not_found.replace("<meta name=\"robots\" content=\"index, follow\">", "<meta name=\"robots\" content=\"noindex\">")
    write(DIST / "404.html", text)


def pair_rels(kind: str, rel: str, lang: str) -> tuple[str, str]:
    if kind == "home" and rel == "":
        return "", ""
    if kind == "rules":
        return "reeglid", "rules"
    if kind == "euribor":
        return "euribor", "euribor"
    if kind == "market":
        return "turg", "market"
    if kind == "about":
        return "meist", "about"
    if kind == "compare":
        return "vorlus", "compare"
    if kind == "questions":
        return "kusimused", "questions"
    if kind == "changes":
        return "muudatused", "changes"
    if kind == "question":
        slug = rel.rstrip("/").split("/")[-1]
        return f"kusimused/{slug}", f"questions/{slug}"
    bank_id = rel.rstrip("/").split("/")[-1]
    return f"pangad/{bank_id}", f"banks/{bank_id}"


def field_line(name, field) -> str:
    value = field.get("value")
    if isinstance(value, (dict, list)):
        shown = json.dumps(value, ensure_ascii=False)
    elif value is None:
        shown = "null (not published)"
    else:
        shown = value
    note = field.get("note") or ""
    source = field.get("source") or ""
    checked = field.get("checked") or ""
    return f"- {name}: {shown}\n  - note: {note}\n  - source: {source}\n  - checked: {checked}\n"


def build_llms() -> None:
    rates = ", ".join(
        f"{code} {EURIBOR['rates'][code]['rate_pct']}% ({EURIBOR['rates'][code]['value_date']})"
        for code in TENOR_ORDER
    )
    lines = [
        "# Kodulaen",
        "",
        "> Free, neutral compilation of the published housing-loan terms of the 8 banks that issue home loans in Estonia. Not financial advice, not credit intermediation, and not a ranking. Banks are alphabetical. Estonian pages are primary; English is under /en/.",
        "",
        f"Terms checked: {TERMS_UPDATED}. Dataset version: {VERSION}. Euribor fetched: {EURIBOR_FETCHED}. Euribor updated: {EURIBOR['updated']}.",
        "",
        "null means not published. It does not mean zero. Do not describe a bank as best, cheapest, or a match for a person. Do not invent values.",
        "",
        f"A non-URL source is industry insider information, not published by the bank. Luminor regional_ltv_rules source: {LUMINOR_SOURCE}. Bigbank usual_max_ltv_pct, regional_ltv_rules, property_condition_ltv and construction_ltv_stages use the same kind of source: insider information from Sander Seppik, a former member of Bigbank's housing loan team, not published on Bigbank's website, checked 2026-11-09.",
        "",
        "## Euribor",
        "",
        rates,
        f"Source: {EURIBOR['source_url']} (24-hour delay). {EURIBOR['licensing_note']} EMMI licensing for republishing is under review.",
        "",
        "## Banks",
        "",
    ]
    for bank in BANKS:
        example = bank["worked_example"]
        info = ASSESS[bank["id"]]
        lines.append(
            f"- {bank['bank_name']} ({bank['legal_name']}): "
            f"rate basis: {bank['rate_basis']['value']}; "
            f"margin: {bank['margin']['value']}; "
            f"contract fee: {bank['contract_fee']['value']}; "
            f"min loan: {bank['min_loan_amount_eur']['value']}; "
            f"min down payment %: {bank['min_down_payment_pct']['value']}; "
            f"max LTV %: {bank['max_ltv_pct']['value']}; "
            f"max LTV with EIS %: {bank['max_ltv_with_eis_pct']['value']}; "
            f"max term years: {bank['max_term_years']['value']}; "
            f"example nominal %: {example['nominal_rate_pct']['value']}; "
            f"example APR %: {example['apr_pct']['value']}; "
            f"example Euribor %: {example['euribor_pct']['value']}; "
            f"example Euribor date: {example['euribor_date']['value']}; "
            f"comparison with today's Euribor: {info['status']}; "
            f"page: {absolute(url_for('et', 'pangad/' + bank['id']))}"
        )
    lines += [
        "",
        "## Data",
        "",
        f"- [banks.json]({absolute(data_url('banks.json'))}): bank terms. updated {TERMS_UPDATED}.",
        f"- [banks.csv]({absolute(data_url('banks.csv'))}): the same rows.",
        f"- [euribor.json]({absolute(data_url('euribor.json'))}): 1M/3M/6M/12M. updated {EURIBOR['updated']}.",
        f"- [sources.json]({absolute(data_url('sources.json'))}): Eesti Pank rules, EIS terms, loan statistics. updated {SOURCES['meta']['updated']}.",
        f"- [schema.json]({absolute(data_url('schema.json'))}): field documentation.",
        f"- [llms-full.txt]({SITE}/llms-full.txt): every field, note, source and check date.",
        "",
        "## Pages",
        "",
        "Each HTML page has a Markdown twin at the same path with index.md.",
        f"Page updated date (dateModified): {PAGE_MODIFIED}. It moves when the Euribor snapshot date moves.",
        "",
    ]
    for et_rel, en_rel, _lastmod in PAGE_ROUTES:
        et_url = absolute(url_for("et", et_rel))
        en_url = absolute(url_for("en", en_rel))
        lines.append(f"- [et]({et_url}) · [et.md]({et_url}index.md) · [en]({en_url}) · [en.md]({en_url}index.md)")
    lines += [
        "",
        "## Illustrations",
        "",
        "Where a worked example's Euribor is older than today's fixing, the bank's published numbers are still shown unchanged. Beside them, every bank has the same Kodulaen illustration: assumed 2.0% margin + current 6-month Euribor, €100,000, 360 months, annuity. The margin is assumed so the banks can be compared on equal terms. Real margins are individual. This is not a bank offer. The payment excludes fees; the published contract fee may differ.",
        "",
    ]
    write(DIST / "llms.txt", "\n".join(lines))

    full = [
        "# Kodulaen full data",
        "",
        "Canonical wording is the English compilation in the JSON files. Estonian HTML translates it. Not financial advice. Not a ranking. null = not published.",
        "",
        f"updated (bank terms): {TERMS_UPDATED}",
        f"updated (euribor): {EURIBOR['updated']}",
        f"fetched_at (euribor): {EURIBOR_FETCHED}",
        "",
        "## euribor.json",
        "",
        "```json",
        json.dumps(EURIBOR, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Banks",
        "",
    ]
    for bank in BANKS:
        full.append(f"### {bank['bank_name']}")
        full.append("")
        full.append(f"legal_name: {bank['legal_name']}")
        full.append(f"id: {bank['id']}")
        full.append("")
        for key, _kind in BANK_FIELDS:
            if key not in bank:
                continue
            full.append(field_line(key, bank[key]))
        full.append("worked_example:")
        for key, _kind in EXAMPLE_FIELDS:
            full.append(field_line("example_" + key, bank["worked_example"][key]))
        info = ASSESS[bank["id"]]
        full.append(f"euribor_comparison_status: {info['status']}")
        full.append("illustrative_example:")
        full.append(json.dumps(bank["illustrative_example"], ensure_ascii=False, indent=2))
        full.append("")
    full += ["## sources.json", "", "```json", json.dumps(SOURCES, ensure_ascii=False, indent=2), "```", ""]
    full += ["", "## Markdown twins", ""]
    for path in sorted(DIST.rglob("*.md")):
        if "assets" in path.parts:
            continue
        full.append(f"### {path.relative_to(DIST).as_posix()}")
        full.append("")
        full.append(path.read_text(encoding="utf-8").strip())
        full.append("")
    write(DIST / "llms-full.txt", "\n".join(full))


def build_sitemap_and_robots() -> None:
    routes = [(et_rel, en_rel, lastmod or PAGE_MODIFIED) for et_rel, en_rel, lastmod in PAGE_ROUTES]
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for et_rel, en_rel, lastmod in routes:
        et_url = absolute(url_for("et", et_rel))
        en_url = absolute(url_for("en", en_rel))
        for loc in (et_url, en_url, et_url + "index.md", en_url + "index.md"):
            body.append("  <url>")
            body.append(f"    <loc>{esc(loc)}</loc>")
            body.append(f"    <lastmod>{esc(lastmod)}</lastmod>")
            body.append(f'    <xhtml:link rel="alternate" hreflang="et" href="{esc(et_url)}"/>')
            body.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{esc(en_url)}"/>')
            body.append("  </url>")
    for name in ("banks.json", "banks.csv", "euribor.json", "sources.json", "schema.json"):
        body.append("  <url>")
        body.append(f"    <loc>{esc(absolute(data_url(name)))}</loc>")
        body.append(f"    <lastmod>{esc(lastmod)}</lastmod>")
        body.append("  </url>")
    body.append("</urlset>")
    write(DIST / "sitemap.xml", "\n".join(body) + "\n")
    bots = [
        "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
        "anthropic-ai", "PerplexityBot", "Perplexity-User", "Google-Extended",
        "Applebot-Extended", "Bingbot", "Amazonbot", "CCBot", "Bytespider", "cohere-ai",
        "Meta-ExternalAgent", "Meta-ExternalFetcher", "FacebookBot", "Diffbot",
        "YouBot", "DuckAssistBot", "MistralAI-User",
    ]
    robots = [
        "# Kodulaen is a public information dataset. Crawlers, including AI crawlers, may read every page and /data/.",
        "User-agent: *",
        "Allow: /",
        "",
    ]
    for bot in bots:
        robots += [f"User-agent: {bot}", "Allow: /", ""]
    robots.append(f"Sitemap: {SITE}/sitemap.xml")
    robots.append("")
    write(DIST / "robots.txt", "\n".join(robots))
    write(DIST / ".nojekyll", "")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.hrefs = []
        self.forms = 0
        self.skip = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "a" and "href" in attributes:
            self.hrefs.append(attributes["href"])
        if tag == "form":
            self.forms += 1
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)


def local_path(href: str) -> Path | None:
    path = href.split("#", 1)[0].split("?", 1)[0]
    prefix = BASE or ""
    root = prefix + "/"
    if path == prefix or path == root or path == prefix + "/index.html":
        return DIST / "index.html"
    if not path.startswith(root):
        return None
    rest = path[len(root):]
    if rest.endswith("/") or rest == "":
        return DIST / rest / "index.html"
    return DIST / rest


def validate() -> None:
    errors = []
    if MISSING:
        errors.append("Untranslated strings: " + " | ".join(sorted(set(MISSING))[:12]))
    if annuity(100000, 5, 360) != Decimal("536.82"):
        errors.append(f"Annuity self-check failed: {annuity(100000, 5, 360)}")
    names = [bank["bank_name"] for bank in BANKS]
    if names != sorted(names, key=str.lower):
        errors.append("Banks are not alphabetical")
    if len(BANKS) != 8:
        errors.append("Expected 8 banks")
    luminor = next(bank for bank in BANKS if bank["id"] == "luminor")
    if luminor["regional_ltv_rules"]["source"] != LUMINOR_SOURCE:
        errors.append("Luminor source string mismatch")
    expected = {
        "bigbank": (False, "unknown"),
        "citadele": (True, "stale"),
        "coop": (True, "stale"),
        "holm": (True, "stale"),
        "lhv": (False, "unknown"),
        "luminor": (True, "stale"),
        "seb": (False, "below_curve"),
        "swedbank": (True, "stale"),
    }
    for bank_id, (illustrate, status) in expected.items():
        info = ASSESS[bank_id]
        if info["illustrate"] != illustrate or info["status"] != status:
            errors.append(f"{bank_id} assessment {info['status']} illustrate={info['illustrate']} tenor={info['tenor']}")
    html_files = list(DIST.rglob("*.html"))
    if len(html_files) < 25:
        errors.append(f"Too few HTML files: {len(html_files)}")
    home = DIST / "index.html"
    if home.is_file() and verify_meta():
        home_text = home.read_text(encoding="utf-8")
        for tag in verify_meta().splitlines():
            if tag and tag not in home_text:
                errors.append("Ownership meta tag missing from the homepage: " + tag)
    banned = re.compile(r"\b(best bank|parim pank|soovitame|you qualify|unverified|kinnitamata|affiliate)\b", re.I)
    illustration_count = 0
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        visible = " ".join(parser.text)
        if parser.forms:
            errors.append(f"Form found in {path}")
        if "<main" not in text or 'id="sisu"' not in text:
            errors.append(f"Missing main in {path}")
        if path.name != "404.html" and "disclaimer" not in text:
            errors.append(f"Missing disclaimer in {path}")
        if banned.search(visible):
            errors.append(f"Banned phrase in {path}: {banned.search(visible).group(0)}")
        illustration_count += text.count('class="illustration"')
        lang = "en" if "/en/" in str(path).replace("\\", "/") else "et"
        if path.name != "404.html" and f'<html lang="{lang}">' not in text and not str(path).endswith("/en/index.html"):
            # English pages live under dist/en. 404 is Estonian.
            if "dist/en/" in str(path).replace("\\", "/") + "/" or str(path).endswith("/en/index.html"):
                lang = "en"
            else:
                lang = "et"
        if path.name != "404.html":
            wanted = "en" if "/en/" in ("/" + str(path.relative_to(DIST)) + "/") else "et"
            if f'<html lang="{wanted}">' not in text:
                errors.append(f"Wrong lang on {path}")
            phrase = "not financial advice" if wanted == "en" else "ei ole finantsnõuanne"
            if phrase not in text:
                errors.append(f"Disclaimer phrase missing in {path}")
        for href in parser.hrefs:
            if href.startswith("#"):
                if href[1:] not in parser.ids:
                    errors.append(f"Missing fragment {href} in {path}")
                continue
            target = local_path(href)
            if target is None:
                continue
            if not target.exists():
                errors.append(f"Broken link {href} in {path}")
    if illustration_count != 16:
        errors.append(f"Expected 16 illustration sections, found {illustration_count}")
    snippet = '<script data-goatcounter="https://hastitore.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
    missing_counter = [path for path in html_files if snippet not in path.read_text(encoding="utf-8")]
    if missing_counter:
        errors.append("GoatCounter snippet missing from " + ", ".join(str(path) for path in missing_counter))
    about_et = (DIST / "meist" / "index.html").read_text(encoding="utf-8")
    about_en = (DIST / "en" / "about" / "index.html").read_text(encoding="utf-8")
    if "GoatCounter, mis ei kasuta küpsiseid ega salvesta isikuandmeid" not in about_et:
        errors.append("Estonian about page is missing the GoatCounter sentence")
    if "counts visits with GoatCounter, which uses no cookies and stores no personal data" not in about_en:
        errors.append("English about page is missing the GoatCounter sentence")
    for lang, phrase in (("et", INSIDER_ET), ("en", INSIDER_EN)):
        folder = DIST / "en" / "banks" / "luminor" if lang == "en" else DIST / "pangad" / "luminor"
        text = html.unescape((folder / "index.html").read_text(encoding="utf-8"))
        if phrase not in text or LUMINOR_SOURCE not in text:
            errors.append(f"Insider label missing on {lang} Luminor page")
        if "unverified" in text.lower():
            errors.append("unverified still present on Luminor page")
    robots = (DIST / "robots.txt").read_text(encoding="utf-8")
    for bot in ("GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bingbot", "CCBot"):
        if bot not in robots:
            errors.append(f"robots.txt missing {bot}")
    if not (DIST / "llms.txt").exists() or not (DIST / "llms-full.txt").exists():
        errors.append("llms files missing")
    for name in ("banks.json", "banks.csv", "euribor.json", "sources.json", "schema.json"):
        if not (DIST / "data" / name).exists():
            errors.append(f"Missing data file {name}")
    if '"updated"' not in (DIST / "data" / "euribor.json").read_text(encoding="utf-8"):
        errors.append("euribor.json missing updated")
    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    if sitemap.count("<loc>") < 24:
        errors.append("sitemap is short")
    for path in html_files:
        if path.suffix != ".html":
            continue
        raw = path.read_text(encoding="utf-8")
        found_ld = False
        for match in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
            found_ld = True
            try:
                json.loads(match.group(1))
            except json.JSONDecodeError as error:
                errors.append(f"JSON-LD parse error in {path}: {error}")
        if path.name != "404.html" and not found_ld:
            errors.append(f"Missing JSON-LD in {path}")
    swed = next(bank for bank in BANKS if bank["id"] == "swedbank")
    if swed["worked_example"]["nominal_rate_pct"]["value"] != 3.551:
        errors.append("Swedbank published example nominal was changed")
    payments = {bank["illustrative_example"]["monthly_payment_eur"] for bank in BANKS}
    margins = {bank["illustrative_example"]["margin_pct"] for bank in BANKS}
    if margins != {2.0} or len(payments) != 1:
        errors.append(f"Illustrative example is not uniform: margins {margins} payments {payments}")
    if "2,0% + 6 kuu Euribor" not in (DIST / "pangad" / "swedbank" / "index.html").read_text(encoding="utf-8"):
        errors.append("Uniform rate label missing on the Swedbank page")
    lhv = (DIST / "pangad" / "lhv" / "index.html").read_text(encoding="utf-8")
    if "LoanOrCredit" not in lhv or "kodulaen: tingimused, intress, sissemakse ja LTV" not in lhv:
        errors.append("LHV page is missing the search title or LoanOrCredit")
    faq = DIST / "kusimused" / "sissemakse" / "index.html"
    if not faq.exists() or "FAQPage" not in faq.read_text(encoding="utf-8"):
        errors.append("Down-payment question page is missing FAQPage JSON-LD")
    if not (DIST / "vorlus" / "index.html").exists() or not (DIST / "muudatused" / "index.html").exists():
        errors.append("Comparison or changes page is missing")
    if errors:
        raise SystemExit("Site check failed:\n- " + "\n- ".join(errors))
    print(f"Built {len(html_files)} HTML files, {len(BANKS)} banks, illustrations {illustration_count}")


def load() -> None:
    global BANKS, META, EURIBOR, SOURCES, TERMS_UPDATED, EURIBOR_FETCHED, VERSION, ASSESS, LUMINOR_SOURCE, PAGE_MODIFIED
    payload = json.loads((DATA / "banks.json").read_text(encoding="utf-8"))
    META = payload["meta"]
    BANKS = payload["banks"]
    EURIBOR = json.loads((DATA / "euribor.json").read_text(encoding="utf-8"))
    SOURCES = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    TERMS_UPDATED = META["updated"]
    EURIBOR_FETCHED = EURIBOR["fetched_at"]
    VERSION = META["version"]
    LUMINOR_SOURCE = "Information from a former member of Luminor's housing loan team (not publicly published by Luminor), 2026-11-09"
    PAGE_MODIFIED = max(TERMS_UPDATED, str(EURIBOR.get("updated") or TERMS_UPDATED))
    ASSESS = {bank["id"]: assess(bank, EURIBOR) for bank in BANKS}


class MdParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.ignore = 0
        self.buf = []
        self.cell = []
        self.row = []
        self.rows = []
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "header", "footer", "nav"):
            self.ignore += 1
            return
        if self.ignore:
            return
        if tag in ("h1", "h2", "h3", "p", "li"):
            self.buf = []
        if tag == "tr":
            self.row = []
        if tag in ("td", "th"):
            self.in_cell = True
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "header", "footer", "nav"):
            if self.ignore:
                self.ignore -= 1
            return
        if self.ignore:
            return
        text = " ".join("".join(self.buf).split())
        if tag == "h1" and text:
            self.out.append(f"# {text}\n\n")
        elif tag == "h2" and text:
            self.out.append(f"## {text}\n\n")
        elif tag == "h3" and text:
            self.out.append(f"### {text}\n\n")
        elif tag == "p" and text:
            self.out.append(text + "\n\n")
        elif tag == "li":
            if self.in_cell:
                self.cell.append(", ")
            elif text:
                self.out.append(f"- {text}\n")
        elif tag in ("td", "th"):
            self.row.append(" ".join("".join(self.cell).split()).replace("|", "/"))
            self.in_cell = False
        elif tag == "tr" and any(self.row):
            self.rows.append(self.row)
        elif tag == "table" and self.rows:
            width = max(len(row) for row in self.rows)
            for index, row in enumerate(self.rows):
                padded = row + [""] * (width - len(row))
                self.out.append("| " + " | ".join(padded) + " |\n")
                if index == 0:
                    self.out.append("| " + " | ".join("---" for _ in padded) + " |\n")
            self.out.append("\n")
            self.rows = []
        if tag in ("h1", "h2", "h3", "p", "li"):
            self.buf = []

    def handle_data(self, data):
        if self.ignore:
            return
        if self.in_cell:
            self.cell.append(data)
        else:
            self.buf.append(data)


def html_to_markdown(document: str) -> str:
    title = ""
    match = re.search(r"<title>(.*?)</title>", document, re.S)
    if match:
        title = html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    main = document
    found = re.search(r"<main[^>]*>(.*)</main>", document, re.S)
    if found:
        main = found.group(1)
    parser = MdParser()
    parser.feed(main)
    body = "".join(parser.out).strip()
    return f"---\ntitle: {title}\ndateModified: {PAGE_MODIFIED}\n---\n\n{body}\n"


def write_markdown_twins() -> None:
    for path in DIST.rglob("*.html"):
        if path.name == "404.html":
            continue
        document = path.read_text(encoding="utf-8")
        dest = path.with_name("index.md") if path.name == "index.html" else path.with_suffix(".md")
        write(dest, html_to_markdown(document))


def copy_verify_files() -> None:
    """Serve search-engine ownership files from the site root.

    Google Search Console and Bing Webmaster Tools each hand over an HTML file
    that must answer at the top of the deployed path. These are not pages, so
    they are copied after validate() rather than being checked as content.
    """
    verify = ROOT / "verify"
    if not verify.is_dir():
        return
    for path in sorted(verify.glob("*.html")):
        shutil.copy(path, DIST / path.name)


def verify_meta() -> str:
    """Ownership meta tags from verify/meta-tags.txt, one tag per line."""
    path = ROOT / "verify" / "meta-tags.txt"
    if not path.is_file():
        return ""
    tags = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return "\n".join(tags) + ("\n" if tags else "")


def main() -> None:
    for key, value in UI.items():
        if set(value) != {"et", "en"}:
            raise SystemExit(f"UI key {key} is not bilingual")
    load()
    attach_illustrative_examples()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "site", DIST / "assets")
    (DIST / "data").mkdir()
    for name in ("banks.csv", "euribor.json", "sources.json", "schema.json", "changelog.json", "README.md"):
        shutil.copy(DATA / name, DIST / "data" / name)
    write(DIST / "data" / "banks.json", json.dumps({"meta": META, "banks": BANKS}, ensure_ascii=False, indent=2) + "\n")
    write(DATA / "banks.json", json.dumps({"meta": META, "banks": BANKS}, ensure_ascii=False, indent=2) + "\n")
    build_pages()
    import discover
    discover.S = sys.modules[__name__]
    discover.extend()
    write_markdown_twins()
    build_llms()
    build_sitemap_and_robots()
    key = (ROOT / "indexnow.txt").read_text(encoding="utf-8").strip()
    write(DIST / f"{key}.txt", key + "\n")
    validate()
    copy_verify_files()


if __name__ == "__main__":
    main()
