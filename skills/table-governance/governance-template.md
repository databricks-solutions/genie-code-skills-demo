# Governance templates

Reusable CREATE / ALTER / TAG statements for `@table-governance`. Substitute catalog, schema, and column names.

## Column comments

```sql
ALTER TABLE <catalog>.<schema>.silver_customers
  ALTER COLUMN customer_id COMMENT 'Unique customer identifier from source system',
  ALTER COLUMN income_tier COMMENT 'Derived income bracket: High Income / Upper Middle / Middle / Lower Middle',
  ALTER COLUMN email_hash COMMENT 'SHA-256 hash of lowercase trimmed email for matching without PII exposure',
  ALTER COLUMN data_quality_flag COMMENT 'Row-level DQ status: CLEAN, MISSING_<field>, or NEGATIVE_<field>',
  ALTER COLUMN audit_timestamp COMMENT 'Pipeline execution timestamp',
  ALTER COLUMN source_system COMMENT 'Upstream source system identifier';
```

## Unity Catalog tags

```sql
ALTER TABLE <catalog>.<schema>.bronze_customers
  SET TAGS ('pii' = 'true', 'data_classification' = 'confidential');
```

## Full silver table with governance applied

```sql
CREATE OR REFRESH MATERIALIZED VIEW silver_customers(
  CONSTRAINT valid_customer_id EXPECT (customer_id IS NOT NULL) ON VIOLATION FAIL UPDATE
)
COMMENT "Cleaned customer data with derived tiers from bronze_customers - CONTAINS PII: email_hash, phone_masked, age"
TBLPROPERTIES (
  "quality" = "silver",
  "owner" = "data-engineering",
  "domain" = "customer",
  "contains_pii" = "true",
  "pii_columns" = "email_hash,phone_masked,age",
  "delta.enableChangeDataFeed" = "true"
)
AS SELECT
  customer_id,
  region,
  customer_segment,
  SHA2(LOWER(TRIM(email)), 256) AS email_hash,
  CONCAT('***-***-', RIGHT(REGEXP_REPLACE(phone, '[^0-9]', ''), 4)) AS phone_masked,
  FLOOR(DATEDIFF(CURRENT_DATE(), CAST(date_of_birth AS DATE)) / 365) AS age,
  CASE
    WHEN annual_income >= 250000 THEN 'High Income'
    WHEN annual_income >= 100000 THEN 'Upper Middle'
    WHEN annual_income >= 50000 THEN 'Middle'
    ELSE 'Lower Middle'
  END AS income_tier,
  CASE
    WHEN customer_id IS NULL THEN 'MISSING_CUSTOMER_ID'
    ELSE 'CLEAN'
  END AS data_quality_flag,
  current_timestamp() AS audit_timestamp,
  'crm_system' AS source_system
FROM LIVE.bronze_customers;

ALTER TABLE silver_customers
  ALTER COLUMN customer_id COMMENT 'Unique customer identifier from CRM',
  ALTER COLUMN email_hash COMMENT 'SHA-256 hash of lowercase trimmed email for matching without PII exposure',
  ALTER COLUMN phone_masked COMMENT 'Last 4 digits of phone number, masked for PII protection',
  ALTER COLUMN age COMMENT 'Derived age in years from date_of_birth',
  ALTER COLUMN income_tier COMMENT 'Derived income bracket: High Income / Upper Middle / Middle / Lower Middle',
  ALTER COLUMN data_quality_flag COMMENT 'Row-level DQ status: CLEAN or MISSING_CUSTOMER_ID';

ALTER TABLE silver_customers
  SET TAGS ('pii' = 'true', 'data_classification' = 'confidential', 'domain' = 'customer');
```
