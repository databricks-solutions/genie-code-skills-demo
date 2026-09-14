# PII masking templates

Reusable SQL for `@pii-management`. Substitute source tables and column names.

## Bronze -- pass through with markers

```sql
CREATE OR REFRESH MATERIALIZED VIEW bronze_customers
COMMENT "Raw customer data - CONTAINS PII: name, email, phone, income"
TBLPROPERTIES (
  "quality" = "bronze",
  "contains_pii" = "true",
  "pii_columns" = "first_name,last_name,email,phone,date_of_birth,annual_income"
)
AS SELECT
  customer_id,
  first_name,            -- [PII: NAME - MEDIUM]
  last_name,             -- [PII: NAME - MEDIUM]
  email,                 -- [PII: EMAIL - HIGH]
  phone,                 -- [PII: PHONE - HIGH]
  date_of_birth,         -- [PII: DOB - MEDIUM]
  annual_income,         -- [PII: FINANCIAL - HIGH]
  account_type,
  region,
  current_timestamp() AS audit_timestamp,
  'crm_system' AS source_system
FROM source_table
WHERE customer_id IS NOT NULL;
```

## Silver -- mask and derive

```sql
-- Income tier instead of exact income
CASE
  WHEN annual_income >= 250000 THEN 'High Income'
  WHEN annual_income >= 100000 THEN 'Upper Middle'
  WHEN annual_income >= 50000 THEN 'Middle'
  ELSE 'Lower Middle'
END AS income_tier,

-- Credit tier instead of exact score
CASE
  WHEN credit_score >= 750 THEN 'Excellent'
  WHEN credit_score >= 700 THEN 'Good'
  WHEN credit_score >= 650 THEN 'Fair'
  ELSE 'Poor'
END AS credit_tier,

-- Hash email for matching without exposing raw value
SHA2(LOWER(TRIM(email)), 256) AS email_hash,

-- Mask phone - show last 4 digits only
CONCAT('***-***-', RIGHT(REGEXP_REPLACE(phone, '[^0-9]', ''), 4)) AS phone_masked,

-- Age instead of DOB
FLOOR(DATEDIFF(CURRENT_DATE(), CAST(date_of_birth AS DATE)) / 365) AS age
```

## Gold -- aggregated only (no individual PII)

```sql
CREATE OR REFRESH MATERIALIZED VIEW gold_customer_segments
COMMENT "Customer segment analytics - NO PII"
TBLPROPERTIES ("quality" = "gold")
AS SELECT
  region,
  income_tier,
  credit_tier,
  COUNT(DISTINCT customer_id) AS customer_count,
  ROUND(AVG(age), 1) AS avg_age,
  current_timestamp() AS audit_timestamp,
  'gold_aggregation' AS source_system
FROM LIVE.silver_customers
GROUP BY region, income_tier, credit_tier;
```

## Unity Catalog column masking

```sql
CREATE OR REPLACE FUNCTION mask_email(email STRING)
RETURNS STRING
RETURN CASE
  WHEN is_member('pii_full_access') THEN email
  WHEN is_member('pii_partial_access') THEN CONCAT(SUBSTR(email, 1, 3), '***@', SPLIT_PART(email, '@', 2))
  ELSE '***@***'
END;

ALTER TABLE silver_customers ALTER COLUMN email SET MASK mask_email;
```
