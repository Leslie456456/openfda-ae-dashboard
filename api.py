import math
from datetime import date

import requests

BASE_URL = "https://api.fda.gov/drug/event.json"
LABEL_URL = "https://api.fda.gov/drug/label.json"
FIRST_FAERS_YEAR = 2004

AGE_LABELS = {
    "1": "Neonate", "2": "Infant", "3": "Child",
    "4": "Adolescent", "5": "Adult", "6": "Elderly",
}
SEX_LABELS = {"0": "Unknown", "1": "Male", "2": "Female"}
OUTCOME_LABELS = {
    "1": "Recovered", "2": "Recovering", "3": "Not recovered",
    "4": "Recovered with sequelae", "5": "Fatal", "6": "Unknown",
}
REPORTER_LABELS = {
    "1": "Physician", "2": "Pharmacist", "3": "Other health professional",
    "4": "Lawyer", "5": "Consumer / non-professional",
}
ACTION_LABELS = {
    "1": "Withdrawn", "2": "Dose reduced", "3": "Dose increased",
    "4": "No change", "5": "Unknown", "6": "Not applicable",
}

def _build_search(drug_name, serious_only=False):
    search = f'patient.drug.medicinalproduct.exact:"{drug_name.upper()}"'
    if serious_only:
        search += " AND serious:1"
    return search

def _count(drug_name, field, limit=100, serious_only=False):
    response = requests.get(BASE_URL, params={
        "search": _build_search(drug_name, serious_only),
        "count": field,
        "limit": limit,
    })
    return response.json().get("results", [])

def _labeled(results, labels, key):
    return [
        {key: labels.get(str(r["term"]), r["term"]), "count": r["count"]}
        for r in results
    ]

def get_total_reports(drug_name, serious_only=False):
    response = requests.get(BASE_URL, params={
        "search": _build_search(drug_name, serious_only),
        "limit": 1,
    })
    return response.json()["meta"]["results"]["total"]

def get_top_reactions(drug_name, serious_only=False, limit=15):
    return _count(
        drug_name, "patient.reaction.reactionmeddrapt.exact",
        limit=limit, serious_only=serious_only,
    )

def get_seriousness(drug_name):
    results = {}
    for field, label in [
        ("serious", "Serious"),
        ("seriousnessdeath", "Death"),
        ("seriousnesshospitalization", "Hospitalization"),
        ("seriousnesslifethreatening", "Life Threatening"),
    ]:
        data = _count(drug_name, field)
        results[label] = next((r["count"] for r in data if str(r["term"]) == "1"), 0)
    return results

def get_age_distribution(drug_name):
    return _labeled(_count(drug_name, "patient.patientagegroup"), AGE_LABELS, "age_group")

def get_sex_breakdown(drug_name):
    return _labeled(_count(drug_name, "patient.patientsex"), SEX_LABELS, "sex")

def get_reaction_outcomes(drug_name):
    return _labeled(
        _count(drug_name, "patient.reaction.reactionoutcome"), OUTCOME_LABELS, "outcome"
    )

def get_reporter_types(drug_name):
    return _labeled(
        _count(drug_name, "primarysource.qualification"), REPORTER_LABELS, "reporter"
    )

def get_top_countries(drug_name, limit=10):
    results = _count(drug_name, "occurcountry.exact", limit=limit)
    return [{"country": r["term"], "count": r["count"]} for r in results]

def get_reports_per_year(drug_name):
    counts = []
    for year in range(FIRST_FAERS_YEAR, date.today().year + 1):
        search = _build_search(drug_name) + f" AND receivedate:[{year}0101 TO {year}1231]"
        response = requests.get(BASE_URL, params={"search": search, "limit": 1})
        total = response.json().get("meta", {}).get("results", {}).get("total", 0)
        counts.append({"year": year, "count": total})
    return counts

# ── Drug-AE pair helpers ──────────────────────────────────────────────────────

def _build_pair_search(drug_name, ae_name):
    return (
        f'patient.drug.medicinalproduct.exact:"{drug_name.upper()}"'
        f' AND patient.reaction.reactionmeddrapt.exact:"{ae_name.upper()}"'
    )

def _count_pair(drug_name, ae_name, field, limit=100):
    response = requests.get(BASE_URL, params={
        "search": _build_pair_search(drug_name, ae_name),
        "count": field,
        "limit": limit,
    })
    return response.json().get("results", [])

def _get_ae_total(ae_name):
    response = requests.get(BASE_URL, params={
        "search": f'patient.reaction.reactionmeddrapt.exact:"{ae_name.upper()}"',
        "limit": 1,
    })
    return response.json().get("meta", {}).get("results", {}).get("total", 0)

def _get_faers_total():
    response = requests.get(BASE_URL, params={"limit": 1})
    return response.json()["meta"]["results"]["total"]

def get_pair_total(drug_name, ae_name):
    response = requests.get(BASE_URL, params={
        "search": _build_pair_search(drug_name, ae_name),
        "limit": 1,
    })
    return response.json().get("meta", {}).get("results", {}).get("total", 0)

def get_pair_age(drug_name, ae_name):
    return _labeled(_count_pair(drug_name, ae_name, "patient.patientagegroup"), AGE_LABELS, "age_group")

def get_pair_sex(drug_name, ae_name):
    return _labeled(_count_pair(drug_name, ae_name, "patient.patientsex"), SEX_LABELS, "sex")

