"""
pages/0_About_the_Data.py — About the Data

Introduces the dataset and sets up the narrative before any analysis begins.
Shows raw records, explains columns in plain English, and flags the one
known data quality issue.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import get_connection, load_all
from src.formatting import render_sidebar

con = get_connection()
dfs = load_all(con)
render_sidebar(dfs)

raw = pd.read_csv("data/telco_customer_churn.csv")

st.title("📋 About the Data")
st.markdown(
    "This analysis is built on 7,043 real customer records from a telecommunications company. "
    "Each row is one customer — their contract, services, monthly bill, and whether they left."
)

st.info(
    "**The central question:** which customers are about to leave — or 'churn', "
    "meaning cancel or not renew their service — and what can we do about it before they go?"
)

# ---------------------------------------------------------------------------
# Churn split KPIs + donut chart
# ---------------------------------------------------------------------------
n_total = len(raw)
n_churned = int((raw["Churn"] == "Yes").sum())
n_retained = n_total - n_churned
pct_churned = round(n_churned / n_total * 100, 1)
pct_retained = round(n_retained / n_total * 100, 1)

kpi1, kpi2, kpi3, chart_col = st.columns([1, 1, 1, 2])

with kpi1:
    st.metric("Total Customers", f"{n_total:,}")
with kpi2:
    st.metric(
        "Churned",
        f"{n_churned:,}",
        delta=f"{pct_churned}% of total",
        delta_color="inverse",
    )
with kpi3:
    st.metric(
        "Retained",
        f"{n_retained:,}",
        delta=f"{pct_retained}% of total",
        delta_color="normal",
    )

with chart_col:
    fig = px.pie(
        values=[n_churned, n_retained],
        names=["Churned", "Retained"],
        hole=0.6,
    )
    fig.update_traces(
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>%{value:,} customers<extra></extra>",
        marker=dict(colors=["#D9534F", "#5CB85C"]),
    )
    fig.update_layout(
        height=180,
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Column guide
# ---------------------------------------------------------------------------
st.subheader("What each column means")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Who the customer is**")
    st.markdown(
        "| Column | Meaning |\n"
        "|--------|---------|\n"
        "| `customerID` | Unique identifier |\n"
        "| `gender` | Male / Female |\n"
        "| `SeniorCitizen` | Whether the customer is 65+ |\n"
        "| `Partner` | Has a partner |\n"
        "| `Dependents` | Has dependents |\n"
        "| `tenure` | Months as a customer |"
    )

    st.markdown("**How they pay**")
    st.markdown(
        "| Column | Meaning |\n"
        "|--------|---------|\n"
        "| `Contract` | Month-to-month, one-year, or two-year |\n"
        "| `PaperlessBilling` | Receives bills by email |\n"
        "| `PaymentMethod` | How they pay each month |\n"
        "| `MonthlyCharges` | Current monthly bill |\n"
        "| `TotalCharges` | Lifetime spend |"
    )

with col_right:
    st.markdown("**Services they use**")
    st.markdown(
        "| Column | Meaning |\n"
        "|--------|---------|\n"
        "| `PhoneService` | Has a phone line |\n"
        "| `MultipleLines` | Has more than one line |\n"
        "| `InternetService` | DSL, Fiber optic, or None |\n"
        "| `OnlineSecurity` | Security add-on |\n"
        "| `OnlineBackup` | Backup add-on |\n"
        "| `DeviceProtection` | Device protection add-on |\n"
        "| `TechSupport` | Tech support add-on |\n"
        "| `StreamingTV` | TV streaming add-on |\n"
        "| `StreamingMovies` | Movie streaming add-on |"
    )

    st.markdown("**The outcome we're analysing**")
    st.markdown(
        "| Column | Meaning |\n"
        "|--------|---------|\n"
        "| `Churn` | Whether the customer left — Yes or No |"
    )

st.divider()

# ---------------------------------------------------------------------------
# Data quality note
# ---------------------------------------------------------------------------
st.subheader("Known data issues")
st.info(
    "11 customers have a blank `TotalCharges` value. "
    "All 11 have `tenure = 0` — they signed up but were never billed. "
    "This is handled automatically before any analysis runs."
)

st.divider()

# ---------------------------------------------------------------------------
# Raw data sample
# ---------------------------------------------------------------------------
st.subheader("Sample rows — the raw data")

st.caption(
    f"{len(raw):,} customers · {raw.shape[1]} columns · source: IBM Telco Churn dataset"
)
st.dataframe(raw.head(20), use_container_width=True, hide_index=True)
