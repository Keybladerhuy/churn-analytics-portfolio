# Quickstart — Demo Cheat Sheet

Everything you need to run and present this dashboard in under 2 minutes.

---

## Start the dashboard

> **Always activate the venv first.** Skipping this causes `ModuleNotFoundError: No module named 'duckdb'`.

```bash
cd ~/WorkspaceGit/customer-retention-analytics
source .venv/bin/activate        # ← required every new terminal session
streamlit run app.py
```

Opens at **http://localhost:8501** — leave this terminal running.

If the browser doesn't open automatically: `open http://localhost:8501`

---

## First-time setup (one-time only)

```bash
cd ~/WorkspaceGit/customer-retention-analytics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Pages and what each one says

| Page | Audience | Key talking point |
|---|---|---|
| **1 · Executive Summary** | Anyone | Churn rate, revenue at risk, top driver — the 30-second overview |
| **2 · Churn Drivers** | Business owner | Which customer segments churn most and why |
| **3 · Retention Priority List** | Operations / CRM team | Ranked list of customers to call — with a recommended action per row |
| **4 · Revenue at Risk** | Finance / management | Dollar figures by tier; basic retention slider |
| **5 · ROI Calculator** | Business owner / budget holder | Full program ROI: cost in vs. revenue recovered, net return |

---

## Demo flow (non-technical audience, ~5 min)

1. **Executive Summary** — "Here's your churn rate and how much revenue is at risk right now."
2. **Churn Drivers** — "Here's why. Month-to-month customers churn at 42% — nearly 4× your stable customers."
3. **Retention Priority List** — "Here's who your team calls on Monday. Sorted, filtered, one recommended action per customer."
4. **ROI Calculator** — "Here's the business case. Adjust the sliders to fit your team's capacity and outreach cost."

Close with: *"This was built on sample data in a few days. With your data, we'd calibrate the thresholds to match your actual churn patterns — usually a one-day engagement."*

---

## Demo flow (technical audience, ~5 min)

1. **Executive Summary** — same as above, brief
2. **Churn Drivers** → show the SQL: `sql/02_churn_drivers.sql` — "All the logic is in plain SQL. No model, no black box."
3. **Retention Priority List** → show `sql/03_customer_scoring.sql` — "This is the scoring logic. Three `CASE WHEN` rules. You can read every condition."
4. Mention: "DuckDB locally, BigQuery in production — same SQL files, swap one function call in `src/data_loader.py`."
5. **ROI Calculator** — "Page 5 is the business case layer on top of the data layer."

---

## Key numbers to have ready (from the Telco sample dataset)

| Metric | Value |
|---|---|
| Total customers | 7,043 |
| Overall churn rate | 26.5% |
| High-risk customers | 1,313 |
| High-risk monthly revenue | $88,167 |
| Avg MRR per high-risk customer | $67 |
| ROI Calculator defaults (50% contact, 20% retain, $50/outreach) | **$72,758 net annual ROI · $3.2× return** |

---

## Sidebar features worth pointing out

- **Currency toggle** (USD / JPY / EUR) — useful when demoing to Japanese clients
- **"How this works" expander** — shows the scoring rules in plain English; good transparency moment with non-technical audiences

---

## If something breaks

```bash
# Re-run the SQL smoke test
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

All five files should return a shape with rows > 0. If Streamlit throws a port error, run `streamlit run app.py --server.port 8502`.

**Expected harmless warning on macOS** — you will see this in the terminal, ignore it:
```
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'
```
This is a macOS system library mismatch. It does not affect the dashboard.
