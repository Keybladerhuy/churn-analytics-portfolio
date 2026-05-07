-- =============================================================================
-- 05_revenue_at_risk.sql
-- PURPOSE: Answer the executive question: "How much revenue could we lose
--   if we do nothing about churn?"
--
-- We group customers by risk tier and calculate:
--   - Monthly recurring revenue (MRR) in each tier
--   - Projected annual revenue at risk (MRR × 12)
--   - Estimated lost revenue, applying the observed churn rate from the
--     dataset as a baseline probability — this is a conservative floor,
--     not a prediction
--
-- The baseline churn rate is computed directly from the actual Churn
-- column in the dataset, making the estimate transparent and auditable.
--
-- Output: one row per risk tier (High / Medium / Low) plus a TOTAL row,
--   suitable for pasting into an executive slide or email.
--
-- Columns:
--   risk_tier, n_customers, monthly_revenue, annual_revenue,
--   baseline_churn_rate, estimated_monthly_loss, estimated_annual_loss
--
-- BigQuery-compatible SQL (Standard SQL dialect).
-- =============================================================================

WITH

-- Overall churn rate from the raw dataset (used as baseline probability)
baseline AS (
    SELECT
        SAFE_DIVIDE(COUNTIF(Churn = 'Yes'), COUNT(*)) AS overall_churn_rate
    FROM telco
),

-- Assign risk tiers (same rules as 03 and 04)
scored AS (
    SELECT
        MonthlyCharges,
        CASE
            WHEN Contract = 'Month-to-month'
                 AND tenure < 12
                 AND TechSupport = 'No'
            THEN 'High'
            WHEN Contract = 'Month-to-month'
                 OR tenure < 6
            THEN 'Medium'
            ELSE 'Low'
        END AS risk_tier
    FROM telco
),

-- Revenue aggregated by risk tier
by_tier AS (
    SELECT
        s.risk_tier,
        COUNT(*)                       AS n_customers,
        ROUND(SUM(s.MonthlyCharges), 2)  AS monthly_revenue,
        ROUND(SUM(s.MonthlyCharges) * 12, 2) AS annual_revenue,
        b.overall_churn_rate
    FROM scored s
    CROSS JOIN baseline b
    GROUP BY s.risk_tier, b.overall_churn_rate
),

-- Estimate revenue at risk using the baseline churn rate
-- (High-risk customers are proportionally more likely to churn,
--  but we use the overall rate here as a conservative, auditable baseline)
tier_with_loss AS (
    SELECT
        risk_tier,
        n_customers,
        monthly_revenue,
        annual_revenue,
        ROUND(overall_churn_rate * 100, 1) AS baseline_churn_pct,
        ROUND(monthly_revenue * overall_churn_rate, 2)        AS estimated_monthly_loss,
        ROUND(monthly_revenue * overall_churn_rate * 12, 2)   AS estimated_annual_loss
    FROM by_tier
),

-- Add a TOTAL summary row
totals AS (
    SELECT
        'TOTAL'                          AS risk_tier,
        SUM(n_customers)                 AS n_customers,
        ROUND(SUM(monthly_revenue), 2)   AS monthly_revenue,
        ROUND(SUM(annual_revenue), 2)    AS annual_revenue,
        MAX(baseline_churn_pct)          AS baseline_churn_pct,
        ROUND(SUM(estimated_monthly_loss), 2) AS estimated_monthly_loss,
        ROUND(SUM(estimated_annual_loss), 2)  AS estimated_annual_loss
    FROM tier_with_loss
)

SELECT * FROM (
    SELECT * FROM tier_with_loss
    UNION ALL
    SELECT * FROM totals
)
ORDER BY
    CASE risk_tier
        WHEN 'High'   THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Low'    THEN 3
        ELSE               4
    END
