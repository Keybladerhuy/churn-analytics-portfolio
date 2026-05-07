"""
pages/3_Retention_Priority_List.py — Retention Priority List

A filterable, exportable table of at-risk customers sorted by
priority (High risk + highest monthly charges first).

This is the operational output: the retention team uses this list
to decide who to call and what to offer.
"""

import streamlit as st
import pandas as pd

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar, fmt_currency, RISK_COLORS

con = get_connection()
dfs = load_all(con)

render_sidebar(dfs)

st.title("🎯 Retention Priority List")
st.caption(
    "High and Medium risk customers, ranked by priority. "
    "Use this list to assign outreach tasks to your retention team."
)
st.caption("**This list updates automatically when new customer data is loaded.**")

priority = dfs["04_retention_priority_list"].copy()
currency  = st.session_state.get("currency", "USD ($)")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
st.subheader("Filters")
fcol1, fcol2, fcol3 = st.columns(3)

with fcol1:
    tier_filter = st.multiselect(
        "Risk Tier",
        options=["High", "Medium"],
        default=["High", "Medium"],
    )

with fcol2:
    contract_filter = st.multiselect(
        "Contract Type",
        options=sorted(priority["contract"].unique()),
        default=sorted(priority["contract"].unique()),
    )

with fcol3:
    min_charge = float(priority["monthly_charges"].min())
    max_charge = float(priority["monthly_charges"].max())
    charge_range = st.slider(
        "Monthly Charges",
        min_value=min_charge,
        max_value=max_charge,
        value=(min_charge, max_charge),
        step=5.0,
    )

# Apply filters
filtered = priority[
    priority["risk_tier"].isin(tier_filter)
    & priority["contract"].isin(contract_filter)
    & priority["monthly_charges"].between(charge_range[0], charge_range[1])
].copy()

st.markdown(
    f"Showing **{len(filtered):,}** customers "
    f"({filtered['risk_tier'].value_counts().get('High', 0):,} High, "
    f"{filtered['risk_tier'].value_counts().get('Medium', 0):,} Medium)"
)

st.divider()

# ---------------------------------------------------------------------------
# Color-code the risk tier column
# ---------------------------------------------------------------------------
def color_risk_tier(val: str) -> str:
    color = RISK_COLORS.get(val, "#000")
    return f"color: {color}; font-weight: bold"


# Format for display
display = filtered.rename(columns={
    "customer_id":        "Customer ID",
    "risk_tier":          "Risk Tier",
    "monthly_charges":    "Monthly Charges",
    "tenure_months":      "Tenure (months)",
    "contract":           "Contract",
    "tech_support":       "Tech Support",
    "primary_risk_factor": "Why At Risk",
    "recommended_action": "Recommended Action",
})

display["Monthly Charges"] = display["Monthly Charges"].apply(
    lambda v: fmt_currency(v, currency)
)

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
st.caption(
    "Scoring logic: High = month-to-month + tenure <12mo + no tech support. "
    "Medium = month-to-month OR tenure <6mo. "
    "See `sql/03_customer_scoring.sql` for the full CASE logic."
)
