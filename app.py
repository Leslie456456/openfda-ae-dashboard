import streamlit as st

import api
import charts

st.set_page_config(page_title="OpenFDA Adverse Events Dashboard", layout="wide")

st.title("💊 OpenFDA Adverse Events Dashboard")
st.caption(
    "Data: FDA FAERS spontaneous reports via OpenFDA. "
    "Counts reflect *reporting*, not incidence — serious events are "
    "over-represented and there is no denominator. Signal exploration only."
)

drug = st.text_input("Drug name", value="aspirin")

@st.cache_data(ttl=3600)
def load(drug_name):
    return {
        "total": api.get_total_reports(drug_name),
        "seriousness": api.get_seriousness(drug_name),
        "reactions": api.get_top_reactions(drug_name),
        "ages": api.get_age_distribution(drug_name),
        "sex": api.get_sex_breakdown(drug_name),
        "per_year": api.get_reports_per_year(drug_name),
        "outcomes": api.get_reaction_outcomes(drug_name),
        "reporters": api.get_reporter_types(drug_name),
        "countries": api.get_top_countries(drug_name),
    }

if drug:
    try:
        with st.spinner(f"Querying FAERS for {drug.upper()}…"):
            data = load(drug.strip())
    except Exception:
        st.error(
            f'No FAERS reports found for "{drug}". Check the spelling — '
            "FAERS matches exact product names, so try the brand name "
            "or the generic name if one fails."
        )
        st.stop()

    s = data["seriousness"]
    total = data["total"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total reports", f"{total:,}")
    for col, label, key in [
        (c2, "Serious", "Serious"),
        (c3, "Deaths", "Death"),
        (c4, "Hospitalizations", "Hospitalization"),
        (c5, "Life-threatening", "Life Threatening"),
    ]:
        col.metric(label, f"{s[key]:,}", f"{s[key] / total:.1%} of reports", delta_color="off")

    st.plotly_chart(charts.trend_area(data["per_year"]))
    st.plotly_chart(charts.reactions_bar(data["reactions"]))

    left, right = st.columns(2)
    left.plotly_chart(charts.age_bar(data["ages"]))
    right.plotly_chart(charts.sex_pie(data["sex"]))

    left2, right2 = st.columns(2)
    left2.plotly_chart(charts.outcomes_bar(data["outcomes"]))
    right2.plotly_chart(charts.reporters_bar(data["reporters"]))

    st.plotly_chart(charts.countries_bar(data["countries"]))
