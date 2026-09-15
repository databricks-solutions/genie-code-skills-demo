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

## Bronze streaming table (Auto Loader)

```sql
CREATE OR REFRESH STREAMING TABLE bronze_transactions
COMMENT "Raw transaction data from POS files"
TBLPROPERTIES ("quality" = "bronze", "domain" = "finance")
CLUSTER BY AUTO
AS SELECT
  *,
  current_timestamp() AS audit_timestamp,
  'pos' AS source_system
FROM STREAM read_files(
  "/Volumes/<catalog>/<schema>/raw_data/transactions/",
  format => "json"
)
WHERE transaction_id IS NOT NULL;
```

## Bronze materialized view (existing table)

```sql
CREATE OR REFRESH MATERIALIZED VIEW bronze_transactions
COMMENT "Raw transaction data from POS systems"
TBLPROPERTIES ("quality" = "bronze", "domain" = "finance")
AS SELECT
  *,
  current_timestamp() AS audit_timestamp,
  'pos' AS source_system
FROM source_table
WHERE transaction_id IS NOT NULL;
```
