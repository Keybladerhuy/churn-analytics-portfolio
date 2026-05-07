-- =============================================================================
-- 01_data_quality.sql
-- PURPOSE: Answer the first question every analyst asks about new data:
--   "Can I trust this dataset?"
--
-- We check for:
--   1. Total row count — know how many customers we are working with
--   2. Duplicate customer IDs — each customer should appear exactly once
--   3. Null / blank values in critical columns — missing data means gaps
--      in our analysis
--   4. The known TotalCharges blank issue — new customers (tenure = 0)
--      have a blank TotalCharges; we flag this rather than silently drop them
--   5. Distributions of key segmentation fields — so we can spot unexpected
--      values before they corrupt downstream analysis
--
-- Output: a single table with columns (check_name, value, status)
--   status = 'OK'     → no action needed
--   status = 'REVIEW' → something worth discussing with the client
--
-- BigQuery-compatible SQL (Standard SQL dialect).
-- Run on DuckDB locally via src/data_loader.py.
-- =============================================================================

WITH

-- 1. Basic counts
row_count AS (
    SELECT
        'Total rows'                               AS check_name,
        CAST(COUNT(*) AS VARCHAR)                  AS value,
        IF(COUNT(*) > 0, 'OK', 'REVIEW')           AS status
    FROM telco
),

duplicate_ids AS (
    SELECT
        'Duplicate customerIDs'                    AS check_name,
        CAST(COUNT(*) - COUNT(DISTINCT customerID) AS VARCHAR) AS value,
        IF(COUNT(*) = COUNT(DISTINCT customerID), 'OK', 'REVIEW') AS status
    FROM telco
),

-- 2. Null / blank counts for critical fields
null_monthly_charges AS (
    SELECT
        'Null MonthlyCharges'                      AS check_name,
        CAST(COUNTIF(MonthlyCharges IS NULL) AS VARCHAR) AS value,
        IF(COUNTIF(MonthlyCharges IS NULL) = 0, 'OK', 'REVIEW') AS status
    FROM telco
),

blank_total_charges AS (
    -- Blank TotalCharges values are converted to NULL during data loading
    -- (new customers with tenure=0 have blank strings in the raw CSV).
    -- We count NULLs here, which works for both cleaned numeric columns
    -- and raw BigQuery STRING columns where blanks become NULLs on CAST.
    SELECT
        'NULL TotalCharges (new customers, tenure=0)' AS check_name,
        CAST(COUNTIF(TotalCharges IS NULL) AS VARCHAR) AS value,
        IF(COUNTIF(TotalCharges IS NULL) = 0, 'OK', 'REVIEW') AS status
    FROM telco
),

null_churn AS (
    SELECT
        'Null Churn label'                         AS check_name,
        CAST(COUNTIF(Churn IS NULL) AS VARCHAR)    AS value,
        IF(COUNTIF(Churn IS NULL) = 0, 'OK', 'REVIEW') AS status
    FROM telco
),

-- 3. Contract type distribution — spot unexpected values
contract_dist AS (
    SELECT
        'Contract types (expected: 3)'             AS check_name,
        CAST(COUNT(DISTINCT Contract) AS VARCHAR)  AS value,
        IF(COUNT(DISTINCT Contract) = 3, 'OK', 'REVIEW') AS status
    FROM telco
),

-- 4. Tenure bucket distribution — sanity-check the data spread
tenure_buckets AS (
    SELECT
        CASE
            WHEN tenure BETWEEN 0  AND 6  THEN '0-6m'
            WHEN tenure BETWEEN 7  AND 12 THEN '6-12m'
            WHEN tenure BETWEEN 13 AND 24 THEN '1-2yr'
            ELSE '2yr+'
        END AS bucket,
        COUNT(*) AS n
    FROM telco
    GROUP BY 1
),

tenure_bucket_summary AS (
    SELECT
        'Tenure bucket counts (0-6m | 6-12m | 1-2yr | 2yr+)' AS check_name,
        STRING_AGG(bucket || ': ' || CAST(n AS VARCHAR), ' | ' ORDER BY bucket) AS value,
        'OK' AS status
    FROM tenure_buckets
),

-- 5. Overall churn rate — baseline metric
overall_churn AS (
    SELECT
        'Overall churn rate'                       AS check_name,
        CAST(ROUND(SAFE_DIVIDE(
            COUNTIF(Churn = 'Yes') * 100.0,
            COUNT(*)
        ), 1) AS VARCHAR) || '%'                   AS value,
        'OK'                                       AS status
    FROM telco
)

-- Combine all checks into one readable output table.
-- Wrap in a subquery so ORDER BY can reference the status column
-- across UNION ALL branches — required by both BigQuery and DuckDB.
SELECT * FROM (
    SELECT check_name, value, status FROM row_count
    UNION ALL
    SELECT check_name, value, status FROM duplicate_ids
    UNION ALL
    SELECT check_name, value, status FROM null_monthly_charges
    UNION ALL
    SELECT check_name, value, status FROM blank_total_charges
    UNION ALL
    SELECT check_name, value, status FROM null_churn
    UNION ALL
    SELECT check_name, value, status FROM contract_dist
    UNION ALL
    SELECT check_name, value, status FROM tenure_bucket_summary
    UNION ALL
    SELECT check_name, value, status FROM overall_churn
)
ORDER BY
    CASE status WHEN 'REVIEW' THEN 0 ELSE 1 END,
    check_name
