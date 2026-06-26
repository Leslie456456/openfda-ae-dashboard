# OpenFDA Adverse Events Dashboard

Type a drug name, see its adverse-event reporting profile — then drill into any
specific drug-reaction pair to explore the clinical story behind the signal.
Built on the FDA's [openFDA](https://open.fda.gov/apis/drug/event/) API over
FAERS (the FDA Adverse Event Reporting System, ~20M+ spontaneous reports).

## What's new — June 26 2026

**Drug-AE Pair Deep Dive module** added. After loading any drug, pick a specific
reaction from the top 15 list to get a full clinical profile of that drug-reaction
pair, including:

- ROR with 95% CI and three-part signal flag (van Puijenbroek 2002)
- FDA label check — is this reaction listed in the current label?
- Confounding by indication detection — flags disease-related terms (e.g. cancer
  progression for oncology drugs) that inflate ROR artificially
- Seriousness comparison — pair vs. drug overall
- De-challenge filtered to HCP reporters only
- Top co-reported (concomitant) drugs
- Full pair demographics, outcomes, trend, and countries

---

## What it shows

### Drug overview
For any drug name:

- **Total reports** with serious / death / hospitalization / life-threatening counts
- **Reports per year** since 2004 — the reporting trend over the drug's life
- **Top 15 reported reactions** (MedDRA preferred terms)
- **Age group** and **sex** distributions
- **Reaction outcomes** and **reporter types** (physician, pharmacist, consumer, lawyer)
- **Top reporting countries**

### Drug-AE pair deep dive
Pick any reaction from the top 15 to get a clinical profile of that specific drug-reaction pair:

- **ROR (Reporting Odds Ratio)** with 95% CI and a signal flag using the
  van Puijenbroek (2002) three-part rule: ROR ≥ 2, CI lower bound > 1, n ≥ 3
- **FDA label check** — whether the reaction is listed in the Boxed Warning,
  Warnings & Precautions, or Adverse Reactions section of the current label
- **Confounding by indication warning** — flags reactions that may reflect the
  treated disease rather than a drug effect (e.g. cancer progression for oncology drugs),
  detected via keyword heuristic and indication-section overlap
- **Seriousness comparison** — pair vs. drug overall for serious, death,
  hospitalization, and life-threatening rates
- **De-challenge (HCP reporters only)** — what clinicians did with the drug
  when the reaction occurred (withdrawn, dose reduced, no change)
- **Top co-reported drugs** — concomitant medications in the same reports
- **Demographics, outcomes, trend over time, and countries** — all filtered
  to the specific drug-reaction pair

All charts are interactive (hover, zoom, pan). Pair data is cached separately
from drug-level data (1 hour TTL each).

## Run it locally

```bash
pip install -r requirements.txt
python3 -m streamlit run app.py
```

Then open http://localhost:8501.

## How it's built

| File | Job |
|---|---|
| `api.py` | Queries openFDA — drug-level and pair-level functions, ROR math, FDA label lookup |
| `charts.py` | Turns API data into plotly figures |
| `app.py` | Streamlit dashboard wiring it together |

Each layer has a self-test: `python3 api.py` and `python3 charts.py` run
standalone checks. API responses are cached for one hour to respect openFDA
rate limits.

## Read the numbers carefully

FAERS is a **spontaneous reporting system**, not a clinical trial. These counts
must not be read as incidence rates:

- **No denominator.** Report counts say nothing about how many patients took
  the drug. More prescriptions → more reports, regardless of safety.
- **Reporting bias.** Serious outcomes are far more likely to be reported than
  mild ones, so the "serious" share is inflated relative to real-world rates.
- **Reported, not verified.** A report is an association someone chose to
  submit — not an established causal link.
- **Name fragmentation.** Searches match the *verbatim* product name as
  reported (e.g., KEYTRUDA and PEMBROLIZUMAB return different result sets).
- **Confounding by indication.** For disease-specific drugs (e.g. oncology),
  high ROR for disease-related terms (progression, metastasis) reflects the
  patient population, not a drug effect. The dashboard flags these automatically.
- **ROR ≠ FDA's official method.** FDA uses EBGM (EB05 ≥ 2, multi-item Gamma
  Poisson Shrinker), which requires the full FAERS bulk dataset. ROR is a widely
  accepted alternative used in peer-reviewed pharmacovigilance literature.

This tool is for **signal exploration**, not safety conclusions.

## Roadmap

- Search on openFDA's harmonized `generic_name` field to merge brand/generic
  reporting (e.g., Keytruda + pembrolizumab)
- Suspect-drug-only filtering (currently catches all reports where the drug
  appears, including concomitant role)
- Time-to-onset distribution (sparse in openFDA but partially available via
  `patient.drug.drugstartdate`)
- Re-challenge data (`patient.drug.reactionrecurrence`)
- PRR (Proportional Reporting Ratio) alongside ROR

## About

A learning project exploring the openFDA drug adverse-event API and
pharmacovigilance signal detection. Built with Python, pandas, plotly,
and streamlit.
