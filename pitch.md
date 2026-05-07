# Customer Retention Analytics — Pitch One-Pager

## What it does

Turns a raw customer CSV into a live dashboard that shows you exactly which customers are about to leave, why, and what to do about it — in plain English, with no data science required on your side.

---

## The problem

You have customer data but no visibility into:
- **Who is about to leave** — you find out at cancellation, not before
- **Why they're leaving** — you have theories, but no evidence
- **What to do first** — your team has limited capacity; which customers deserve a call today?

Most analytics tools give you charts. This gives you a **prioritised action list**.

---

## The solution

A rule-based scoring system + live dashboard, built on your own data.

**How it works:**

1. Your customer data (CSV or BigQuery) is loaded into the analysis pipeline
2. Five SQL queries run in sequence — each answers one business question
3. Every customer receives a risk score based on transparent, readable rules:
   - **High risk**: month-to-month contract + under 12 months tenure + no tech support
   - **Medium risk**: month-to-month contract OR under 6 months tenure
   - **Low risk**: everything else
4. The dashboard shows the results — and the retention team gets a sorted, filtered action list

**Why you can trust it:** the scoring logic is a single SQL file. You can read every rule. If you disagree with a threshold, we change one number and re-run.

---

## ROI example (from this sample dataset)

These numbers come directly from the IBM Telco churn dataset (7,043 customers):

| Metric | Value |
|---|---|
| Overall churn rate | **26.5%** |
| High-risk customers | **1,313** |
| High-risk monthly revenue | **$88,167** |
| High-risk annual revenue at risk | **$1,058,005** |
| Estimated annual revenue lost (at baseline churn rate) | **$280,763** |

**Retention scenario:** If you retain just **20% of your high-risk customers**, you recover:
- **$17,633/month** → **$211,601/year**

That is the business case for a retention program. Before any outreach has been done.

---

## Why rule-based instead of machine learning

> "You can see exactly why each customer was flagged. No black box."

- A data scientist can read the scoring SQL in 2 minutes
- A business owner can read the plain-English risk reason in 5 seconds
- You can challenge, adjust, and re-run any rule without retraining a model
- No model drift, no explainability debt, no dependency on labelled training data
- Scoring logic that survives staff turnover: it's in a SQL file, not a Jupyter notebook

---

## What's customisable

| Component | Customisation |
|---|---|
| Scoring rules | Change any threshold (e.g. `tenure < 12` → `tenure < 18`) |
| Risk tiers | Add a fourth tier, rename existing tiers |
| Recommended actions | Edit the action strings in `sql/04_retention_priority_list.sql` |
| Output fields | Add any column from your customer table |
| Language | Dashboard labels can be switched to Japanese (or any language) |
| Currency | USD / JPY / EUR toggle built in; extend to any symbol |
| Data source | DuckDB locally; BigQuery for production — same SQL, swap one function |

---

## What a client needs to get started

A CSV or BigQuery table with six columns:

```
customerID    — unique customer identifier
Contract      — Month-to-month / One year / Two year
tenure        — months as a customer (integer)
MonthlyCharges — current monthly bill (decimal)
TechSupport   — Yes / No / No internet service
Churn         — Yes / No (for churn rate baseline)
```

If additional columns exist (payment method, service add-ons, plan tier), they can be incorporated into the scoring rules or displayed in the dashboard.

---

## Short FAQ

**Can this connect to our existing database?**
Yes. Locally, the dashboard runs on DuckDB (no cloud account needed). For production, it connects to BigQuery with a service account — the SQL files need zero changes. Other databases (Postgres, Snowflake) are supported with minor data_loader changes.

**Can the scoring rules be adjusted?**
Yes, at any time. The rules are in a single SQL file (`sql/03_customer_scoring.sql`). Changing a threshold takes 30 seconds and the dashboard reflects it on next load.

**Is this available in Japanese?**
Yes. The README and this pitch document are bilingual. Dashboard labels can be localised; the sidebar already includes a currency toggle for JPY display.

**How long does setup take for a new client?**
For a CSV-based demo: under one hour. For a BigQuery production connection with client-specific data: typically one day including data mapping and threshold calibration.

**What does it cost to run?**
The demo runs free on Streamlit Cloud (public apps). BigQuery costs depend on query volume — for a 100K-customer dataset, monthly analysis costs are typically under $5/month.

---

*Built with: Python · DuckDB · BigQuery SQL · Streamlit · Plotly*
*Dataset: IBM Telco Customer Churn (Kaggle) — 7,043 records, no PII*
