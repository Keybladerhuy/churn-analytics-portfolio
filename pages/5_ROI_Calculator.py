"""
pages/5_ROI_Calculator.py — Retention Program ROI Calculator

Models program cost vs. revenue recovered to produce a net ROI number
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

st.title("🧮 Retention Program ROI Calculator")
st.markdown(
    "Adjust the three inputs below to model the financial return of a retention program. "
    "Numbers on the right update instantly from your live data."
)

# ---------------------------------------------------------------------------
# Base numbers from the pipeline — High-risk tier only
# ---------------------------------------------------------------------------
high_row    = dfs["05_revenue_at_risk"][dfs["05_revenue_at_risk"]["risk_tier"] == "High"].iloc[0]
n_high_risk = int(high_row["n_customers"])
avg_mrr     = float(high_row["monthly_revenue"]) / n_high_risk  # avg MRR per high-risk customer

st.caption(
    f"Live data: **{n_high_risk:,} High-risk customers** · "
    f"avg {fmt_currency(avg_mrr, currency)} MRR each"
)
st.divider()

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
st.subheader("Program assumptions")

contact_pct = st.slider(
    "% of High-risk customers to contact",
    min_value=10, max_value=100, value=50, step=10, format="%d%%",
    help="How much of your high-risk segment your team reaches out to.",
)

retention_rate = st.slider(
    "Retention rate from outreach",
    min_value=5, max_value=60, value=20, step=5, format="%d%%",
    help="Of those contacted, the % you successfully keep.",
)

cost_per_outreach = st.number_input(
    "Cost per customer contacted (in selected display currency)",
    min_value=0, max_value=5000, value=50, step=10,
    help="All-in cost per customer: staff time, discounts, incentives.",
)

st.divider()

# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------
n_contacted       = round(n_high_risk * contact_pct / 100)
n_retained        = round(n_contacted * retention_rate / 100)
monthly_recovered = n_retained * avg_mrr
annual_recovered  = monthly_recovered * 12
program_cost      = n_contacted * cost_per_outreach
net_annual_roi    = annual_recovered - program_cost
roi_multiple      = annual_recovered / program_cost if program_cost > 0 else None

# ---------------------------------------------------------------------------
# KPI metrics row
# ---------------------------------------------------------------------------
st.subheader("Program results")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Customers contacted",      f"{n_contacted:,}")
c2.metric("Customers retained",       f"{n_retained:,}")
c3.metric("Monthly revenue recovered", fmt_currency(monthly_recovered, currency))
c4.metric("Annual revenue recovered",  fmt_currency(annual_recovered, currency))
c5.metric("Total program cost",        fmt_currency(program_cost, currency))

# ---------------------------------------------------------------------------
# Net ROI headline — the number a business owner takes into a budget meeting
# ---------------------------------------------------------------------------
if net_annual_roi > 0:
    multiple_str = f" — every $1 spent returns **${roi_multiple:.1f}**" if roi_multiple else ""
    st.success(
        f"**Net annual ROI: {fmt_currency(net_annual_roi, currency)}**{multiple_str}"
    )
else:
    st.warning(
        f"At these settings the program costs "
        f"**{fmt_currency(abs(net_annual_roi), currency)}** more than it recovers. "
        "Try lowering outreach cost or increasing the contact or retention rate."
    )

st.divider()

# ---------------------------------------------------------------------------
# Full breakdown table — for technical readers who want to verify the math
# ---------------------------------------------------------------------------
st.subheader("Full breakdown")

breakdown = pd.DataFrame({
    "Metric": [
        "High-risk customers (total)",
        "Customers contacted",
        "Customers retained",
        "Avg MRR per retained customer",
        "Monthly revenue recovered",
        "Annual revenue recovered",
        "Program cost (one-time)",
        "Net annual ROI",
    ],
    "Value": [
        f"{n_high_risk:,}",
        f"{n_contacted:,}  ({contact_pct}% of segment)",
        f"{n_retained:,}  ({retention_rate}% of contacted)",
        fmt_currency(avg_mrr, currency),
        fmt_currency(monthly_recovered, currency),
        fmt_currency(annual_recovered, currency),
        fmt_currency(program_cost, currency),
        fmt_currency(net_annual_roi, currency),
    ],
})

st.dataframe(breakdown, use_container_width=True, hide_index=True)

st.caption(
    "Program cost is modelled as a one-time outreach effort. "
    "Revenue recovery is annualised (monthly × 12). "
    "Source: `sql/05_revenue_at_risk.sql` · High-risk tier."
)
