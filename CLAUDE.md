# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (Python 3.9+)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py

# Smoke-test all SQL files against DuckDB (no Streamlit needed)
python3 -c "
import duckdb, pandas as pd
from pathlib import Path
df = pd.read_csv('data/telco_customer_churn.csv')
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
con = duckdb.connect(':memory:')
con.register('telco', df)
con.execute(\"CREATE OR REPLACE MACRO SAFE_DIVIDE(a,b) AS CASE WHEN b=0 OR b IS NULL THEN NULL ELSE CAST(a AS DOUBLE)/CAST(b AS DOUBLE) END\")
for f in sorted(Path('sql').glob('*.sql')):
    sql = f.read_text().replace('COUNTIF(', 'COUNT_IF(')
    print(f.name, con.execute(sql).df().shape)
"
```

## Architecture

**Data flow:** CSV → DuckDB (in-memory) → SQL files → pandas DataFrames → Streamlit pages.

**SQL layer (`sql/`)** — five BigQuery Standard SQL files, run in sequence. Each file is self-contained (no cross-file dependencies at the SQL level; `04` and `05` inline the scoring logic from `03` rather than referencing it as a view). All files are decorated with plain-English comment headers explaining the business question they answer.

**Python layer (`src/`):**
- `data_loader.py` — owns the DuckDB connection (`@st.cache_resource`) and DataFrame cache (`@st.cache_data`). Registers BQ-compat shims before executing SQL. Two shims exist: a `SAFE_DIVIDE` macro (registered as DuckDB SQL) and a `COUNTIF` → `COUNT_IF` string replacement applied in `run_sql_file()`. The BigQuery migration stub is commented out at the bottom.
- `formatting.py` — currency config, `fmt_currency()`, `fmt_pct()`, and `render_sidebar()`. The sidebar is called at the top of every page file to ensure it appears on all pages.

**Streamlit app (`app.py` + `pages/`)** — standard Streamlit multi-page pattern. `app.py` is Page 1 (Executive Summary); `pages/2_*`, `pages/3_*`, `pages/4_*` are auto-discovered. Every page calls `get_connection()` and `load_all()` at the top — both are cached so only the first page load hits DuckDB.

## BQ ↔ DuckDB compatibility

SQL files are written in BigQuery dialect. Two points of incompatibility are handled by `data_loader.py`, not in the SQL files:

1. `SAFE_DIVIDE(a, b)` — registered as a DuckDB macro at session start
2. `COUNTIF(expr)` → `COUNT_IF(expr)` — string-replaced in `run_sql_file()`

`UNION ALL … ORDER BY CASE …` requires a subquery wrapper in both dialects — this pattern is already applied in `01_data_quality.sql` and `05_revenue_at_risk.sql`.

## Dataset

`data/telco_customer_churn.csv` is committed (7,043 rows). One known data quality issue: `TotalCharges` is a blank string for 11 customers with `tenure=0`. This is handled in `get_connection()` via `pd.to_numeric(..., errors='coerce')` before loading into DuckDB.

## Deployment

No secrets or env vars required for the demo. For Streamlit Cloud: push to GitHub, point at `app.py`. For BigQuery: see the commented stub in `src/data_loader.py` and `secrets.toml.example`.
