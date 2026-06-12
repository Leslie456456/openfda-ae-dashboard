import pandas as pd
import plotly.express as px

AGE_ORDER = ["Neonate", "Infant", "Child", "Adolescent", "Adult", "Elderly"]

def reactions_bar(reactions):
    df = pd.DataFrame(reactions)
    fig = px.bar(
        df, x="count", y="term", orientation="h",
        labels={"count": "Reports", "term": ""},
        title="Top Reported Reactions",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig

def age_bar(age_groups):
    df = pd.DataFrame(age_groups)
    fig = px.bar(
        df, x="age_group", y="count",
        category_orders={"age_group": AGE_ORDER},
        labels={"age_group": "", "count": "Reports"},
        title="Reports by Age Group",
    )
    return fig

def sex_pie(sex_breakdown):
    df = pd.DataFrame(sex_breakdown)
    fig = px.pie(df, names="sex", values="count", title="Reports by Sex")
    return fig

def trend_area(per_year):
    df = pd.DataFrame(per_year)
    fig = px.area(
        df, x="year", y="count",
        labels={"year": "", "count": "Reports"},
        title="Reports Received per Year",
    )
    return fig

def outcomes_bar(outcomes):
    df = pd.DataFrame(outcomes)
    fig = px.bar(
        df, x="count", y="outcome", orientation="h",
        labels={"count": "Reactions", "outcome": ""},
        title="Reaction Outcomes",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig

def reporters_bar(reporters):
    df = pd.DataFrame(reporters)
    fig = px.bar(
        df, x="count", y="reporter", orientation="h",
        labels={"count": "Reports", "reporter": ""},
        title="Who Reported",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig

def countries_bar(countries):
    df = pd.DataFrame(countries)
    fig = px.bar(
        df, x="country", y="count",
        labels={"country": "", "count": "Reports"},
        title="Top Reporting Countries",
    )
    return fig

if __name__ == "__main__":
    import api
    drug = "aspirin"
    figures = {
        "reactions": reactions_bar(api.get_top_reactions(drug)),
        "ages": age_bar(api.get_age_distribution(drug)),
        "sex": sex_pie(api.get_sex_breakdown(drug)),
        "trend": trend_area(api.get_reports_per_year(drug)),
        "outcomes": outcomes_bar(api.get_reaction_outcomes(drug)),
        "reporters": reporters_bar(api.get_reporter_types(drug)),
        "countries": countries_bar(api.get_top_countries(drug)),
    }
    for name, fig in figures.items():
        path = f"/tmp/{name}.html"
        fig.write_html(path)
        print(f"wrote {path}")
