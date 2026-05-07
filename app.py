"""
app.py — Page 1: Executive Summary

Entry point for the Streamlit multi-page dashboard.
The pages/ directory contains the other three pages;
Streamlit auto-discovers them.
"""

import pandas as pd
import streamlit as st
import plotly.express as px

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar, fmt_currency, fmt_pct, RISK_COLORS, TIER_ORDER

st.set_page_config(
    page_title="Customer Retention Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load data (cached — runs once per session)
# ---------------------------------------------------------------------------
con = get_connection()
dfs = load_all(con)

render_sidebar(dfs)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("📊 Executive Summary")
st.caption("Customer retention analytics · IBM Telco Churn sample dataset")

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
rev5 = dfs["05_revenue_at_risk"]
total_row = rev5[rev5["risk_tier"] == "TOTAL"].iloc[0]
high_row  = rev5[rev5["risk_tier"] == "High"].iloc[0]
med_row   = rev5[rev5["risk_tier"] == "Medium"].iloc[0]

total_customers = int(total_row["n_customers"])
churn_rate_pct  = float(total_row["baseline_churn_pct"])
at_risk_mrr     = float(high_row["monthly_revenue"]) + float(med_row["monthly_revenue"])

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Customers", f"{total_customers:,}")
with col2:
    st.metric("Overall Churn Rate", fmt_pct(churn_rate_pct))
with col3:
    st.metric(
        "High-Risk Monthly Revenue",
        fmt_currency(high_row["monthly_revenue"]),
        help="Monthly recurring revenue from High-risk customers",
    )
with col4:
    st.metric(
        "Total At-Risk MRR (High + Medium)",
        fmt_currency(at_risk_mrr),
        help="Monthly revenue from customers classified as High or Medium risk",
    )

st.divider()

# ---------------------------------------------------------------------------
# Customer distribution chart
# ---------------------------------------------------------------------------
col_chart, col_insight = st.columns([3, 2])

with col_chart:
    st.subheader("Customer Distribution by Risk Tier")

    score3 = dfs["03_customer_scoring"]
    tier_counts = (
        score3.groupby("risk_tier")
              .size()
              .reset_index(name="count")
    )
    # Ensure consistent tier order
    tier_counts["risk_tier"] = pd.Categorical(
        tier_counts["risk_tier"], categories=TIER_ORDER, ordered=True
    )
    tier_counts = tier_counts.sort_values("risk_tier")
    tier_counts["pct"] = (tier_counts["count"] / tier_counts["count"].sum() * 100).round(1)

    fig = px.bar(
        tier_counts,
        x="risk_tier",
        y="count",
        color="risk_tier",
        color_discrete_map=RISK_COLORS,
        text=tier_counts["pct"].apply(lambda x: f"{x}%"),
        labels={"risk_tier": "Risk Tier", "count": "Customers"},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False,
        height=320,
        margin=dict(t=20, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_insight:
    st.subheader("Key Insight")

    # Auto-generate insight from real data
    drivers = dfs["02_churn_drivers"]
    top_driver = drivers.iloc[0]
    high_n = int(high_row["n_customers"])
    high_pct = round(high_n / total_customers * 100, 1)
    at_risk_annual = float(high_row["annual_revenue"]) + float(med_row["annual_revenue"])

    insight = (
        f"**{top_driver['segment']}** customers churn at "
        f"**{top_driver['churn_rate']}%** — the highest of any segment. "
        f"Your **{high_n:,} High-risk customers** ({high_pct}% of total) "
        f"represent {fmt_currency(high_row['annual_revenue'])} in annual recurring revenue."
    )
    st.info(insight)

    st.markdown("**Revenue at risk (annual estimate)**")
    for _, row in rev5[rev5["risk_tier"] != "TOTAL"].iterrows():
        tier = row["risk_tier"]
        color = RISK_COLORS.get(tier, "#888")
        st.markdown(
            f"<span style='color:{color};font-weight:bold'>{tier}</span>: "
            f"{fmt_currency(row['estimated_annual_loss'])} estimated loss",
            unsafe_allow_html=True,
        )

    st.caption(
        "Loss estimate uses the 26.5% observed churn rate as a baseline. "
        "Real loss may differ. See Revenue at Risk page for full detail."
    )

st.divider()

# ---------------------------------------------------------------------------
# Revenue at risk summary table
# ---------------------------------------------------------------------------
st.subheader("Revenue at Risk — Summary")

display = rev5.copy()
display = display.rename(columns={
    "risk_tier":               "Risk Tier",
    "n_customers":             "Customers",
    "monthly_revenue":         "Monthly Revenue",
    "annual_revenue":          "Annual Revenue",
    "baseline_churn_pct":      "Churn Rate (%)",
    "estimated_monthly_loss":  "Est. Monthly Loss",
    "estimated_annual_loss":   "Est. Annual Loss",
})

currency = st.session_state.get("currency", "USD ($)")
for col in ["Monthly Revenue", "Annual Revenue", "Est. Monthly Loss", "Est. Annual Loss"]:
    display[col] = display[col].apply(lambda v: fmt_currency(v, currency))

st.dataframe(display, use_container_width=True, hide_index=True)
