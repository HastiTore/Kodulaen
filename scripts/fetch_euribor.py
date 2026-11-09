#!/usr/bin/env python3
"""Fetch current Euribor (1M, 3M, 6M, 12M) from euribor-rates.eu and write data/euribor.json.

Source publishes EMMI Euribor with a 24h delay. Republishing Euribor values may require an
EMMI licence (open question) — see data/README.md.

The file is replaced only after every tenor parses and passes range checks. A failed run
leaves the previous data/euribor.json untouched and exits non-zero.
"""
import datetime
import html
import json
import pathlib
import re
import sys
import urllib.request

URL = "https://www.euribor-rates.eu/en/"
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "euribor.json"
TENORS = {"1 month": "1M", "3 months": "3M", "6 months": "6M", "12 months": "12M"}
ORDER = ["1M", "3M", "6M", "12M"]
# Euribor has been slightly negative. Anything outside this band is a parse error.
RATE_MIN = -2.0
RATE_MAX = 20.0
# A fixing older than this is treated as a bad parse (the source is a current-rate page).
MAX_AGE_DAYS = 14


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (homeloan-site data fetcher)"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            sys.exit(f"Euribor source returned HTTP {status}")
        body = response.read()
    if not body:
        sys.exit("Euribor source returned an empty body")
    return body.decode("utf-8", "ignore")


def cells(row_html):
    return [
        re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", cell))).strip()
        for cell in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row_html, flags=re.S)
    ]


def parse(page):
    out = {}
    for match in re.finditer(r"<table.*?</table>", page, flags=re.S):
        table = match.group()
        before = re.sub(r"<[^>]+>", " ", page[max(0, match.start() - 1500):match.start()])
        pre_dates = re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b", before)
        rows = [cells(row) for row in re.findall(r"<tr.*?</tr>", table, flags=re.S)]
        rows = [row for row in rows if row]
        if not rows:
            continue
        header = rows[0]
        dates = [item for item in header if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", item)] or pre_dates[-1:]
        for row in rows:
            label = row[0].lower().replace("euribor", "").strip()
            if label in TENORS and len(row) > 1:
                found = re.search(r"-?\d+(?:\.\d+)?", row[1])
                if not found:
                    continue
                if dates:
                    month, day, year = map(int, dates[0].split("/"))
                    try:
                        value_date = datetime.date(year, month, day).isoformat()
                    except ValueError:
                        sys.exit(f"Unusable Euribor value date: {dates[0]}")
                else:
                    value_date = None
                out.setdefault(TENORS[label], {"rate_pct": float(found.group()), "value_date": value_date})
    return out


def validate(rates, today):
    missing = [tenor for tenor in ORDER if tenor not in rates]
    if missing:
        sys.exit(f"Could not parse tenors: {missing}")
    for tenor in ORDER:
        item = rates[tenor]
        rate = item["rate_pct"]
        if isinstance(rate, bool) or not isinstance(rate, (int, float)):
            sys.exit(f"{tenor}: rate is not a number ({rate!r})")
        if not (RATE_MIN <= float(rate) <= RATE_MAX):
            sys.exit(f"{tenor}: rate {rate} is outside {RATE_MIN}..{RATE_MAX}")
        value_date = item.get("value_date")
        if not value_date:
            sys.exit(f"{tenor}: missing value date")
        try:
            parsed = datetime.date.fromisoformat(value_date)
        except ValueError:
            sys.exit(f"{tenor}: bad value date {value_date}")
        age = (today - parsed).days
        if age < 0:
            sys.exit(f"{tenor}: value date {value_date} is in the future")
        if age > MAX_AGE_DAYS:
            sys.exit(f"{tenor}: value date {value_date} is {age} days old; refusing to write")


def main():
    dry_run = "--dry-run" in sys.argv
    page = fetch(URL)
    rates = parse(page)
    today = datetime.datetime.now(datetime.timezone.utc).astimezone().date()
    validate(rates, today)
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    fetched = now.isoformat(timespec="seconds")
    data = {
        "source_url": URL,
        "source_type": "secondary: euribor-rates.eu republishes EMMI Euribor with a 24-hour delay",
        "administrator": "European Money Markets Institute (EMMI), https://www.emmi-benchmarks.eu/",
        "fetched_at": fetched,
        "updated": now.date().isoformat(),
        "licensing_note": "Open question: public redistribution of Euribor values may require an EMMI licence.",
        "rates": {tenor: {**rates[tenor], "source_url": URL} for tenor in ORDER},
    }
    if dry_run:
        print(json.dumps(data["rates"], indent=1), "\nfetched_at", fetched, "\n(dry-run, file not written)")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUT)
    print(json.dumps(data["rates"], indent=1), "\nfetched_at", fetched)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # urllib errors and unexpected parse errors must not leave a partial file.
        if not isinstance(error, SystemExit):
            sys.exit(f"Euribor fetch failed: {type(error).__name__}: {error}")
        raise
