"""Question, comparison, and changelog pages. Imported after build_site helpers exist."""
import json

S = None


def field_cell(field, lang, kind):
    if field is None:
        return S.missing_html(lang)
    return S.compact_value(field, lang, kind)


def simple_table(lang, caption, headers, rows):
    head = "".join(f'<th scope="col">{S.esc(header)}</th>' for header in headers)
    body = []
    for row in rows:
        cells = []
        for index, cell in enumerate(row):
            if index == 0:
                cells.append(f'<th scope="row">{cell}</th>')
            else:
                cells.append(f"<td>{cell}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="table-wrap"><table>'
        f"<caption>{S.esc(caption)}</caption>"
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def bank_link(bank, lang):
    rel = ("pangad/" if lang == "et" else "banks/") + bank["id"]
    return f'<a href="{S.esc(S.url_for(lang, rel))}">{S.esc(bank["bank_name"])}</a>'


def names_group(bank, code, lang):
    programs = bank["eis_programs"]["value"]
    if programs is None:
        return S.esc(S.T(lang, "does_not_itemise"))
    if code in programs:
        return S.esc(S.T(lang, "names"))
    return S.esc(S.T(lang, "does_not_name"))


def mentions(bank, needles):
    types = bank["loan_types"]["value"] or []
    text = " ".join(types).lower()
    return any(needle in text for needle in needles)


def lead_and_table(lang, title, lead, caption, headers, rows, source_html):
    return (
        S.crumbs_html(lang, [("Kodulaen", S.url_for(lang, "")), (S.T(lang, "nav_questions"), S.url_for(lang, "kusimused" if lang == "et" else "questions")), (title, None)])
        + f"<h1>{S.esc(title)}</h1>"
        + f'<p class="lead">{S.esc(lead)}</p>'
        + f'<p class="small">{S.esc(S.T(lang, "page_updated"))} <time datetime="{S.esc(S.PAGE_MODIFIED)}">{S.esc(S.PAGE_MODIFIED)}</time>. '
        + f'{S.esc(S.T(lang, "read_alpha"))}</p>'
        + simple_table(lang, caption, headers, rows)
        + source_html
    )


def down_payment(lang):
    rules = S.SOURCES["eesti_pank_lending_rules"]
    eis = S.SOURCES["eis_housing_loan_guarantee"]
    if lang == "et":
        title = "Kui suur on kodulaenu sissemakse? (2026)"
        lead = (
            f"Eesti Panga piirang on kuni {S.fmt_pct(rules['max_ltv_pct'], lang)} tagatisest "
            f"(omafinantseering vähemalt {S.fmt_pct(100 - rules['max_ltv_pct'], lang)}) ja riigi käendusega kuni "
            f"{S.fmt_pct(rules['max_ltv_state_guaranteed_pct'], lang)}. EIS-i eluasemelaenu käendusel on minimaalne "
            f"omafinantseering {S.fmt_pct(eis['min_down_payment_pct'], lang)}, lasterikkal perel "
            f"{S.fmt_pct(eis['min_down_payment_large_family_pct'], lang)}. Pankade enda avaldatud miinimumid on tabelis."
        )
        headers = ["Pank", "Minimaalne sissemakse", "Max LTV", "Max LTV EIS-iga"]
        caption = "Pankade avaldatud sissemakse ja LTV. Tähestikuline järjekord."
    else:
        title = "How large is the housing-loan down payment? (2026)"
        lead = (
            f"Eesti Pank's limit is {S.fmt_pct(rules['max_ltv_pct'], lang)} of the collateral "
            f"(down payment at least {S.fmt_pct(100 - rules['max_ltv_pct'], lang)}) and "
            f"{S.fmt_pct(rules['max_ltv_state_guaranteed_pct'], lang)} with a state guarantee. "
            f"Under the EIS housing-loan guarantee the minimum down payment is {S.fmt_pct(eis['min_down_payment_pct'], lang)}, "
            f"and {S.fmt_pct(eis['min_down_payment_large_family_pct'], lang)} for a large family. "
            f"Each bank's published minimum is in the table."
        )
        headers = ["Bank", "Minimum down payment", "Max LTV", "Max LTV with EIS"]
        caption = "Published down payment and LTV. Alphabetical order."
    rows = []
    for bank in S.BANKS:
        rows.append([
            bank_link(bank, lang),
            field_cell(bank["min_down_payment_pct"], lang, "pct"),
            field_cell(bank["max_ltv_pct"], lang, "pct"),
            field_cell(bank["max_ltv_with_eis_pct"], lang, "pct"),
        ])
    sources = (
        f'<p class="prov"><a href="{S.esc(rules["source"])}">{S.esc(S.T(lang, "source"))}</a> '
        f'<time datetime="{S.esc(rules["checked"])}">{S.esc(rules["checked"])}</time> · '
        f'<a href="{S.esc(eis["source"])}">EIS</a> <time datetime="{S.esc(eis["checked"])}">{S.esc(eis["checked"])}</time></p>'
    )
    return title, lead, lead_and_table(lang, title, lead, caption, headers, rows, sources)


def eis_groups(lang):
    eis = S.SOURCES["eis_housing_loan_guarantee"]
    young = eis["target_groups"]["young_family"]
    specialist = eis["target_groups"]["young_specialist"]
    if lang == "et":
        title = "EIS ja KredExi käendus noorele perele ja noorele spetsialistile (2026)"
        lead = (
            f"EIS-i eluasemelaenu käendust taotletakse panga kaudu; EISile eraldi avaldust ei saadeta. "
            f"Noor pere: {S.tr(young, lang)}. Noor spetsialist: {S.tr(specialist, lang)}. "
            f"Minimaalne omafinantseering on {S.fmt_pct(eis['min_down_payment_pct'], lang)}, lasterikkal perel "
            f"{S.fmt_pct(eis['min_down_payment_large_family_pct'], lang)}. Tasu: {S.tr(eis['fee'], lang)}. "
            f"Kodulaen ei otsusta, kas inimene sihtrühma kuulub."
        )
        headers = ["Pank", "Noor pere", "Noor spetsialist", "EIS-i käendus"]
        caption = "Kas pank oma lehel sihtrühma nimetab. See ei ole hinnang."
    else:
        title = "EIS and KredEx guarantee for a young family and a young specialist (2026)"
        lead = (
            f"The EIS housing-loan guarantee is requested through the bank; there is no separate application to EIS. "
            f"Young family: {young}. Young specialist: {specialist}. "
            f"The minimum down payment is {S.fmt_pct(eis['min_down_payment_pct'], lang)}, and "
            f"{S.fmt_pct(eis['min_down_payment_large_family_pct'], lang)} for a large family. Fee: {eis['fee']}. "
            f"Kodulaen does not decide whether a person belongs to a target group."
        )
        headers = ["Bank", "Young family", "Young specialist", "EIS guarantee"]
        caption = "Whether the bank names the target group on its own page. This is not a judgement."
    rows = []
    for bank in S.BANKS:
        rows.append([
            bank_link(bank, lang),
            names_group(bank, "young_family", lang),
            names_group(bank, "young_specialist", lang),
            field_cell(bank["eis_participation"], lang, "bool"),
        ])
    sources = (
        f'<p class="prov"><a href="{S.esc(eis["source"])}">{S.esc(S.T(lang, "source"))}</a> '
        f'<time datetime="{S.esc(eis["checked"])}">{S.esc(eis["checked"])}</time></p>'
    )
    return title, lead, lead_and_table(lang, title, lead, caption, headers, rows, sources)


def euribor_margin(lang):
    rate = S.EURIBOR["rates"]["6M"]
    if lang == "et":
        title = "Euribor ja kodulaenu marginaal (2026)"
        lead = (
            f"6 kuu Euribor on {S.fmt_pct(rate['rate_pct'], lang)}, väärtuspäev {rate['value_date']} "
            f"(euribor-rates.eu avaldab EMMI määra 24-tunnise viitega). Pankade avaldatud kodulaen on üldiselt "
            f"individuaalne marginaal pluss Euribor. Ühist marginaali pangad ei avalda."
        )
        headers = ["Pank", "Intressi alus", "Marginaal", "Näite marginaal"]
        caption = "Avaldatud intressi alus ja marginaal. Tähestikuline järjekord."
    else:
        title = "Euribor and the housing-loan margin (2026)"
        lead = (
            f"6-month Euribor is {S.fmt_pct(rate['rate_pct'], lang)}, value date {rate['value_date']} "
            f"(euribor-rates.eu republishes the EMMI fixing with a 24-hour delay). The housing loans banks publish "
            f"are generally an individual margin plus Euribor. The banks do not publish one shared margin."
        )
        headers = ["Bank", "Rate basis", "Margin", "Example margin"]
        caption = "Published rate basis and margin. Alphabetical order."
    rows = []
    for bank in S.BANKS:
        rows.append([
            bank_link(bank, lang),
            field_cell(bank["rate_basis"], lang, "text"),
            field_cell(bank["margin"], lang, "text"),
            field_cell(bank["worked_example"]["margin_pct"], lang, "pct"),
        ])
    sources = (
        f'<p class="prov"><a href="{S.esc(S.EURIBOR["source_url"])}">euribor-rates.eu</a> '
        f'<time datetime="{S.esc(S.EURIBOR["updated"])}">{S.esc(S.EURIBOR["updated"])}</time>. '
        f'{S.esc(S.T(lang, "licensing"))}</p>'
    )
    return title, lead, lead_and_table(lang, title, lead, caption, headers, rows, sources)


def ltv_rules(lang):
    rules = S.SOURCES["eesti_pank_lending_rules"]
    if lang == "et":
        title = "LTV ja Eesti Panga eluasemelaenu nõuded (2026)"
        lead = (
            f"Eesti Pank piirab eluasemelaenu kuni {S.fmt_pct(rules['max_ltv_pct'], lang)} tagatisest ja riigi käendusega "
            f"kuni {S.fmt_pct(rules['max_ltv_state_guaranteed_pct'], lang)}, kehtib alates {rules['in_force_since']}. "
            f"{S.tr(rules['exception'], lang)}."
        )
        headers = ["Pank", "Max LTV", "Max LTV EIS-iga", "Piirkond"]
        caption = "Pankade avaldatud LTV. Tähestikuline järjekord."
    else:
        title = "LTV and Eesti Pank housing-loan requirements (2026)"
        lead = (
            f"Eesti Pank limits a housing loan to {S.fmt_pct(rules['max_ltv_pct'], lang)} of collateral and "
            f"{S.fmt_pct(rules['max_ltv_state_guaranteed_pct'], lang)} with a state guarantee, in force since {rules['in_force_since']}. "
            f"{rules['exception']}."
        )
        headers = ["Bank", "Max LTV", "Max LTV with EIS", "Region"]
        caption = "Published LTV. Alphabetical order."
    rows = []
    for bank in S.BANKS:
        rows.append([
            bank_link(bank, lang),
            field_cell(bank["max_ltv_pct"], lang, "pct"),
            field_cell(bank["max_ltv_with_eis_pct"], lang, "pct"),
            field_cell(bank["regional_ltv_rules"], lang, "text") if not isinstance(bank["regional_ltv_rules"].get("value"), dict) else S.regional_summary(bank["regional_ltv_rules"]["value"], lang),
        ])
    sources = (
        f'<p class="prov"><a href="{S.esc(rules["source"])}">{S.esc(S.T(lang, "source"))}</a> '
        f'<time datetime="{S.esc(rules["checked"])}">{S.esc(rules["checked"])}</time></p>'
    )
    return title, lead, lead_and_table(lang, title, lead, caption, headers, rows, sources)


def debt_service(lang):
    rules = S.SOURCES["eesti_pank_lending_rules"]
    if lang == "et":
        title = "Kodulaenu maksekoormus 50% (2026)"
        lead = (
            f"Eesti Panga võlateeninduse piir on {S.fmt_pct(rules['max_dsti_pct'], lang)} netosissetulekust. "
            f"Ujuva intressiga laenul on stressimäär {S.tr(rules['dsti_stress_rate'], lang)}. "
            f"Osa panku avaldab sama 50% piiri, osa ei avalda oma lehel arvu."
        )
        headers = ["Pank", "Avaldatud DSTI", "Sissetuleku tingimus"]
        caption = "Panga lehel avaldatud maksekoormus. Tähestikuline järjekord."
    else:
        title = "Housing-loan debt service at 50% (2026)"
        lead = (
            f"Eesti Pank's debt-service limit is {S.fmt_pct(rules['max_dsti_pct'], lang)} of net income. "
            f"For a variable-rate loan the stress rate is {rules['dsti_stress_rate']}. "
            f"Some banks publish the same 50% limit; some do not publish a figure on their page."
        )
        headers = ["Bank", "Published DSTI", "Income terms"]
        caption = "Debt-service figures published on the bank page. Alphabetical order."
    rows = []
    for bank in S.BANKS:
        rows.append([
            bank_link(bank, lang),
            field_cell(bank["dsti_max_pct"], lang, "pct"),
            field_cell(bank["income_rules"], lang, "text"),
        ])
    sources = (
        f'<p class="prov"><a href="{S.esc(rules["source"])}">{S.esc(S.T(lang, "source"))}</a> '
        f'<time datetime="{S.esc(rules["checked"])}">{S.esc(rules["checked"])}</time></p>'
    )
    return title, lead, lead_and_table(lang, title, lead, caption, headers, rows, sources)


def loan_term(lang):
    rules = S.SOURCES["eesti_pank_lending_rules"]
    eis = S.SOURCES["eis_housing_loan_guarantee"]
    if lang == "et":
        title = "Kodulaenu maksimaalne periood (2026)"
        lead = (
            f"Eesti Panga maksimaalne eluasemelaenu tähtaeg on {S.fmt_years(rules['max_term_years'], lang)}. "
            f"Kui EIS-i käendusega tähtaeg on üle 30 aasta: {S.tr(eis['term_over_30y_conditions'], lang)}."
        )
        headers = ["Pank", "Maksimaalne tähtaeg"]
        caption = "Pankade avaldatud maksimaalne tähtaeg. Tähestikuline järjekord."
    else:
        title = "Maximum housing-loan term (2026)"
        lead = (
            f"Eesti Pank's maximum housing-loan term is {S.fmt_years(rules['max_term_years'], lang)}. "
            f"If an EIS-guaranteed term exceeds 30 years: {eis['term_over_30y_conditions']}."
        )
        headers = ["Bank", "Maximum term"]
        caption = "Maximum term published by each bank. Alphabetical order."
    rows = [[bank_link(bank, lang), field_cell(bank["max_term_years"], lang, "years")] for bank in S.BANKS]
    sources = (
        f'<p class="prov"><a href="{S.esc(rules["source"])}">Eesti Pank</a> '
        f'<time datetime="{S.esc(rules["checked"])}">{S.esc(rules["checked"])}</time> · '
        f'<a href="{S.esc(eis["source"])}">EIS</a> <time datetime="{S.esc(eis["checked"])}">{S.esc(eis["checked"])}</time></p>'
    )
    return title, lead, lead_and_table(lang, title, lead, caption, headers, rows, sources)


def construction(lang):
    big = next(bank for bank in S.BANKS if bank["id"] == "bigbank")
    stages = big["construction_ltv_stages"]["value"]
    by_stage = {item["stage"]: item for item in stages}
    land = by_stage["land_plot"]["max_ltv_pct"]
    closed = by_stage["building_closed"]["max_ltv_pct"]
    done = by_stage["building_95_percent_complete"]["max_ltv_pct"]
    if lang == "et":
        title = "Ehituslaenu LTV (2026)"
        lead = (
            f"Selles andmestikus on ehituslaenu LTV etapid ainult Bigbanki kohta ja need on tööstusharu siseteave, "
            f"mitte Bigbanki lehel avaldatud tingimus: tavaliselt {S.fmt_pct(land, lang)} maatüki väärtusest, "
            f"{S.fmt_pct(closed, lang)} kui hoone on kinni (seinad, katus, aknad ja uksed paigaldatud), "
            f"{S.fmt_pct(done, lang)} kui hoone on 95% valmis. Teised pangad ei avalda siin andmestikus samu etappe."
        )
        headers = ["Pank", "Ehitust mainiv toode", "Avaldatud LTV etapid"]
        caption = "Ehituslaen andmestikus. Tähestikuline järjekord."
        yes = "jah, siseteave"
        no = S.T(lang, "not_published")
    else:
        title = "Construction-loan LTV (2026)"
        lead = (
            f"In this dataset, construction-loan LTV stages are recorded only for Bigbank, and they are industry insider "
            f"information, not a term published on Bigbank's website: usually {S.fmt_pct(land, lang)} of the land plot's value, "
            f"{S.fmt_pct(closed, lang)} once the building is closed (walls, roof, windows and doors installed), and "
            f"{S.fmt_pct(done, lang)} once the building is 95% complete. The other banks do not publish those stages in this dataset."
        )
        headers = ["Bank", "Product that mentions construction", "Published LTV stages"]
        caption = "Construction loans in the dataset. Alphabetical order."
        yes = "yes, insider information"
        no = S.T(lang, "not_published")
    rows = []
    for bank in S.BANKS:
        named = mentions(bank, ("ehitus", "build", "renovat", "maja ehitus"))
        rows.append([
            bank_link(bank, lang),
            field_cell(bank["loan_types"], lang, "list") if named else S.missing_html(lang),
            yes if "construction_ltv_stages" in bank else no,
        ])
    sources = (
        f'<p class="prov"><strong class="badge">{S.esc(S.T(lang, "insider"))}</strong> '
        f'{S.esc(big["construction_ltv_stages"]["source"])} '
        f'<time datetime="{S.esc(big["construction_ltv_stages"]["checked"])}">{S.esc(big["construction_ltv_stages"]["checked"])}</time></p>'
    )
    return title, lead, lead_and_table(lang, title, lead, caption, headers, rows, sources)


def contract_fee(lang):
    if lang == "et":
        title = "Kodulaenu lepingutasu (2026)"
        lead = "Lepingutasu ei ole kõigile pankadele ühine. Iga pank avaldab oma tasu oma lehel või hinnakirjas, ja tühi lahter tähendab, et väärtust ei ole avaldatud."
        headers = ["Pank", "Lepingutasu"]
        caption = "Avaldatud lepingutasu. Tähestikuline järjekord."
    else:
        title = "Housing-loan contract fee (2026)"
        lead = "There is no contract fee shared by every bank. Each bank publishes its own fee on its page or price list, and an empty cell means the value is not published."
        headers = ["Bank", "Contract fee"]
        caption = "Published contract fee. Alphabetical order."
    rows = [[bank_link(bank, lang), field_cell(bank["contract_fee"], lang, "text")] for bank in S.BANKS]
    return title, lead, lead_and_table(lang, title, lead, caption, headers, rows, "")


def refinancing(lang):
    if lang == "et":
        title = "Kodulaenu refinantseerimine (2026)"
        lead = "Refinantseerimine on mitme panga toodete nimekirjas. Ühist refinantseerimise intressi pangad ei avalda. Kampaania tekst ja kuupäev on tabelis ainult siis, kui pank selle avaldab."
        headers = ["Pank", "Tooted", "Kampaaniad"]
        caption = "Refinantseerimine pankade avaldatud tekstis. Tähestikuline järjekord."
    else:
        title = "Housing-loan refinancing (2026)"
        lead = "Refinancing is named in several banks' product lists. The banks do not publish one shared refinancing rate. A promotion appears in the table only when the bank publishes it."
        headers = ["Bank", "Products", "Promotions"]
        caption = "Refinancing in the banks' published text. Alphabetical order."
    rows = []
    for bank in S.BANKS:
        rows.append([
            bank_link(bank, lang),
            field_cell(bank["loan_types"], lang, "list"),
            field_cell(bank["promo_rates"], lang, "list"),
        ])
    return title, lead, lead_and_table(lang, title, lead, caption, headers, rows, "")


QUESTIONS = [
    ("sissemakse", "down-payment", down_payment),
    ("eis-kaendus", "eis-guarantee", eis_groups),
    ("euribor-ja-marginaal", "euribor-and-margin", euribor_margin),
    ("ltv", "ltv", ltv_rules),
    ("maksekoormus", "debt-service", debt_service),
    ("laenuperiood", "loan-term", loan_term),
    ("ehituslaen", "construction-loan", construction),
    ("lepingutasu", "contract-fee", contract_fee),
    ("refinantseerimine", "refinancing", refinancing),
]


def question_index(lang):
    if lang == "et":
        title = "Kodulaenu küsimused (2026)"
        lead = "Vastused kasutavad ainult pankade avaldatud tingimusi, Eesti Panga ja EIS-i lehti ning märgitud siseteavet. Järjekord ei ole hinnang."
    else:
        title = "Housing-loan questions (2026)"
        lead = "The answers use only terms the banks published, Eesti Pank and EIS pages, and insider information where it is labelled. The order is not a judgement."
    items = []
    for et_slug, en_slug, builder in QUESTIONS:
        q_title, q_lead, _body = builder(lang)
        slug = et_slug if lang == "et" else en_slug
        prefix = "kusimused" if lang == "et" else "questions"
        items.append(f'<li><a href="{S.esc(S.url_for(lang, prefix + "/" + slug))}">{S.esc(q_title)}</a> — {S.esc(q_lead)}</li>')
    body = (
        S.crumbs_html(lang, [("Kodulaen", S.url_for(lang, "")), (title, None)])
        + f"<h1>{S.esc(title)}</h1><p class=\"lead\">{S.esc(lead)}</p><ul>{''.join(items)}</ul>"
    )
    return title, lead, body


def compare_page(lang):
    year = S.TERMS_UPDATED[:4]
    if lang == "et":
        title = f"Eesti pankade kodulaenu tingimused kõrvuti ({year})"
        lead = "Kaheksa panka on kõrvuti tähestikulises järjekorras. Madalam või kõrgem number ei ole soovitus. Iga lahtri juures on allikas ja kontrolli kuupäev."
    else:
        title = f"Estonian housing-loan terms side by side ({year})"
        lead = "Eight banks are side by side in alphabetical order. A lower or higher number is not a recommendation. Every cell has a source and a check date."
    body = (
        S.crumbs_html(lang, [("Kodulaen", S.url_for(lang, "")), (title, None)])
        + f"<h1>{S.esc(title)}</h1><p class=\"lead\">{S.esc(lead)}</p>"
        + f'<p class="small">{S.esc(S.T(lang, "page_updated"))} <time datetime="{S.esc(S.PAGE_MODIFIED)}">{S.esc(S.PAGE_MODIFIED)}</time></p>'
        + S.comparison_section(lang)
    )
    return title, lead, body


def changes_page(lang):
    data = json.loads((S.DATA / "changelog.json").read_text(encoding="utf-8"))
    if lang == "et":
        title = "Mis kodulaenu andmetes muutus"
        lead = f"Siin on andmestiku muudatused kuupäevaga. Euribori faili viimane uuendus on {S.EURIBOR['updated']} (tõmmatud {S.EURIBOR_FETCHED})."
    else:
        title = "What changed in the housing-loan data"
        lead = f"These are the dated changes to the dataset. The Euribor file was last updated on {S.EURIBOR['updated']} (fetched {S.EURIBOR_FETCHED})."
    items = []
    for entry in data["entries"]:
        items.append(f'<li><time datetime="{S.esc(entry["date"])}">{S.esc(entry["date"])}</time> — {S.esc(entry[lang])}</li>')
    body = (
        S.crumbs_html(lang, [("Kodulaen", S.url_for(lang, "")), (title, None)])
        + f"<h1>{S.esc(title)}</h1><p class=\"lead\">{S.esc(lead)}</p><ul>{''.join(items)}</ul>"
        + f'<p class="small">{S.esc(S.T(lang, "page_updated"))} <time datetime="{S.esc(S.PAGE_MODIFIED)}">{S.esc(S.PAGE_MODIFIED)}</time></p>'
    )
    return title, lead, body


def write_pair(kind, et_rel, en_rel, builder, scripts=""):
    for lang, rel in (("et", et_rel), ("en", en_rel)):
        title, description, body = builder(lang)
        current = kind if kind != "question" else "questions"
        payload = {
            "@context": "https://schema.org",
            "@graph": [
                S.breadcrumb(lang, [("Kodulaen", S.url_for(lang, "")), (title, S.url_for(lang, rel))]),
            ],
        }
        if kind == "question":
            payload["@graph"].insert(0, {
                "@type": "FAQPage",
                "mainEntity": [{
                    "@type": "Question",
                    "name": title,
                    "acceptedAnswer": {"@type": "Answer", "text": description},
                }],
            })
        S.write(
            S.page_out(lang, rel),
            S.render_document(lang, rel, title, description, body, current, payload, et_rel, en_rel, scripts),
        )
    S.register_route(et_rel, en_rel)


def extend():
    write_pair("compare", "vorlus", "compare", compare_page, scripts=f'<script src="{S.esc(S.asset("sort.js"))}" defer></script>')
    write_pair("questions", "kusimused", "questions", question_index)
    write_pair("changes", "muudatused", "changes", changes_page)
    for et_slug, en_slug, builder in QUESTIONS:
        write_pair("question", f"kusimused/{et_slug}", f"questions/{en_slug}", builder)
