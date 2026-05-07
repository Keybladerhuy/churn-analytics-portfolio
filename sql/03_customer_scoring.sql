-- =============================================================================
-- 03_customer_scoring.sql
-- PURPOSE: Assign every customer a risk tier and a plain-English reason
--   for that tier — no machine learning, no black box.
--
-- Scoring rules (transparent CASE logic):
--
--   HIGH RISK (score 3):
--     Month-to-month contract  AND  tenure < 12 months  AND  no tech support
--     → All three warning signals present simultaneously
--
--   MEDIUM RISK (score 2):
--     Month-to-month contract  OR  tenure < 6 months
--     → At least one major warning signal present
--
--   LOW RISK (score 1):
--     Everything else (annual/two-year contract, established customers)
--
-- Why rule-based instead of ML?
--   These rules were derived by looking at which segments had the highest
--   churn rates in 02_churn_drivers.sql. A client can read, challenge, and
--   adjust every line. The scoring is auditable — not a black box.
--
-- Output columns:
--   customerID, risk_tier, risk_score, primary_risk_factor,
--   Contract, tenure, MonthlyCharges, TechSupport, Churn (for validation)
--
-- BigQuery-compatible SQL (Standard SQL dialect).
-- =============================================================================

SELECT
    customerID,

    -- Risk tier assignment
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

    -- Numeric score for easy sorting (High=3, Medium=2, Low=1)
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

    -- Plain-English reason — the most specific matching rule wins
    -- (evaluated top to bottom; first match returned)
    CASE
        WHEN Contract = 'Month-to-month'
             AND tenure < 6
             AND TechSupport = 'No'
        THEN 'Month-to-month contract with less than 6 months tenure and no tech support'

        WHEN Contract = 'Month-to-month'
             AND tenure < 12
             AND TechSupport = 'No'
        THEN 'Month-to-month contract under 12 months with no tech support add-on'

        WHEN Contract = 'Month-to-month'
             AND tenure < 6
        THEN 'Month-to-month contract with less than 6 months tenure'

        WHEN Contract = 'Month-to-month'
             AND tenure < 12
        THEN 'Month-to-month contract with less than 1 year tenure'

        WHEN Contract = 'Month-to-month'
        THEN 'Month-to-month contract (no long-term commitment)'

        WHEN tenure < 6
        THEN 'New customer: less than 6 months tenure'

        WHEN Contract = 'One year'
        THEN 'One-year contract — moderate stability'

        ELSE 'Two-year contract or long-tenured customer — low churn risk'
    END AS primary_risk_factor,

    -- Raw fields passed through for downstream queries
    Contract,
    tenure,
    MonthlyCharges,
    TechSupport,
    InternetService,
    PaymentMethod,
    Churn

FROM telco
ORDER BY risk_score DESC, MonthlyCharges DESC
