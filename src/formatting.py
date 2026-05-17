"""
formatting.py — Currency helpers and shared sidebar renderer.

The currency toggle relabels symbols only.  MonthlyCharges in the Telco
dataset is in USD; selecting JPY or EUR changes the display format but
does not apply an FX conversion rate.  This is intentional — demo data
should not misrepresent FX math.  Real client deployments can add a
conversion multiplier here once the client's base currency is known.
"""

from typing import Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Currency configuration
# ---------------------------------------------------------------------------
CURRENCIES = {
    "USD ($)": {"symbol": "$",  "prefix": True,  "decimals": 2},
    "JPY (¥)": {"symbol": "¥",  "prefix": True,  "decimals": 0},
    "EUR (€)": {"symbol": "€",  "prefix": True,  "decimals": 2},
}

RISK_COLORS = {
    "High":   "#D9534F",   # red
    "Medium": "#F0AD4E",   # amber
    "Low":    "#5CB85C",   # green
    "TOTAL":  "#6C757D",   # grey
}

TIER_ORDER = ["High", "Medium", "Low"]


def get_currency() -> str:
    """Return the currently selected currency key from session state."""
    return st.session_state.get("currency", "USD ($)")


def fmt_currency(value: float, currency: Optional[str] = None) -> str:
    """Format a numeric value with the selected currency symbol."""
    if currency is None:
        currency = get_currency()
    cfg = CURRENCIES[currency]
    dec = cfg["decimals"]
    sym = cfg["symbol"]
    formatted = f"{value:,.{dec}f}"
    return f"{sym}{formatted}" if cfg["prefix"] else f"{formatted}{sym}"


def fmt_pct(value: float, decimals: int = 1) -> str:
    """Format a float (already in percent units, e.g. 26.5) as '26.5%'."""
    return f"{value:.{decimals}f}%"


# ---------------------------------------------------------------------------
# Scoring rules explanation — shown in the sidebar "How this works" expander.
# This is the transparency selling point: the client can read every rule.
# ---------------------------------------------------------------------------
_SCORING_EXPLANATION = """
**How customers are scored**

Risk is assigned using three transparent rules — no machine learning,
no black box. Every reason is readable.

```
HIGH RISK (score 3)
  Month-to-month contract
  AND tenure < 12 months
  AND no tech support add-on

MEDIUM RISK (score 2)
  Month-to-month contract
  OR tenure < 6 months

LOW RISK (score 1)
  Everything else
  (annual/two-year contract + established customer)
```

These rules were derived from the churn driver analysis in the
**Churn Drivers** page — the segments with the highest observed churn
rates are used as the scoring criteria.

A client can adjust any threshold (e.g. change 12→18 months) and
re-run the analysis in minutes.  The scoring logic is in
`sql/03_customer_scoring.sql`, one screen of plain SQL.
"""


def render_sidebar(dfs: dict) -> None:
    """
    Render the shared sidebar present on every page.

    Parameters
    ----------
    dfs : dict
        The dict returned by data_loader.load_all(), used to show
        dataset info (row count, churn rate).
    """
    with st.sidebar:
        st.markdown("## Customer Retention Analytics")
        st.caption("Portfolio demo · IBM Telco Churn dataset")

        st.divider()

        # Dataset info
        st.markdown("**Dataset**")
        if "03_customer_scoring" in dfs:
            n = len(dfs["03_customer_scoring"])
            st.metric("Customers", f"{n:,}")
        if "01_data_quality" in dfs:
            dq = dfs["01_data_quality"]
            churn_row = dq[dq["check_name"] == "Overall churn rate"]
            if not churn_row.empty:
                st.metric("Overall churn rate", churn_row.iloc[0]["value"])
        st.caption("No date column in this dataset — tenure is in months.")

        st.divider()

        # Currency toggle
        st.markdown("**Display currency**")
        st.radio(
            label="currency_radio",
            options=list(CURRENCIES.keys()),
            key="currency",
            label_visibility="collapsed",
        )
        st.caption(
            "Relabels the symbol only.  Demo data is in USD.  "
            "Real deployments apply your own FX rates."
        )

        st.divider()

        # Transparency expander — the main selling point
        with st.expander("How this works", expanded=False):
            st.markdown(_SCORING_EXPLANATION)
