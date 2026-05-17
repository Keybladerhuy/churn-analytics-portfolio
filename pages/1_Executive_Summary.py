"""
pages/1_Executive_Summary.py — Executive Summary

Three KPIs (past → present → cost), a loss chart, and a guide to the
rest of the report. No tables — those live on the downstream pages.
"""

import pandas as pd
import streamlit as st
import plotly.express as px

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar, fmt_currency, fmt_pct, RISK_COLORS, load_sql, sql_popover

con = get_connection()
dfs = load_all(con)

render_sidebar(dfs)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("📊 Executive Summary")
st.markdown(
    "Last year, 1 in 4 customers cancelled their service. "
    "Using those same records, we can see who is showing the same warning signs today — "
    "and what it will cost if nothing changes."
)

# ---------------------------------------------------------------------------
# Data — pulled once, used across KPIs, connecting sentence, and chart
# ---------------------------------------------------------------------------
rev5        = dfs["05_revenue_at_risk"]
total_row   = rev5[rev5["risk_tier"] == "TOTAL"].iloc[0]
high_row    = rev5[rev5["risk_tier"] == "High"].iloc[0]
med_row     = rev5[rev5["risk_tier"] == "Medium"].iloc[0]

total_customers = int(total_row["n_customers"])
churn_rate_pct  = float(total_row["baseline_churn_pct"])
churned_count   = round(total_customers * churn_rate_pct / 100)
at_risk_count   = int(high_row["n_customers"]) + int(med_row["n_customers"])
at_risk_loss    = float(high_row["estimated_annual_loss"]) + float(med_row["estimated_annual_loss"])

# ---------------------------------------------------------------------------
# KPI row — three numbers, read left to right as: past → present → cost
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Left Last Year",
        f"{churned_count:,}",
        delta=f"{fmt_pct(churn_rate_pct)} of all customers",
        delta_color="inverse",
        help="Customers who already cancelled — the historical baseline we use to identify who is next",
    )
with col2:
    st.metric(
        "At Risk Right Now",
        f"{at_risk_count:,}",
        help="Customers showing the same warning signs as those who already left (High + Medium risk combined)",
    )
with col3:
    st.metric(
        "Expected Annual Loss",
        fmt_currency(at_risk_loss),
        help=f"Estimated revenue lost per year if at-risk customers churn at the observed {fmt_pct(churn_rate_pct)} rate",
    )

st.divider()

# ---------------------------------------------------------------------------
# Connecting sentence — ties the three KPIs together before the chart
# ---------------------------------------------------------------------------
st.markdown(
    f"Those **{at_risk_count:,} customers** match the profile of the **{churned_count:,} who already left**. "
    f"If they leave at the same rate, the business loses **{fmt_currency(at_risk_loss, md=True)} this year**. "
    f"Here is where that risk is concentrated:"
)

# ---------------------------------------------------------------------------
# Horizontal bar chart — estimated annual loss by risk group
#
# Bars are ordered High (top) then Medium (bottom). Bar length = expected
# dollar loss; the label shows the dollar figure + customer count so the
# reader gets both dimensions without needing a separate table.
# ---------------------------------------------------------------------------
chart_data = rev5[rev5["risk_tier"].isin(["High", "Medium"])].copy()

# Categorical order: Medium first so High renders at the top in Plotly
chart_data["risk_tier"] = pd.Categorical(
    chart_data["risk_tier"], categories=["Medium", "High"], ordered=True
)
chart_data = chart_data.sort_values("risk_tier")
chart_data["bar_label"] = chart_data.apply(
    lambda r: f"{fmt_currency(r['estimated_annual_loss'])}  ({int(r['n_customers']):,} customers)",
    axis=1,
)

fig = px.bar(
    chart_data,
    x="estimated_annual_loss",
    y="risk_tier",
    color="risk_tier",
    color_discrete_map=RISK_COLORS,
    orientation="h",
    text="bar_label",
    labels={"estimated_annual_loss": "", "risk_tier": ""},
)
fig.update_traces(textposition="outside")
fig.update_layout(
    showlegend=False,
    height=180,
    margin=dict(t=10, b=10, l=10, r=10),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(
        # Extra headroom so the outside labels are never clipped
        range=[0, chart_data["estimated_annual_loss"].max() * 1.7],
        showticklabels=False,
        showgrid=False,
        zeroline=False,
    ),
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    f"Loss estimate applies the observed {fmt_pct(churn_rate_pct)} churn rate to each group's annual revenue. "
    "Low-risk customers are not shown — see the Revenue at Risk page for a full breakdown."
)

st.divider()

# ---------------------------------------------------------------------------
# What this report covers — guides the reader to each downstream page
# ---------------------------------------------------------------------------
st.subheader("What this report covers")
st.markdown(
    "- **Churn Drivers** — which customer characteristics are most associated with leaving, and by how much\n"
    "- **Retention Priority List** — every at-risk customer ranked by urgency, with a plain-English recommended action\n"
    "- **Revenue at Risk** — full financial breakdown of expected losses by risk tier\n"
    "- **ROI Calculator** — model a retention program: what does it cost, and does it pay off?"
)

st.divider()

# ---------------------------------------------------------------------------
# Data Sources
# ---------------------------------------------------------------------------
st.subheader("Data Sources")
st.caption("All figures are derived from two SQL queries — no black box.")

# Single popover with tabs keeps both SQL files accessible without two buttons
with st.popover("📄 Show SQL used on this page"):
    tab1, tab2 = st.tabs(["Customer scoring (03)", "Revenue at risk (05)"])
    with tab1:
        st.caption("sql/03_customer_scoring.sql — assigns High / Medium / Low risk to every customer")
        st.code(load_sql("03_customer_scoring.sql"), language="sql")
    with tab2:
        st.caption("sql/05_revenue_at_risk.sql — aggregates revenue by risk tier and estimates losses")
        st.code(load_sql("05_revenue_at_risk.sql"), language="sql")
