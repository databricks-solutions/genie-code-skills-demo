---
name: pii-management
description: Identify and label PII columns in SDP pipeline tables. Use when creating or modifying tables that contain customer or personal data. Includes detection patterns, table property labeling, column annotation, and masking guidance. Always generate SDP pipelines using SQL, not Python.
---

# PII Management in SDP Pipelines

When a table contains personal or sensitive data, apply these detection, labelling, and protection rules.

## Identify PII Columns

Flag columns matching these patterns as PII:

| Column Pattern | PII Type | Risk |
|----------------|----------|------|
| `email`, `email_address` | EMAIL | HIGH |
| `phone`, `mobile`, `telephone` | PHONE | HIGH |
| `first_name`, `last_name`, `full_name` | NAME | MEDIUM |
| `date_of_birth`, `dob` | DOB | MEDIUM |
| `address`, `street`, `postal_code` | ADDRESS | MEDIUM |
| `ssn`, `national_id`, `tax_id` | SSN | CRITICAL |
| `account_number`, `iban`, `sort_code` | ACCOUNT | HIGH |
| `credit_score`, `income`, `salary` | FINANCIAL | HIGH |
| `card_number`, `cvv` | PAYMENT | CRITICAL |

## Label PII Tables

Any table containing PII columns MUST include these table properties:

```sql
TBLPROPERTIES (
  "quality" = "bronze",
  "contains_pii" = "true",
  "pii_columns" = "email,phone,first_name,last_name"
)
```

## Comment PII Tables

The COMMENT clause MUST mention that the table contains PII:

```sql
COMMENT "Raw customer data - CONTAINS PII: name, email, phone, address"
```

## Annotate PII Columns in SQL

Add inline comments next to PII columns to flag their risk level:

```sql
SELECT
  customer_id,
  first_name,            -- [PII: NAME - MEDIUM]
  last_name,             -- [PII: NAME - MEDIUM]
  email,                 -- [PII: EMAIL - HIGH]
  phone_number,          -- [PII: PHONE - HIGH]
  date_of_birth,         -- [PII: DOB - MEDIUM]
  annual_income,         -- [PII: FINANCIAL - HIGH]
  current_timestamp() AS audit_timestamp,
  'crm_system' AS source_system
FROM source_table;
```

## PII Handling by Layer

### Bronze -- Pass Through with Markers

Pass PII through at Bronze but add properties and comments for visibility:

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

### Silver -- Apply Masking and Derivation

At Silver, replace raw PII with derived or masked equivalents:

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

### Gold -- Aggregated Only

Gold tables MUST NOT contain individual PII. Only include aggregated data:

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

## Unity Catalog Column Masking

For dynamic masking based on user permissions, create masking functions:

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
