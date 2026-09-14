---
name: pii-management
description: Identify and label PII columns in SDP pipeline tables. Use when creating or modifying tables that contain customer or personal data. Includes detection patterns, table property labeling, column annotation, and masking guidance. Always generate SDP pipelines using SQL, not Python.
---

# PII Management in SDP Pipelines

When a table contains personal or sensitive data, apply these detection, labelling, and protection rules.

For bronze/silver/gold SQL and Unity Catalog masking functions, read [masking-templates.md](masking-templates.md).

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

| Layer | Rule |
|-------|------|
| Bronze | Pass PII through with markers (properties, COMMENT, inline `-- [PII: ...]` annotations) |
| Silver | Replace raw PII with derived or masked equivalents (`income_tier`, `email_hash`, `phone_masked`, `age`) |
| Gold | Aggregated data only -- no individual PII |

Copy the layer-specific SQL from [masking-templates.md](masking-templates.md).