def get_pair_outcomes(drug_name, ae_name):
    return _labeled(
        _count_pair(drug_name, ae_name, "patient.reaction.reactionoutcome"), OUTCOME_LABELS, "outcome"
    )

def get_pair_reporters(drug_name, ae_name):
    return _labeled(
        _count_pair(drug_name, ae_name, "primarysource.qualification"), REPORTER_LABELS, "reporter"
    )

def get_pair_countries(drug_name, ae_name, limit=10):
    results = _count_pair(drug_name, ae_name, "occurcountry.exact", limit=limit)
    return [{"country": r["term"], "count": r["count"]} for r in results]

def get_pair_per_year(drug_name, ae_name):
    counts = []
    for year in range(FIRST_FAERS_YEAR, date.today().year + 1):
        search = _build_pair_search(drug_name, ae_name) + f" AND receivedate:[{year}0101 TO {year}1231]"
        response = requests.get(BASE_URL, params={"search": search, "limit": 1})
        total = response.json().get("meta", {}).get("results", {}).get("total", 0)
        counts.append({"year": year, "count": total})
    return counts

def get_pair_seriousness(drug_name, ae_name):
    results = {}
    for field, label in [
        ("serious", "Serious"),
        ("seriousnessdeath", "Death"),
        ("seriousnesshospitalization", "Hospitalization"),
        ("seriousnesslifethreatening", "Life Threatening"),
    ]:
        data = _count_pair(drug_name, ae_name, field)
        results[label] = next((r["count"] for r in data if str(r["term"]) == "1"), 0)
    return results

def get_pair_dechallenge(drug_name, ae_name):
    hcp_search = (
        _build_pair_search(drug_name, ae_name)
        + " AND primarysource.qualification:[1 TO 3]"
    )
    response = requests.get(BASE_URL, params={
        "search": hcp_search,
        "count": "patient.drug.actiondrug",
        "limit": 100,
    })
    results = response.json().get("results", [])
    return _labeled(results, ACTION_LABELS, "action")

CONFOUNDING_KEYWORDS = {
    "progression", "metastasis", "metastases", "metastatic",
    "neoplasm", "malignant", "malignancy", "tumour", "tumor",
    "cancer", "carcinoma", "lymphoma", "leukemia", "sarcoma",
    "condition aggravated", "disease progression",
}

def get_label_ae_status(drug_name, ae_name):
    label = None
    for field in ["openfda.substance_name.exact", "openfda.brand_name.exact"]:
        resp = requests.get(LABEL_URL, params={
            "search": f'{field}:"{drug_name.upper()}"',
            "limit": 1,
        })
        results = resp.json().get("results", [])
        if results:
            label = results[0]
            break

    ae_lower = ae_name.lower()
    keyword_flag = any(kw in ae_lower for kw in CONFOUNDING_KEYWORDS)

    if not label:
        return {"label_found": False, "found": False, "sections": [],
                "in_indication": False, "keyword_flag": keyword_flag}

    section_map = [
        ("Boxed Warning", "boxed_warning"),
        ("Warnings & Precautions", "warnings_and_precautions"),
        ("Adverse Reactions", "adverse_reactions"),
        ("Warnings", "warnings"),
    ]
    hits = [name for name, field in section_map if ae_lower in " ".join(label.get(field, [])).lower()]
    indication_text = " ".join(label.get("indications_and_usage", [])).lower()
    in_indication = ae_lower in indication_text

    return {
        "label_found": True, "found": len(hits) > 0, "sections": hits,
        "in_indication": in_indication, "keyword_flag": keyword_flag,
    }

def get_pair_concomitant_drugs(drug_name, ae_name, limit=10):
    results = _count_pair(drug_name, ae_name, "patient.drug.medicinalproduct.exact", limit=limit + 5)
    drug_upper = drug_name.upper()
    filtered = [r for r in results if r["term"].upper() != drug_upper]
    return [{"drug": r["term"], "count": r["count"]} for r in filtered[:limit]]

def get_ror(drug_name, ae_name):
    a = get_pair_total(drug_name, ae_name)
    drug_total = get_total_reports(drug_name)
    ae_total = _get_ae_total(ae_name)
    faers_total = _get_faers_total()

    b = max(drug_total - a, 0)
    c = max(ae_total - a, 0)
    d = max(faers_total - a - b - c, 0)

    if a == 0 or b == 0 or c == 0 or d == 0:
        return {"ror": None, "ci_low": None, "ci_high": None}

    ror = (a * d) / (b * c)
    log_se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    ci_low = math.exp(math.log(ror) - 1.96 * log_se)
    ci_high = math.exp(math.log(ror) + 1.96 * log_se)

    return {"ror": round(ror, 2), "ci_low": round(ci_low, 2), "ci_high": round(ci_high, 2)}


if __name__ == "__main__":
    drug = "aspirin"
    print(f"Total reports: {get_total_reports(drug)}")
    print(f"Top reactions: {get_top_reactions(drug, limit=3)}")
    print(f"Seriousness: {get_seriousness(drug)}")
    print(f"Age groups: {get_age_distribution(drug)}")
    print(f"Sex breakdown: {get_sex_breakdown(drug)}")
    print(f"Outcomes: {get_reaction_outcomes(drug)}")
    print(f"Reporters: {get_reporter_types(drug)}")
    print(f"Countries: {get_top_countries(drug, limit=5)}")
    print(f"Per year (last 3): {get_reports_per_year(drug)[-3:]}")
