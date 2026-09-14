# SDP SQL templates

Reusable patterns for `@sdp-basics`. Substitute entity names, source, and quality tags.

## Audit columns (always last)

```sql
current_timestamp() AS audit_timestamp,
'<source_description>' AS source_system
```

## Data quality flag (silver)

```sql
CASE
  WHEN <field> IS NULL THEN 'MISSING_<FIELD>'
  WHEN <field> < 0 THEN 'NEGATIVE_<FIELD>'
  ELSE 'CLEAN'
END AS data_quality_flag
```

## Bronze materialized view

```sql
CREATE OR REFRESH MATERIALIZED VIEW bronze_transactions
COMMENT "Raw transaction data from POS systems"
TBLPROPERTIES ("quality" = "bronze")
AS SELECT
  *,
  current_timestamp() AS audit_timestamp,
  'pos' AS source_system
FROM source_table
WHERE transaction_id IS NOT NULL;
```
