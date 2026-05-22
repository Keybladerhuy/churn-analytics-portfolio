"""
formatting.py — Currency helpers and shared sidebar renderer.

The currency toggle relabels symbols only.  MonthlyCharges in the Telco
dataset is in USD; selecting JPY or EUR changes the display format but
does not apply an FX conversion rate.  This is intentional — demo data
should not misrepresent FX math.  Real client deployments can add a
conversion multiplier here once the client's base currency is known.
"""

from pathlib import Path
from typing import Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Currency configuration
# ---------------------------------------------------------------------------
CURRENCIES = {
    "USD ($)": {"symbol": "$",  "prefix": True,  "decimals": 0},
    "JPY (¥)": {"symbol": "¥",  "prefix": True,  "decimals": 0},
    "EUR (€)": {"symbol": "€",  "prefix": True,  "decimals": 0},
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


def fmt_currency(value: float, currency: Optional[str] = None, md: bool = False) -> str:
    """Format a numeric value with the selected currency symbol.

    Pass md=True when embedding in a Streamlit markdown context (st.info,
    st.markdown, st.success, st.warning, st.caption) so the $ sign is
    escaped as \\$ and Streamlit does not treat it as a LaTeX delimiter.
    st.metric renders plain text and does not need escaping.
    """
    if currency is None:
        currency = get_currency()
    cfg = CURRENCIES[currency]
    dec = cfg["decimals"]
    sym = cfg["symbol"]
    formatted = f"{value:,.{dec}f}"
    result = f"{sym}{formatted}" if cfg["prefix"] else f"{formatted}{sym}"
    # Only $ triggers LaTeX in Streamlit; ¥ and € are safe as-is
    return result.replace("$", r"\$") if (md and sym == "$") else result


def fmt_pct(value: float, decimals: int = 1) -> str:
    """Format a float (already in percent units, e.g. 26.5) as '26.5%'."""
    return f"{value:.{decimals}f}%"


# ---------------------------------------------------------------------------
# SQL visibility helpers — three patterns for surfacing query logic in-page.
# All three read the same sql/ files; only the UI container differs.
# ---------------------------------------------------------------------------

def load_sql(filename: str) -> str:
    """Return the raw text of a file from the sql/ directory."""
    return (Path(__file__).parent.parent / "sql" / filename).read_text()


def sql_expander(filename: str, label: str = "Show SQL") -> None:
    """Inline expander — collapsed by default, pushes content down when opened.

    Best for pages where the SQL is tightly related to a single section
    and the reader might want to read it alongside the chart above.
    """
    with st.expander(label):
        st.code(load_sql(filename), language="sql")


def sql_popover(filename: str, label: str = "📄 Show SQL") -> None:
    """Floating popover — opens a panel over the page without shifting layout.

    Best for pages where you want SQL available but don't want it to
    interrupt the reading flow when collapsed (added in Streamlit 1.31).
    """
    with st.popover(label):
        st.code(load_sql(filename), language="sql")



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
        st.caption(
            "7,043 customer records — one row per client. "
            "All analysis is written in SQL: every rule is readable, "
            "auditable, and can be tuned to fit any business."
        )
