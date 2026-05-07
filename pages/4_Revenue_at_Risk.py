"""
pages/4_Revenue_at_Risk.py — Revenue at Risk

Translates customer churn risk into financial impact.
Includes an interactive ROI calculator: "if you retain X% of
high-risk customers, how much revenue do you recover?"
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar, fmt_currency, fmt_pct, RISK_COLORS, TIER_ORDER

con = get_connection()
dfs = load_all(con)

render_sidebar(dfs)

st.title("💰 Revenue at Risk")
st.caption(
    "How much monthly recurring revenue is exposed to churn? "
    "Use these numbers to quantify the business case for a retention program."
)

rev = dfs["05_revenue_at_risk"]
currency = st.session_state.get("currency", "USD ($)")

tier_data  = rev[rev["risk_tier"] != "TOTAL"].copy()
total_row  = rev[rev["risk_tier"] == "TOTAL"].iloc[0]
high_row   = rev[rev["risk_tier"] == "High"].iloc[0]

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
st.subheader("Revenue Summary by Risk Tier")

display = tier_data.copy()
display["risk_tier"] = pd.Categorical(
    display["risk_tier"], categories=TIER_ORDER, ordered=True
)
display = display.sort_values("risk_tier")

# Add a totals row for display
totals_display = total_row.to_frame().T
display = pd.concat([display, totals_display], ignore_index=True)

display = display.rename(columns={
    "risk_tier":              "Risk Tier",
    "n_customers":            "Customers",
    "monthly_revenue":        "Monthly Revenue",
    "annual_revenue":         "Annual Revenue",
    "baseline_churn_pct":     "Observed Churn %",
    "estimated_monthly_loss": "Est. Monthly Loss",
    "estimated_annual_loss":  "Est. Annual Loss",
})

for col in ["Monthly Revenue", "Annual Revenue", "Est. Monthly Loss", "Est. Annual Loss"]:
    display[col] = display[col].apply(lambda v: fmt_currency(float(v), currency))

display["Customers"] = display["Customers"].apply(lambda v: f"{int(v):,}")

st.dataframe(display, use_container_width=True, hide_index=True)

st.caption(
    "Loss estimates apply the observed 26.5% dataset churn rate uniformly across tiers. "
    "Real-world loss for High-risk customers will likely be higher — "
    "use these as a conservative floor for business-case planning."
)

st.divider()

# ---------------------------------------------------------------------------
# Bar chart: Monthly and Annual Revenue at Risk by Tier
# ---------------------------------------------------------------------------
st.subheader("Revenue at Risk by Tier")

chart_data = tier_data.copy()
chart_data["risk_tier"] = pd.Categorical(
    chart_data["risk_tier"], categories=TIER_ORDER, ordered=True
)
chart_data = chart_data.sort_values("risk_tier")

fig = go.Figure()
fig.add_trace(go.Bar(
    name="Monthly Revenue",
    x=chart_data["risk_tier"],
    y=chart_data["monthly_revenue"],
    marker_color=[RISK_COLORS[t] for t in chart_data["risk_tier"]],
    opacity=0.6,
    hovertemplate="<b>%{x}</b><br>Monthly: %{y:,.0f}<extra></extra>",
))
fig.add_trace(go.Bar(
    name="Annual Revenue",
    x=chart_data["risk_tier"],
    y=chart_data["annual_revenue"],
    marker_color=[RISK_COLORS[t] for t in chart_data["risk_tier"]],
    hovertemplate="<b>%{x}</b><br>Annual: %{y:,.0f}<extra></extra>",
))
fig.update_layout(
    barmode="group",
    height=350,
    margin=dict(t=20, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    yaxis_title="Revenue",
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# ROI Calculator
# ---------------------------------------------------------------------------
st.subheader("🧮 Retention ROI Calculator")
st.markdown(
    "Slide to see how much revenue you recover by retaining a percentage "
    "of your **High-risk** customers."
)

high_monthly = float(high_row["monthly_revenue"])
high_annual  = float(high_row["annual_revenue"])

retention_pct = st.slider(
    "If you retain this % of High-risk customers:",
    min_value=5,
    max_value=80,
    value=20,
    step=5,
    format="%d%%",
)

recovered_monthly = high_monthly * retention_pct / 100
recovered_annual  = high_annual  * retention_pct / 100

rc1, rc2 = st.columns(2)
with rc1:
    st.metric(
        f"Recovered monthly revenue ({retention_pct}% retention)",
        fmt_currency(recovered_monthly, currency),
    )
with rc2:
    st.metric(
        "Recovered annual revenue",
        fmt_currency(recovered_annual, currency),
    )

st.success(
    f"Retaining just **{retention_pct}% of your {int(high_row['n_customers']):,} "
    f"High-risk customers** would recover "
    f"**{fmt_currency(recovered_annual, currency)} per year** — "
    f"before accounting for the higher-than-average churn probability in this segment."
)

st.divider()
st.caption(
    "Source: `sql/05_revenue_at_risk.sql`. "
    "Revenue figures are based on current MonthlyCharges in the dataset. "
    "ROI calculations assume retention efforts succeed uniformly across the segment."
)
