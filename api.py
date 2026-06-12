from datetime import date

import requests

BASE_URL = "https://api.fda.gov/drug/event.json"
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
