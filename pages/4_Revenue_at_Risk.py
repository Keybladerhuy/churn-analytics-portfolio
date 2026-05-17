"""
pages/4_Revenue_at_Risk.py — Revenue at Risk

Quantifies the cost of inaction: if at-risk customers leave at the
historical rate, how much revenue does the business lose?
Loss is the focus — revenue is shown for context only.
"""

import pandas as pd
import streamlit as st
import plotly.express as px

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar, fmt_currency, fmt_pct, RISK_COLORS, sql_popover

con = get_connection()
dfs = load_all(con)

render_sidebar(dfs)

rev      = dfs["05_revenue_at_risk"]
currency = st.session_state.get("currency", "USD ($)")

total_row = rev[rev["risk_tier"] == "TOTAL"].iloc[0]
high_row  = rev[rev["risk_tier"] == "High"].iloc[0]
med_row   = rev[rev["risk_tier"] == "Medium"].iloc[0]
tier_data = rev[rev["risk_tier"] != "TOTAL"].copy()

total_loss = float(total_row["estimated_annual_loss"])
high_loss  = float(high_row["estimated_annual_loss"])
med_loss   = float(med_row["estimated_annual_loss"])
churn_pct  = float(total_row["baseline_churn_pct"])

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("💰 Revenue at Risk")
st.markdown(
    "The Retention Priority List in dollar terms. "
    f"If at-risk customers leave at the historical rate, the business loses an estimated "
    f"**{fmt_currency(total_loss, md=True)} this year** — before anything is done."
)

# ---------------------------------------------------------------------------
# Three headline stat blocks — the cost of inaction at a glance
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Estimated Annual Loss",
        fmt_currency(total_loss),
        help=f"All customers combined, applying the {fmt_pct(churn_pct)} observed churn rate",
    )
with col2:
    st.metric(
        "High-Risk Annual Loss",
        fmt_currency(high_loss),
        help=f"{int(high_row['n_customers']):,} customers showing all three warning signs",
    )
with col3:
    st.metric(
        "Medium-Risk Annual Loss",
        fmt_currency(med_loss),
        help=f"{int(med_row['n_customers']):,} customers showing at least one warning sign",
    )

st.divider()

# ---------------------------------------------------------------------------
# Horizontal bar chart — estimated annual loss by tier
# Bar length = expected dollar loss; consistent with the Executive Summary chart
# ---------------------------------------------------------------------------
st.subheader("Estimated Annual Loss by Risk Group")

chart_data = tier_data.copy()
# "Low" first so "High" renders at the top in Plotly's bottom-up horizontal axis
chart_data["risk_tier"] = pd.Categorical(
    chart_data["risk_tier"], categories=["Low", "Medium", "High"], ordered=True
)
chart_data = chart_data.sort_values("risk_tier")
chart_data["bar_label"] = chart_data.apply(
    lambda r: f"{fmt_currency(r['estimated_annual_loss'])}  ({int(r['n_customers']):,} customers)",
    axis=1,
)
# Pre-format hover values so they respect the selected display currency
chart_data["loss_fmt"]   = chart_data["estimated_annual_loss"].apply(lambda v: fmt_currency(float(v), currency))
chart_data["rev_fmt"]    = chart_data["annual_revenue"].apply(lambda v: fmt_currency(float(v), currency))

fig = px.bar(
    chart_data,
    x="estimated_annual_loss",
    y="risk_tier",
    color="risk_tier",
    color_discrete_map=RISK_COLORS,
    orientation="h",
    text="bar_label",
    custom_data=["loss_fmt", "rev_fmt", "n_customers"],
    labels={"estimated_annual_loss": "", "risk_tier": ""},
)
fig.update_traces(
    textposition="outside",
    # Hover shows annual revenue so readers can see the full picture without a table
    hovertemplate=(
        "<b>%{y} risk</b><br>"
        "Estimated annual loss: %{customdata[0]}<br>"
        "Annual revenue: %{customdata[1]}<br>"
        "Customers: %{customdata[2]:,.0f}"
        "<extra></extra>"
    ),
)
fig.update_layout(
    showlegend=False,
    height=240,
    margin=dict(t=10, b=10, l=10, r=10),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(
        range=[0, chart_data["estimated_annual_loss"].max() * 1.7],
        showticklabels=False,
        showgrid=False,
        zeroline=False,
    ),
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    f"Based on the {fmt_pct(churn_pct)} observed churn rate applied to each group's annual revenue. "
    "This is a conservative estimate — High-risk customers are disproportionately likely to churn, "
    "so real losses in that tier will likely be higher."
)

st.divider()

# ---------------------------------------------------------------------------
# Connecting statement — bridge to the ROI Calculator
# ---------------------------------------------------------------------------
st.info(
    "These are the stakes. The next page models what a retention program costs — "
    "and whether the revenue recovered justifies the investment."
)

st.divider()

# ---------------------------------------------------------------------------
# Data Sources — standard pattern consistent with other pages
# ---------------------------------------------------------------------------
st.subheader("Data Sources")
st.caption(
    "Revenue figures are based on current MonthlyCharges in the dataset. "
    "Loss estimates apply the observed churn rate uniformly — use as a conservative floor."
)
sql_popover("05_revenue_at_risk.sql", "📄 Show SQL")
