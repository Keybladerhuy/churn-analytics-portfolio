"""
pages/5_ROI_Calculator.py — Retention Program ROI Calculator

Models program cost vs. revenue recovered to produce a net return number
a business owner can take directly into a budget conversation.
"""

import pandas as pd
import streamlit as st

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar, fmt_currency

con = get_connection()
dfs = load_all(con)

render_sidebar(dfs)

currency = st.session_state.get("currency", "USD ($)")

high_row    = dfs["05_revenue_at_risk"][dfs["05_revenue_at_risk"]["risk_tier"] == "High"].iloc[0]
n_high_risk = int(high_row["n_customers"])
high_loss   = float(high_row["estimated_annual_loss"])
avg_mrr     = float(high_row["monthly_revenue"]) / n_high_risk

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("🧮 Retention Program ROI Calculator")
st.markdown(
    "The previous page showed the cost of doing nothing. "
    "This page models the other side: adjust the three assumptions below "
    "to see whether a retention program pays off."
)
st.caption(
    f"Starting point: **{n_high_risk:,} High-risk customers** — "
    f"estimated **{fmt_currency(high_loss, md=True)}** annual loss in that group "
    "if no action is taken."
)

st.divider()

# ---------------------------------------------------------------------------
# Inputs — three assumptions, each followed by a plain-English live result
# ---------------------------------------------------------------------------
st.subheader("Set your assumptions")

contact_pct = st.slider(
    "What % of High-risk customers does your team contact?",
    min_value=10, max_value=100, value=50, step=10, format="%d%%",
)
n_contacted = round(n_high_risk * contact_pct / 100)
st.caption(f"→ Your team reaches out to **{n_contacted:,} customers**")

retention_rate = st.slider(
    "Of those contacted, what % do you expect to keep?",
    min_value=5, max_value=60, value=20, step=5, format="%d%%",
    help="A realistic first campaign typically lands around 15–25%.",
)
n_retained = round(n_contacted * retention_rate / 100)
st.caption(f"→ **{n_retained:,} customers** successfully retained")

cost_per_outreach = st.number_input(
    "All-in cost per customer contacted",
    min_value=0, max_value=5000, value=50, step=10,
    help="Include staff time, any discounts offered, and incentives.",
)

# All derived values computed after inputs are set
monthly_recovered = n_retained * avg_mrr
annual_recovered  = monthly_recovered * 12
program_cost      = n_contacted * cost_per_outreach
net_annual_roi    = annual_recovered - program_cost
roi_multiple      = annual_recovered / program_cost if program_cost > 0 else None

st.caption(f"→ Total program cost: **{fmt_currency(program_cost, md=True)}**")

st.divider()

# ---------------------------------------------------------------------------
# Result — net ROI callout first, then the three supporting numbers below.
# The callout is the most important output on this page; it leads.
# ---------------------------------------------------------------------------
st.subheader("Result")

if net_annual_roi > 0:
    multiple_str = (
        f"\n\nEvery \\$1 spent returns **\\${roi_multiple:.1f}** in recovered revenue."
        if roi_multiple else ""
    )
    st.success(
        f"### Net Annual Return: {fmt_currency(net_annual_roi, currency, md=True)}"
        f"{multiple_str}"
    )
else:
    st.warning(
        f"### At these settings, the program costs more than it recovers.\n\n"
        f"The shortfall is **{fmt_currency(abs(net_annual_roi), currency, md=True)}**. "
        "Try lowering the cost per contact or increasing the retention rate."
    )

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Annual Revenue Recovered", fmt_currency(annual_recovered, currency))
with col2:
    st.metric("Total Program Cost", fmt_currency(program_cost, currency))
with col3:
    st.metric("Net Annual Return", fmt_currency(net_annual_roi, currency))

st.divider()

# ---------------------------------------------------------------------------
# Full calculation — collapsed by default; for readers who want to verify the math
# ---------------------------------------------------------------------------
with st.expander("Full calculation"):
    breakdown = pd.DataFrame({
        "Step": [
            "High-risk customers in dataset",
            "Customers contacted",
            "Customers retained",
            "Annual revenue recovered",
            "Total program cost",
            "Net annual return",
        ],
        "Formula": [
            "from dataset",
            f"{n_high_risk:,} × {contact_pct}%",
            f"{n_contacted:,} × {retention_rate}%",
            f"{n_retained:,} × {fmt_currency(avg_mrr, currency)} avg/mo × 12",
            f"{n_contacted:,} × {fmt_currency(cost_per_outreach, currency)} per contact",
            "annual recovered − program cost",
        ],
        "Value": [
            f"{n_high_risk:,}",
            f"{n_contacted:,}",
            f"{n_retained:,}",
            fmt_currency(annual_recovered, currency),
            fmt_currency(program_cost, currency),
            fmt_currency(net_annual_roi, currency),
        ],
    })
    st.dataframe(breakdown, use_container_width=True, hide_index=True)
    st.caption(
        "Revenue recovery = customers retained × average monthly revenue per customer × 12. "
        "Program cost = customers contacted × cost per contact."
    )

st.divider()

# ---------------------------------------------------------------------------
# Data Sources
# ---------------------------------------------------------------------------
st.subheader("Data Sources")
st.caption(
    "Base figures (High-risk customer count and average monthly revenue) come from "
    "sql/05_revenue_at_risk.sql. All other values are calculated from the assumptions above."
)
