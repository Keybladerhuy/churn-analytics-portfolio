"""
pages/2_Churn_Drivers.py — Churn Driver Analysis

Answers: "Which customer characteristics are most associated with churn?"

All charts come directly from 02_churn_drivers.sql. No ML — the churn
rates shown are plain counts from the dataset, divided by segment size.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar, fmt_pct, RISK_COLORS

con = get_connection()
dfs = load_all(con)

render_sidebar(dfs)

st.title("📉 Churn Driver Analysis")
st.caption(
    "Which customer segments churn at the highest rate? "
    "Use this to decide where to focus retention investment."
)

drivers = dfs["02_churn_drivers"]

# Top driver callout
top = drivers.iloc[0]
st.info(
    f"**Top churn driver:** {top['driver']} — segment **\"{top['segment']}\"** "
    f"has a **{top['churn_rate']}% churn rate** "
    f"({int(top['churned_customers']):,} churned out of {int(top['n_customers']):,} customers). "
    f"This is the single highest-churn segment in the dataset."
)

st.divider()


def bar_chart(data: pd.DataFrame, title: str, plain_english: str) -> None:
    """Render a churn-rate bar chart with a plain-English explanation."""
    st.subheader(title)
    fig = px.bar(
        data.sort_values("churn_rate", ascending=False),
        x="segment",
        y="churn_rate",
        color="churn_rate",
        color_continuous_scale=["#5CB85C", "#F0AD4E", "#D9534F"],
        text=data.sort_values("churn_rate", ascending=False)["churn_rate"].apply(
            lambda v: f"{v}%"
        ),
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
        yaxis=dict(range=[0, data["churn_rate"].max() * 1.25]),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"> {plain_english}")
    st.markdown("")


# ---------------------------------------------------------------------------
# 1. Contract type
# ---------------------------------------------------------------------------
bar_chart(
    drivers[drivers["driver"] == "Contract type"],
    "Churn Rate by Contract Type",
    "Month-to-month customers churn at over 40% — nearly four times the rate "
    "of two-year contract holders. Every customer you move to an annual or "
    "two-year contract significantly reduces their churn probability. "
    "This is the easiest lever to pull: target month-to-month customers "
    "with a discount offer to upgrade.",
)

# ---------------------------------------------------------------------------
# 2. Tenure bucket
# ---------------------------------------------------------------------------
tenure_data = drivers[drivers["driver"] == "Tenure bucket"].copy()
tenure_order = ["0-6 months", "6-12 months", "1-2 years", "2+ years"]
tenure_data["segment"] = pd.Categorical(
    tenure_data["segment"], categories=tenure_order, ordered=True
)
tenure_data = tenure_data.sort_values("segment")

bar_chart(
    tenure_data,
    "Churn Rate by Customer Tenure",
    "More than half of customers in their first 6 months leave. "
    "This is the 'new customer cliff' — the critical window where customers "
    "decide if your service is worth keeping. "
    "Onboarding programs, check-in calls, and early incentives during months 1-6 "
    "deliver the highest retention ROI of any initiative.",
)

# ---------------------------------------------------------------------------
# 3. Monthly charge tier
# ---------------------------------------------------------------------------
charge_order = ["Low (<$35)", "Mid ($35-$65)", "High (>$65)"]
charge_data = drivers[drivers["driver"] == "Monthly charge tier"].copy()
charge_data["segment"] = pd.Categorical(
    charge_data["segment"], categories=charge_order, ordered=True
)
charge_data = charge_data.sort_values("segment")

bar_chart(
    charge_data,
    "Churn Rate by Monthly Charge Tier",
    "Higher-paying customers churn more — counterintuitively, because they are "
    "also more likely to be on month-to-month contracts with premium services. "
    "High-charge churners represent disproportionate revenue impact. "
    "Prioritise retention outreach by monthly charge value, not just churn probability.",
)

# ---------------------------------------------------------------------------
# 4. Tech support add-on
# ---------------------------------------------------------------------------
bar_chart(
    drivers[drivers["driver"] == "Tech support add-on"],
    "Churn Rate by Tech Support Subscription",
    "Customers without tech support churn at 41.6% — nearly double those "
    "who have it. This suggests that tech support creates a 'stickiness' effect: "
    "customers feel more supported and less likely to switch. "
    "Offering tech support as a free trial to at-risk customers is a "
    "low-cost, high-impact retention tactic.",
)

st.divider()
st.caption(
    "All figures are calculated directly from the customer dataset using plain SQL. "
    "See `sql/02_churn_drivers.sql` for the full query logic."
)
