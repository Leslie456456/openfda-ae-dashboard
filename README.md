# OpenFDA Adverse Events Dashboard

Type a drug name, see its adverse-event reporting profile — built on the FDA's
[openFDA](https://open.fda.gov/apis/drug/event/) API over FAERS (the FDA Adverse
Event Reporting System, ~20M+ spontaneous reports).

For each drug, the dashboard shows:

- **Total reports**, with serious / death / hospitalization / life-threatening
  counts and their share of all reports
- **Reports per year** since 2004 — the reporting trend over the drug's life
- **Top reported reactions** (MedDRA preferred terms)
- **Age group** and **sex** distributions
- **Reaction outcomes** (recovered / not recovered / fatal / unknown)
- **Who reported** (physician, pharmacist, consumer, lawyer) and **top countries**

All charts are interactive (hover, zoom, pan).

## Run it locally

```bash
pip install -r requirements.txt
python3 -m streamlit run app.py
```

Then open http://localhost:8501.

## How it's built

| File | Job |
|---|---|
| `api.py` | Queries openFDA (pure data fetching, no UI) |
| `charts.py` | Turns API data into plotly figures |
| `app.py` | Streamlit dashboard wiring it together |

Each layer has a self-test: `python3 api.py` and `python3 charts.py` run
standalone checks. API responses are cached for one hour to respect openFDA
rate limits.

## Read the numbers carefully

FAERS is a **spontaneous reporting system**, and these counts must not be read
as incidence rates:

- **No denominator.** Report counts say nothing about how many patients took
  the drug. More prescriptions → more reports, regardless of safety.
- **Reporting bias.** Serious outcomes are far more likely to be reported than
  mild ones, so the "serious" share is inflated.
- **Reported, not verified.** A report is an association someone chose to
  submit — not an established causal link.
- **Name fragmentation.** Searches match the *verbatim* product name as
  reported (e.g., KEYTRUDA and PEMBROLIZUMAB return different result sets).

This tool is for **signal exploration**, not safety conclusions.

## Roadmap

- Search on openFDA's harmonized `generic_name` field to merge brand/generic
  reporting (e.g., Keytruda + pembrolizumab)
- Suspect-drug-only filtering and indication charts, computed client-side
  (openFDA queries cannot tie conditions to the same drug entry within a report)
- ROR / PRR disproportionality scoring
- Compare top reported reactions against the official label (`drug/label`)
  to surface unlabeled signals

## About

A learning project exploring the openFDA drug adverse-event API. Built with
Python, pandas, plotly, and streamlit.
