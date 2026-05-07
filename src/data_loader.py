"""
data_loader.py — DuckDB session manager and SQL runner.

Architecture: DuckDB as a BigQuery drop-in for local / demo use.
Every SQL file in sql/ is written in BigQuery Standard SQL dialect.
This module shims the handful of BQ-only functions so the same SQL
runs against DuckDB without modification of the SQL files.

To swap DuckDB for a real BigQuery connection, see the commented stub
at the bottom of this file.
"""

from pathlib import Path
import duckdb
import pandas as pd
import streamlit as st

_ROOT = Path(__file__).parent.parent
_DATA_PATH = _ROOT / "data" / "telco_customer_churn.csv"
_SQL_DIR = _ROOT / "sql"

# ---------------------------------------------------------------------------
# DuckDB shims for BigQuery-only functions.
# When you migrate to BigQuery, drop these — the same names are built in.
# ---------------------------------------------------------------------------
_BQ_COMPAT_MACROS = """
CREATE OR REPLACE MACRO SAFE_DIVIDE(a, b) AS
    CASE WHEN b = 0 OR b IS NULL THEN NULL ELSE CAST(a AS DOUBLE) / CAST(b AS DOUBLE) END;
"""

# DuckDB uses COUNT_IF (with underscore); BigQuery uses COUNTIF (no underscore).
# We do a text substitution in run_sql_file() so the SQL files stay BQ-clean.
_BQ_TO_DUCKDB = {
    "COUNTIF(": "COUNT_IF(",
}


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Create a DuckDB in-memory connection with the Telco dataset loaded.

    Cached as a Streamlit resource so all pages share one connection
    (avoids reloading the CSV on every page navigation).

    What this does:
    1. Reads the CSV via pandas (handles the blank TotalCharges issue)
    2. Registers the DataFrame as a DuckDB table called 'telco'
    3. Registers BigQuery-compat macros so BQ SQL runs unchanged
    """
    df = pd.read_csv(_DATA_PATH)

    # The Telco dataset has a known data quality issue: customers with
    # tenure=0 have a blank string in TotalCharges instead of 0.0.
    # pd.to_numeric with errors='coerce' silently converts blanks → NaN.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    con = duckdb.connect(database=":memory:")
    con.register("telco", df)
    con.execute(_BQ_COMPAT_MACROS)

    return con


def run_sql_file(con: duckdb.DuckDBPyConnection, path: Path) -> pd.DataFrame:
    """
    Read a .sql file, apply BQ→DuckDB function name translations,
    execute against the connection, and return a pandas DataFrame.

    The translation dict (_BQ_TO_DUCKDB) is the only place BQ syntax
    differs from DuckDB. All other Standard SQL is identical.
    """
    sql = path.read_text(encoding="utf-8")

    for bq_fn, duckdb_fn in _BQ_TO_DUCKDB.items():
        sql = sql.replace(bq_fn, duckdb_fn)

    return con.execute(sql).df()


@st.cache_data
def load_all(_con: duckdb.DuckDBPyConnection) -> dict[str, pd.DataFrame]:
    """
    Run all five SQL analysis files in order and return results as a dict.

    Keys are the SQL file stem names:
        '01_data_quality', '02_churn_drivers', '03_customer_scoring',
        '04_retention_priority_list', '05_revenue_at_risk'

    The underscore prefix on _con tells Streamlit's cache not to try to
    hash the DuckDB connection object (it's not serialisable).
    """
    sql_files = sorted(_SQL_DIR.glob("*.sql"))
    return {f.stem: run_sql_file(_con, f) for f in sql_files}


# ---------------------------------------------------------------------------
# BigQuery migration stub
# ---------------------------------------------------------------------------
# When a client has their data in BigQuery, replace get_connection() and
# run_sql_file() with the block below. The SQL files in sql/ need zero
# changes — they are already BigQuery Standard SQL.
#
# Migration checklist:
#   1. pip install google-cloud-bigquery db-dtypes
#   2. Set GOOGLE_APPLICATION_CREDENTIALS env var (service account JSON)
#      or copy credentials into .streamlit/secrets.toml (see example file)
#   3. Replace the table name 'telco' in each SQL file with your BQ table,
#      e.g. `my-project.customer_data.transactions`
#   4. Remove the DuckDB shim macros — SAFE_DIVIDE is built into BQ
#
# --- BEGIN BQ STUB ---
#
# from google.cloud import bigquery
#
# @st.cache_resource
# def get_bq_client() -> bigquery.Client:
#     project_id = st.secrets["bigquery"]["project_id"]
#     return bigquery.Client(project=project_id)
#
# def run_sql_file_bq(client: bigquery.Client, path: Path) -> pd.DataFrame:
#     sql = path.read_text(encoding="utf-8")
#     return client.query(sql).to_dataframe()
#
# @st.cache_data(ttl=3600)   # refresh BigQuery results every hour
# def load_all_bq(_client: bigquery.Client) -> dict[str, pd.DataFrame]:
#     sql_files = sorted(_SQL_DIR.glob("*.sql"))
#     return {f.stem: run_sql_file_bq(_client, f) for f in sql_files}
#
# --- END BQ STUB ---
