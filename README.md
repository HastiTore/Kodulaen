# Kodulaen

Tasuta ja erapooletu kogumik kaheksa Eesti panga avaldatud eluasemelaenu tingimustest. Leht on staatiline HTML. See ei ole finantsnõuanne ega krediidi vahendamine.

Free, neutral compilation of the published housing-loan terms of the eight banks that issue home loans in Estonia. The site is static HTML. It is not financial advice and not credit intermediation.

Expected site: <https://hastitore.github.io/Kodulaen/>

## What is in the repository

| Path | Role |
|---|---|
| `data/banks.json`, `data/banks.csv` | Bank terms. One record per value: `value`, `note`, `source`, `checked`. |
| `data/sources.json` | Eesti Pank limits, EIS guarantee terms, new-loan statistics. |
| `data/euribor.json` | 1M, 3M, 6M and 12M Euribor from euribor-rates.eu. |
| `data/schema.json`, `data/README.md` | Schema and the dataset notes. |
| `scripts/build_site.py` | Renders `dist/` from the JSON. Estonian at the root, English under `/en/`. |
| `scripts/translations.json` | Estonian wording of the English dataset strings. |
| `scripts/fetch_euribor.py` | Refreshes `data/euribor.json`. Exits without writing if parsing fails. |
| `scripts/build_data.py`, `scripts/build_sources.py` | Reference generators for the bank and source files. Running them overwrites `data/`. |
| `scripts/serve.py` | Local preview at `http://127.0.0.1:8765/Kodulaen/`. |
| `site/` | CSS, the small sort script, favicon. |
| `.github/workflows/pages.yml` | Builds the site on pull requests and deploys `main` to GitHub Pages. |
| `.github/workflows/update-euribor.yml` | Weekdays at 06:00 UTC: fetch Euribor, commit, rebuild, deploy. |

No paid services. Python’s standard library is enough. There is no application framework and no JavaScript rendering of the content. The sort control only reorders the comparison table; without JavaScript the banks stay alphabetical.

## Pages

- `/` and `/en/` — comparison table. Alphabetical by default. A reader can reorder it. Nothing is ranked, hidden, or marked as best.
- `/pangad/<id>/` and `/en/banks/<id>/` — one page per bank, every field with its source and check date, the bank’s worked example, and a clearly labelled illustration when that example’s Euribor is older than today’s fixing.
- `/reeglid/` and `/en/rules/` — Eesti Pank lending limits and EIS guarantees, including first-time buyers and young families. The page does not say who qualifies.
- `/euribor/` and `/en/euribor/` — current tenors, attribution, and the EMMI licensing note.
- `/meist/` and `/en/about/` — method, neutrality, disclaimer, and questions.
- `/data/banks.json`, `/data/banks.csv`, `/data/euribor.json`, `/data/sources.json` — the same files, with `updated` timestamps (`meta.updated`, or `updated` on the Euribor file).
- `/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/sitemap.xml` — summaries and crawler access, including GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-User, PerplexityBot, Google-Extended and Applebot-Extended.

Russian is not built yet.

## Neutrality

Banks are alphabetical. `null` is shown as “avaldamata” / “not published”, never guessed. The only non-public figure is Luminor’s regional LTV. Its source is:

> Information from a former member of Luminor's housing loan team (not publicly published by Luminor), 2026-11-09

The site labels that field “tööstusharu siseteave, pank ei ole seda avaldanud” / “industry insider information, not published by the bank”.

There are no lead forms, affiliate links, or ads. The disclaimer is on every page: information only, not financial advice or credit intermediation, no payments from banks, check the terms with the bank.

## Build locally

```bash
python3 scripts/build_site.py
python3 scripts/serve.py
```

Open <http://127.0.0.1:8765/Kodulaen/>. The build checks links, the disclaimer, the Luminor label, the Euribor illustration, and that the HTML does not contain a ranking phrase. `BASE_PATH` defaults to `/Kodulaen` and `SITE_ORIGIN` to `https://hastitore.github.io`.

## Update the data

Bank terms change on the banks’ pages. Do not fill a gap with a guess: use `null` and a note.

1. Edit `scripts/build_data.py` (the reference copy of the dataset) and run `python3 scripts/build_data.py`, **or** edit `data/banks.json` and `data/banks.csv` together so they stay in lockstep.
2. Set `checked` to the day you read the page. Keep `meta.updated` in step with that.
3. Official context (Eesti Pank, EIS, the statistics snapshot) lives in `scripts/build_sources.py`. Run `python3 scripts/build_sources.py` after editing it.
4. If you add an English sentence that the Estonian pages display, add it to `scripts/translations.json`. The build fails when a string is missing.
5. Run `python3 scripts/build_site.py` and commit the data files. `dist/` is generated and is not committed.

`scripts/build_data.py` overwrites `data/banks.json` and `data/banks.csv`. The Luminor regional-LTV source string in that script is the corrected one above; do not put the old “unverified” wording back.

### Euribor

```bash
python3 scripts/fetch_euribor.py --dry-run   # parse only
python3 scripts/fetch_euribor.py             # replace data/euribor.json
```

The weekday workflow does this on `main`, commits `data/euribor.json`, and deploys. A parse failure stops the job before any write. A push made with the default `GITHUB_TOKEN` does not start the Pages workflow again, so the Euribor workflow deploys the site itself.

Rates are shown with a link to [euribor-rates.eu](https://www.euribor-rates.eu/en/) and a note that EMMI licensing for republishing is under review.

## Enable GitHub Pages

The workflow cannot turn Pages on by itself. After this branch is merged:

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. **Settings → Actions → General → Workflow permissions → Read and write.** The weekday job commits `data/euribor.json`. The workflow file already requests `contents: write`; the repository setting has to allow it.

The first deploy runs when a commit reaches `main`. The site URL is <https://hastitore.github.io/Kodulaen/>.

Last deploy trigger: 2026-11-09, after Pages was set to GitHub Actions and workflow permissions to read and write.

## Licence

CC BY 4.0 is proposed for this compilation. The underlying facts belong to the banks and public bodies cited.
