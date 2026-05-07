-- =============================================================================
-- 02_churn_drivers.sql
-- PURPOSE: Answer "Which customer characteristics are most associated
--   with churn?" — without using machine learning.
--
-- We compare churn rates across four dimensions:
--   1. Contract type  — do month-to-month customers churn more?
--   2. Tenure bucket  — are newer customers more likely to leave?
--   3. Monthly charge tier — does price level predict churn?
--   4. Tech support   — does having a support add-on improve retention?
--
-- Output: a ranked table ordered by churn_rate DESC, so row 1 is always
--   the single segment with the highest churn — the dashboard reads this
--   directly to populate the "Key Finding" callout.
--
-- Columns: driver, segment, churn_rate, n_customers, churned_customers
--
-- BigQuery-compatible SQL (Standard SQL dialect).
-- =============================================================================

WITH

-- Classify MonthlyCharges into tertiles (low / mid / high)
-- using fixed quantiles so the labels are stable across data refreshes.
charge_tiers AS (
    SELECT
        customerID,
        Churn,
        MonthlyCharges,
        CASE
            WHEN MonthlyCharges < 35  THEN 'Low (<$35)'
            WHEN MonthlyCharges < 65  THEN 'Mid ($35-$65)'
            ELSE                           'High (>$65)'
        END AS charge_tier
    FROM telco
),

-- 1. Churn rate by contract type
by_contract AS (
    SELECT
        'Contract type'                        AS driver,
        Contract                               AS segment,
        ROUND(SAFE_DIVIDE(
            COUNTIF(Churn = 'Yes') * 100.0,
            COUNT(*)
        ), 1)                                  AS churn_rate,
        COUNT(*)                               AS n_customers,
        COUNTIF(Churn = 'Yes')                 AS churned_customers
    FROM telco
    GROUP BY Contract
),

-- 2. Churn rate by tenure bucket
by_tenure AS (
    SELECT
        'Tenure bucket'                        AS driver,
        CASE
            WHEN tenure BETWEEN 0  AND 6  THEN '0-6 months'
            WHEN tenure BETWEEN 7  AND 12 THEN '6-12 months'
            WHEN tenure BETWEEN 13 AND 24 THEN '1-2 years'
            ELSE                               '2+ years'
        END                                    AS segment,
        ROUND(SAFE_DIVIDE(
            COUNTIF(Churn = 'Yes') * 100.0,
            COUNT(*)
        ), 1)                                  AS churn_rate,
        COUNT(*)                               AS n_customers,
        COUNTIF(Churn = 'Yes')                 AS churned_customers
    FROM telco
    GROUP BY 2
),

-- 3. Churn rate by monthly charge tier
by_charge AS (
    SELECT
        'Monthly charge tier'                  AS driver,
        charge_tier                            AS segment,
        ROUND(SAFE_DIVIDE(
            COUNTIF(Churn = 'Yes') * 100.0,
            COUNT(*)
        ), 1)                                  AS churn_rate,
        COUNT(*)                               AS n_customers,
        COUNTIF(Churn = 'Yes')                 AS churned_customers
    FROM charge_tiers
    GROUP BY charge_tier
),

-- 4. Churn rate by tech support subscription
by_tech_support AS (
    SELECT
        'Tech support add-on'                  AS driver,
        CASE TechSupport
            WHEN 'Yes' THEN 'Has tech support'
            WHEN 'No'  THEN 'No tech support'
            ELSE            'No internet service'
        END                                    AS segment,
        ROUND(SAFE_DIVIDE(
            COUNTIF(Churn = 'Yes') * 100.0,
            COUNT(*)
        ), 1)                                  AS churn_rate,
        COUNT(*)                               AS n_customers,
        COUNTIF(Churn = 'Yes')                 AS churned_customers
    FROM telco
    GROUP BY TechSupport
)

-- Union all drivers into one ranked output
SELECT driver, segment, churn_rate, n_customers, churned_customers
FROM by_contract
UNION ALL
SELECT driver, segment, churn_rate, n_customers, churned_customers
FROM by_tenure
UNION ALL
SELECT driver, segment, churn_rate, n_customers, churned_customers
FROM by_charge
UNION ALL
SELECT driver, segment, churn_rate, n_customers, churned_customers
FROM by_tech_support
ORDER BY churn_rate DESC
