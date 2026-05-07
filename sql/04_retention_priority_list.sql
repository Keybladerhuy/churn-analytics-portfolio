-- =============================================================================
-- 04_retention_priority_list.sql
-- PURPOSE: Turn the risk scores from 03_customer_scoring.sql into an
--   actionable priority list that a retention team can work through today.
--
-- We filter to High and Medium risk customers only (Low risk = monitor, no
-- immediate action), then sort by:
--   1. risk_score DESC  — address High before Medium
--   2. MonthlyCharges DESC — within the same tier, target high-value first
--      (losing a $100/month customer hurts more than a $25/month customer)
--
-- Each row includes a recommended_action — a plain-English script for the
-- retention team, customised by risk tier and contract type.
--
-- Output columns:
--   customer_id, risk_tier, monthly_charges, tenure_months, contract,
--   tech_support, primary_risk_factor, recommended_action
--
-- BigQuery-compatible SQL (Standard SQL dialect).
-- =============================================================================

WITH scored AS (
    -- Inline the scoring logic from 03_customer_scoring.sql.
    -- In a real BigQuery project this would reference a VIEW or a table
    -- created by running 03 first (e.g. SELECT * FROM `project.dataset.customer_scores`).
    SELECT
        customerID,

        CASE
            WHEN Contract = 'Month-to-month'
                 AND tenure < 12
                 AND TechSupport = 'No'
            THEN 'High'
            WHEN Contract = 'Month-to-month'
                 OR tenure < 6
            THEN 'Medium'
            ELSE 'Low'
        END AS risk_tier,

        CASE
            WHEN Contract = 'Month-to-month'
                 AND tenure < 12
                 AND TechSupport = 'No'
            THEN 3
            WHEN Contract = 'Month-to-month'
                 OR tenure < 6
            THEN 2
            ELSE 1
        END AS risk_score,

        CASE
            WHEN Contract = 'Month-to-month' AND tenure < 6  AND TechSupport = 'No'
            THEN 'Month-to-month contract with less than 6 months tenure and no tech support'
            WHEN Contract = 'Month-to-month' AND tenure < 12 AND TechSupport = 'No'
            THEN 'Month-to-month contract under 12 months with no tech support add-on'
            WHEN Contract = 'Month-to-month' AND tenure < 6
            THEN 'Month-to-month contract with less than 6 months tenure'
            WHEN Contract = 'Month-to-month' AND tenure < 12
            THEN 'Month-to-month contract with less than 1 year tenure'
            WHEN Contract = 'Month-to-month'
            THEN 'Month-to-month contract (no long-term commitment)'
            WHEN tenure < 6
            THEN 'New customer: less than 6 months tenure'
            ELSE 'Stable contract — routine monitoring'
        END AS primary_risk_factor,

        Contract,
        tenure,
        MonthlyCharges,
        TechSupport
    FROM telco
)

SELECT
    customerID                              AS customer_id,
    risk_tier,
    ROUND(MonthlyCharges, 2)               AS monthly_charges,
    tenure                                 AS tenure_months,
    Contract                               AS contract,
    TechSupport                            AS tech_support,
    primary_risk_factor,

    -- Plain-English recommended action, tailored by risk profile
    CASE
        WHEN risk_tier = 'High' AND TechSupport = 'No'
        THEN 'Assign to retention specialist within 7 days — offer tech support bundle free for 3 months'

        WHEN risk_tier = 'High' AND Contract = 'Month-to-month' AND tenure < 6
        THEN 'Priority call within 48 hours — offer first-year annual contract at 15% discount'

        WHEN risk_tier = 'High'
        THEN 'Retention team outreach — offer annual contract upgrade with loyalty incentive'

        WHEN risk_tier = 'Medium' AND Contract = 'Month-to-month'
        THEN 'Send personalised email — offer 12-month contract with 10% discount'

        WHEN risk_tier = 'Medium' AND tenure < 6
        THEN 'Welcome-series check-in call — confirm service satisfaction, offer add-on trial'

        ELSE 'Standard retention nurture email sequence'
    END AS recommended_action

FROM scored
WHERE risk_tier IN ('High', 'Medium')
ORDER BY risk_score DESC, MonthlyCharges DESC
