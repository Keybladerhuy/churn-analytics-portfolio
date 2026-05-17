"""
pages/2_Churn_Drivers.py — Churn Driver Analysis

Answers "why are customers leaving?" and bridges the Executive Summary
(scale of the problem) to the Retention Priority List (who to act on).
Three drivers are covered in depth; monthly charges is noted as a
correlate, not an independent signal.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar, sql_expander

con = get_connection()
dfs = load_all(con)

render_sidebar(dfs)

drivers = dfs["02_churn_drivers"]

# Pre-compute the key high/low comparisons used throughout the page
contract = drivers[drivers["driver"] == "Contract type"]
worst_contract = contract.loc[contract["churn_rate"].idxmax()]
best_contract  = contract.loc[contract["churn_rate"].idxmin()]

tenure = drivers[drivers["driver"] == "Tenure bucket"]
worst_tenure = tenure.loc[tenure["churn_rate"].idxmax()]
best_tenure  = tenure.loc[tenure["churn_rate"].idxmin()]

# Exclude "No internet service" — they cannot have tech support, different population
tech = drivers[
    (drivers["driver"] == "Tech support add-on") &
    (drivers["segment"] != "No internet service")
]
worst_tech = tech.loc[tech["churn_rate"].idxmax()]
best_tech  = tech.loc[tech["churn_rate"].idxmin()]

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("📉 Churn Drivers")
st.markdown(
    "Not all customers leave for the same reason. "
    "Three traits explain most of the difference between customers who stay and customers who go."
)

# ---------------------------------------------------------------------------
# At a glance — one table showing all three drivers side by side
# so the reader sees the full picture before the detail below
# ---------------------------------------------------------------------------
st.markdown(
    "| Driver | Highest-churn group | Lowest-churn group |\n"
    "|--------|---------------------|--------------------|\n"
    f"| Contract type | {worst_contract['segment']}: **{worst_contract['churn_rate']}%** "
    f"| {best_contract['segment']}: **{best_contract['churn_rate']}%** |\n"
    f"| Time as a customer | {worst_tenure['segment']}: **{worst_tenure['churn_rate']}%** "
    f"| {best_tenure['segment']}: **{best_tenure['churn_rate']}%** |\n"
    f"| Tech support | {worst_tech['segment']}: **{worst_tech['churn_rate']}%** "
    f"| {best_tech['segment']}: **{best_tech['churn_rate']}%** |"
)
st.caption("Each row shows the worst-case and best-case segment for that driver. The gap tells the story.")

st.divider()

# ---------------------------------------------------------------------------
# Deep dive 1 — Contract type
# Gets the full chart treatment: it's the most actionable finding
# and the biggest gap (roughly 15× between month-to-month and two-year)
# ---------------------------------------------------------------------------
st.subheader("1. Contract type is the strongest predictor")

contract_data = contract.copy().sort_values("churn_rate", ascending=False)
# Combine churn rate + customer count into one bar label for full context
contract_data["bar_label"] = contract_data.apply(
    lambda r: f"{r['churn_rate']}%  ·  {int(r['n_customers']):,} customers", axis=1
)

fig = px.bar(
    contract_data,
    x="segment",
    y="churn_rate",
    color="churn_rate",
    color_continuous_scale=["#5CB85C", "#F0AD4E", "#D9534F"],
    text="bar_label",
    labels={"segment": "", "churn_rate": "Churn Rate (%)"},
    custom_data=["n_customers", "churned_customers"],
)
fig.update_traces(
    textposition="outside",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Churn rate: %{y}%<br>"
        "Customers: %{customdata[0]:,}<br>"
        "Churned: %{customdata[1]:,.0f}"
        "<extra></extra>"
    ),
)
fig.update_layout(
    showlegend=False,
    coloraxis_showscale=False,
    height=320,
    margin=dict(t=20, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(range=[0, contract_data["churn_rate"].max() * 1.3]),
)
st.plotly_chart(fig, use_container_width=True)

contract_multiplier = round(worst_contract["churn_rate"] / best_contract["churn_rate"])
st.markdown(
    f"Month-to-month customers churn at **{worst_contract['churn_rate']}%** — "
    f"roughly **{contract_multiplier}× the rate** of two-year contract holders "
    f"({best_contract['churn_rate']}%). "
    "Every customer moved from a month-to-month plan to an annual or two-year contract "
    "significantly lowers their likelihood of leaving. "
    "This is the single highest-impact retention lever in the dataset."
)

st.divider()

# ---------------------------------------------------------------------------
# Deep dives 2 & 3 — Tenure and tech support, side by side
# These don't need full charts — two numbers tell the story more clearly
# ---------------------------------------------------------------------------
col_tenure, col_tech = st.columns(2)

with col_tenure:
    st.subheader("2. New customers are the most vulnerable")
    st.caption(
        "**Tenure** is simply how many months someone has been a customer. "
        "The shorter the tenure, the less committed they are — they haven't yet decided to stay."
    )

    m1, m2 = st.columns(2)
    with m1:
        st.metric(
            "First 6 months",
            f"{worst_tenure['churn_rate']}%",
            help=f"{int(worst_tenure['n_customers']):,} customers in this group",
        )
    with m2:
        st.metric(
            "After 2 years",
            f"{best_tenure['churn_rate']}%",
            help=f"{int(best_tenure['n_customers']):,} customers in this group",
        )

    tenure_multiplier = round(worst_tenure["churn_rate"] / best_tenure["churn_rate"])
    st.markdown(
        f"Customers in their first 6 months churn at **{tenure_multiplier}× the rate** "
        "of those who have been around for 2+ years. "
        "Onboarding programs, early check-in calls, and first-month incentives "
        "target this window directly."
    )

with col_tech:
    st.subheader("3. Tech support creates stickiness")
    st.caption(
        "Customers with a tech support add-on have someone to call when things go wrong. "
        "That relationship makes them significantly less likely to leave."
    )

    m1, m2 = st.columns(2)
    with m1:
        st.metric(
            "No tech support",
            f"{worst_tech['churn_rate']}%",
            help=f"{int(worst_tech['n_customers']):,} customers in this group",
        )
    with m2:
        st.metric(
            "Has tech support",
            f"{best_tech['churn_rate']}%",
            help=f"{int(best_tech['n_customers']):,} customers in this group",
        )

    tech_multiplier = round(worst_tech["churn_rate"] / best_tech["churn_rate"])
    st.markdown(
        f"Customers without tech support churn at nearly **{tech_multiplier}× the rate** "
        "of those who have it. "
        "Offering tech support as a free trial to at-risk customers is a "
        "low-cost, high-impact retention tactic."
    )

st.divider()

# ---------------------------------------------------------------------------
# Monthly charges — note only, not a full chart
# It correlates with contract type rather than being an independent driver
# ---------------------------------------------------------------------------
charge_data = drivers[drivers["driver"] == "Monthly charge tier"]
high_charge  = charge_data.loc[charge_data["churn_rate"].idxmax()]
st.caption(
    f"**What about monthly charges?** High-charge customers do churn more "
    f"({high_charge['segment']}: {high_charge['churn_rate']}%), but this largely reflects "
    "that premium plans tend to be month-to-month — not an independent signal. "
    "For that reason it is not included in the risk score."
)

st.divider()

# ---------------------------------------------------------------------------
# Connecting statement — bridge to the Retention Priority List
# ---------------------------------------------------------------------------
st.info(
    "These three factors — **contract type**, **time as a customer**, and **tech support** — "
    "are the building blocks of the risk score. "
    "The next page uses all three together to flag specific customers "
    "and tell your team exactly who to call first."
)

st.divider()
st.subheader("Data Sources")
# st.expander: collapses to a single line when closed so it doesn't crowd the content above
sql_expander("02_churn_drivers.sql", "📄 Show SQL — 02_churn_drivers.sql")
