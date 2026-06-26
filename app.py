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

@st.cache_data(ttl=3600)
def load_pair(drug_name, ae_name):
    return {
        "total": api.get_pair_total(drug_name, ae_name),
        "ror": api.get_ror(drug_name, ae_name),
        "ages": api.get_pair_age(drug_name, ae_name),
        "sex": api.get_pair_sex(drug_name, ae_name),
        "per_year": api.get_pair_per_year(drug_name, ae_name),
        "outcomes": api.get_pair_outcomes(drug_name, ae_name),
        "reporters": api.get_pair_reporters(drug_name, ae_name),
        "countries": api.get_pair_countries(drug_name, ae_name),
        "concomitant": api.get_pair_concomitant_drugs(drug_name, ae_name),
        "seriousness": api.get_pair_seriousness(drug_name, ae_name),
        "dechallenge": api.get_pair_dechallenge(drug_name, ae_name),
        "label": api.get_label_ae_status(drug_name, ae_name),
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

    # ── Deep Dive ──────────────────────────────────────────────────────────────
    ae_options = [r["term"] for r in data["reactions"]]
    st.markdown("### Dig deeper into a reaction →")
    selected_ae = st.selectbox("reaction", [""] + ae_options, label_visibility="collapsed")

    if selected_ae:
        with st.spinner(f"Loading deep dive for {drug.upper()} + {selected_ae.upper()}…"):
            pair = load_pair(drug.strip(), selected_ae)

        st.divider()
        st.subheader(f"Deep Dive: {drug.upper()} + {selected_ae.upper()}")

        lab = pair["label"]
        if not lab["label_found"]:
            st.warning("Drug label not found in OpenFDA — cannot check whether this AE is listed.")
        elif lab["found"]:
            st.success(f"Listed in current FDA label: {', '.join(lab['sections'])} — this is a known, labeled effect.")
        else:
            st.error("Not found in current FDA label — if ROR signal is strong, this may be an unlabeled effect worth investigating.")
        st.caption(
            "Label check searches the AE term (as typed) against FDA label sections. "
            "May miss synonyms or related terms (e.g. 'colitis' will not match 'enteritis')."
        )

        confounding_reasons = []
        if lab.get("in_indication"):
            confounding_reasons.append("this term appears in the drug's indications section — it likely reflects the treated disease, not a drug reaction")
        if lab.get("keyword_flag"):
            confounding_reasons.append("this term contains keywords associated with disease progression or malignancy")
        if confounding_reasons:
            st.warning(
                "Potential confounding by indication: "
                + "; ".join(confounding_reasons).capitalize()
                + ". A high ROR here may reflect the underlying patient population, not a drug-induced effect. "
                "Interpret with clinical judgement."
            )

        r = pair["ror"]
        pair_total = pair["total"]
        fatal_count = next((o["count"] for o in pair["outcomes"] if o["outcome"] == "Fatal"), 0)

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Pair reports", f"{pair_total:,}", f"{pair_total / total:.1%} of drug reports", delta_color="off")
        if r["ror"]:
            p2.metric("ROR", f"{r['ror']:.2f}")
            p3.metric("95% CI", f"{r['ci_low']:.2f} – {r['ci_high']:.2f}")
        p4.metric("Fatal", f"{fatal_count:,}", f"{fatal_count / pair_total:.1%} of pair reports" if pair_total else "—", delta_color="off")

        if r["ror"]:
            is_signal = r["ror"] >= 2 and r["ci_low"] > 1 and pair_total >= 3
            if is_signal:
                st.success(f"Signal detected — all three ROR criteria met (ROR ≥ 2, 95% CI lower bound > 1, n ≥ 3).")
            else:
                st.info("No signal by ROR criteria — one or more of ROR ≥ 2, CI lower bound > 1, n ≥ 3 not met.")
        st.caption(
            "Signal detection method: van Puijenbroek et al. (2002) three-part ROR rule — "
            "ROR ≥ 2 AND lower bound of 95% CI > 1 AND n ≥ 3. "
            "FDA's official method is EBGM (EB05 ≥ 2, multi-item Gamma Poisson Shrinker), "
            "which requires the full FAERS bulk dataset and cannot be computed from the OpenFDA API."
        )

        ps = pair["seriousness"]
        st.markdown("**Seriousness — pair vs. drug overall**")
        q1, q2, q3, q4 = st.columns(4)
        for col, label, key in [
            (q1, "Serious", "Serious"),
            (q2, "Deaths", "Death"),
            (q3, "Hospitalizations", "Hospitalization"),
            (q4, "Life-threatening", "Life Threatening"),
        ]:
            pair_pct = ps[key] / pair_total if pair_total else 0
            drug_pct = s[key] / total if total else 0
            delta = f"{pair_pct - drug_pct:+.1%} vs drug overall"
            col.metric(label, f"{pair_pct:.1%}", delta, delta_color="inverse")
        st.caption(
            "Drug overall = all reports for this drug across every reaction. "
            "A higher % here means patients with this specific reaction tend to have worse outcomes "
            "than the average report for this drug — not compared to the general population. "
            "Caveat: serious events are more likely to be reported at all, so all percentages are inflated."
        )

        dl, dr = st.columns(2)
        if r["ror"]:
            dl.plotly_chart(charts.ror_indicator(r["ror"], r["ci_low"], r["ci_high"]))
        dr.plotly_chart(charts.concomitant_bar(pair["concomitant"]))

        st.plotly_chart(charts.trend_area(pair["per_year"]))

        dl2, dr2 = st.columns(2)
        dl2.plotly_chart(charts.age_bar(pair["ages"]))
        dr2.plotly_chart(charts.sex_pie(pair["sex"]))

        dl3, dr3 = st.columns(2)
        dl3.plotly_chart(charts.outcomes_bar(pair["outcomes"]))
        dr3.plotly_chart(charts.dechallenge_bar(pair["dechallenge"]))
        st.caption(
            "De-challenge filtered to HCP reporters only (physician, pharmacist, other health professional). "
            "'Withdrawn' = drug stopped when AE occurred — supports drug causality. "
            "Consumer-reported de-challenge is excluded as it may reflect unrelated reasons for stopping."
        )

        dl4, dr4 = st.columns(2)
        dl4.plotly_chart(charts.reporters_bar(pair["reporters"]))
        dr4.plotly_chart(charts.countries_bar(pair["countries"]))
