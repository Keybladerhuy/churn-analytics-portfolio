"""
pages/3_Retention_Priority_List.py — Retention Priority List

The operational output of the analysis: every at-risk customer ranked
by urgency (risk level first, then monthly charges within each tier).
Designed to be worked through top to bottom by a retention team.
"""

import streamlit as st
import pandas as pd

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar, fmt_currency, RISK_COLORS, load_sql

con = get_connection()
dfs = load_all(con)

render_sidebar(dfs)

# @st.dialog must be at module level — Streamlit registers the modal when the
# script loads, and the trigger button (at the bottom) opens it on click.
@st.dialog("Scoring logic — SQL", width="large")
def _sql_dialog() -> None:
    # Two SQL files power this page: 03 scores every customer, 04 builds the list
    tab1, tab2 = st.tabs(["Customer scoring (03)", "Priority list (04)"])
    with tab1:
        st.caption("sql/03_customer_scoring.sql — assigns High / Medium / Low to every customer")
        st.code(load_sql("03_customer_scoring.sql"), language="sql")
    with tab2:
        st.caption("sql/04_retention_priority_list.sql — filters to at-risk customers, adds recommended actions")
        st.code(load_sql("04_retention_priority_list.sql"), language="sql")


priority = dfs["04_retention_priority_list"].copy()
currency  = st.session_state.get("currency", "USD ($)")

n_high   = int((priority["risk_tier"] == "High").sum())
n_medium = int((priority["risk_tier"] == "Medium").sum())

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("🎯 Retention Priority List")
st.markdown(
    "This is the action list. Every at-risk customer, ranked by urgency — "
    "highest-risk and highest-value first. Your team works from the top down."
)

# ---------------------------------------------------------------------------
# Context stats — give the reader a sense of scale before the filters appear
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    st.metric(
        "High-Risk Customers",
        f"{n_high:,}",
        help="All three warning signs present: month-to-month contract, under 12 months tenure, no tech support",
    )
with col2:
    st.metric(
        "Medium-Risk Customers",
        f"{n_medium:,}",
        help="At least one warning sign: month-to-month contract or under 6 months tenure",
    )

st.caption(
    "Sorted by risk level first, then by monthly charges within each tier — "
    "so the customers who would cost the most to lose are always at the top."
)

st.divider()

# ---------------------------------------------------------------------------
# Filters — default to High only so the list opens in a focused, actionable state
# ---------------------------------------------------------------------------
st.subheader("Filters")
fcol1, fcol2 = st.columns(2)

with fcol1:
    tier_filter = st.multiselect(
        "Risk Tier",
        options=["High", "Medium"],
        default=["High"],
        help="High = all three warning signs. Add Medium to broaden the list.",
    )

with fcol2:
    min_charge = float(priority["monthly_charges"].min())
    max_charge = float(priority["monthly_charges"].max())
    charge_range = st.slider(
        "Monthly Charges",
        min_value=min_charge,
        max_value=max_charge,
        value=(min_charge, max_charge),
        step=5.0,
        help="Filter by the customer's current monthly bill — useful for prioritising by revenue value",
    )

# Apply filters
filtered = priority[
    priority["risk_tier"].isin(tier_filter)
    & priority["monthly_charges"].between(charge_range[0], charge_range[1])
].copy()

st.markdown(
    f"Showing **{len(filtered):,}** customers "
    f"({filtered['risk_tier'].value_counts().get('High', 0):,} High, "
    f"{filtered['risk_tier'].value_counts().get('Medium', 0):,} Medium)"
)

st.divider()

# ---------------------------------------------------------------------------
# Table — actionable columns first, supporting diagnostic detail at the end
# ---------------------------------------------------------------------------
def color_risk_tier(val: str) -> str:
    color = RISK_COLORS.get(val, "#000")
    return f"color: {color}; font-weight: bold"


display = filtered.rename(columns={
    "risk_tier":            "Risk Tier",
    "monthly_charges":      "Monthly Charges",
    "primary_risk_factor":  "Why At Risk",
    "recommended_action":   "Recommended Action",
    "customer_id":          "Customer ID",
    "tenure_months":        "Tenure (months)",
    "contract":             "Contract",
    "tech_support":         "Tech Support",
})

display["Monthly Charges"] = display["Monthly Charges"].apply(
    lambda v: fmt_currency(v, currency)
)

# Reorder: what to do first, then who they are, then why (supporting detail)
display = display[[
    "Risk Tier", "Monthly Charges", "Why At Risk", "Recommended Action",
    "Customer ID", "Tenure (months)", "Contract", "Tech Support",
]]

styled = display.style.map(color_risk_tier, subset=["Risk Tier"])
st.dataframe(styled, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇ Export to CSV",
    data=csv_bytes,
    file_name="retention_priority_list.csv",
    mime="text/csv",
    help="Download the filtered list as a CSV file",
)

st.divider()

# ---------------------------------------------------------------------------
# Connecting statement — bridge to Revenue at Risk
# ---------------------------------------------------------------------------
st.info(
    "To see the revenue impact of these customers in dollar terms, "
    "head to the **Revenue at Risk** page."
)

st.divider()

# ---------------------------------------------------------------------------
# Data Sources — consistent with all other pages, lives at the bottom
# ---------------------------------------------------------------------------
st.subheader("Data Sources")
st.caption(
    "High = month-to-month + tenure <12 months + no tech support. "
    "Medium = month-to-month OR tenure <6 months."
)
# Button triggers the modal defined at the top of this file
if st.button("📄 Show scoring SQL", help="See the exact rules used to classify and rank these customers"):
    _sql_dialog()
