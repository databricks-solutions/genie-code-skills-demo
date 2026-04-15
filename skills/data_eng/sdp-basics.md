---
name: sdp-basics
description: Apply basic SDP pipeline best practices for table naming, comments, and table properties. Use when creating or modifying tables in Spark Declarative Pipelines. Always generate SDP pipelines using SQL, not Python.
---

# SDP Pipeline Basics

Always build SDP pipelines using SQL (not Python). When creating or modifying tables in SDP pipelines, follow these rules.

## Table Naming

All table names MUST use `lowercase_snake_case` with a layer prefix:

| Layer | Prefix | Example |
|-------|--------|---------|
| Bronze | `bronze_` | `bronze_transactions` |
| Silver | `silver_` | `silver_customers` |
| Gold | `gold_` | `gold_daily_revenue` |

Never use PascalCase, UPPERCASE, kebab-case, or camelCase. Never omit the layer prefix.

## Table Types

| Type | When to Use | Syntax |
|------|-------------|--------|
| `STREAMING TABLE` | File ingestion (Auto Loader), CDC, real-time data | `CREATE OR REFRESH STREAMING TABLE` |
| `MATERIALIZED VIEW` | Batch data from existing Delta tables, aggregations | `CREATE OR REFRESH MATERIALIZED VIEW` |
| `LIVE.table_name` | Referencing tables within the same pipeline | `FROM LIVE.bronze_articles` |

## Comments

Every table MUST have a `COMMENT` clause describing its purpose:

| Layer | Pattern |
|-------|---------|
| Bronze | `COMMENT "Raw <entity> data from <source>"` |
| Silver | `COMMENT "Cleaned and validated <entity> with derived metrics"` |
| Gold | `COMMENT "Business aggregation for <use case>"` |

## Table Properties

Every table MUST have `TBLPROPERTIES` with at least the quality tag:

```sql
TBLPROPERTIES ("quality" = "bronze")
TBLPROPERTIES ("quality" = "silver", "delta.enableChangeDataFeed" = "true", "delta.enableRowTracking" = "true")
TBLPROPERTIES ("quality" = "gold", "delta.enableChangeDataFeed" = "true")
```

## Audit Columns

Every table MUST include these two columns as the LAST columns in the SELECT:

```sql
current_timestamp() AS audit_timestamp,
'<source_description>' AS source_system
```

## Data Quality Constraints

- **Bronze**: Use `WHERE` clause filtering only (preserve raw data)
- **Silver**: Use `CONSTRAINT` clauses for validation
  - `ON VIOLATION FAIL UPDATE` for critical fields
  - `ON VIOLATION DROP ROW` for non-critical fields
- **Gold**: Generally no constraints (data validated in Silver)

## Data Quality Flag

Silver tables MUST include a `data_quality_flag` column:

```sql
CASE
  WHEN <field> IS NULL THEN 'MISSING_<FIELD>'
  WHEN <field> < 0 THEN 'NEGATIVE_<FIELD>'
  ELSE 'CLEAN'
END AS data_quality_flag
```

## SQL Formatting

| Element | Case |
|---------|------|
| SQL keywords | UPPERCASE (`SELECT`, `FROM`, `WHERE`, `AS`) |
| Table/column names | lowercase_snake_case |
| Aliases | short lowercase (`t`, `a`, `d`) |
| Functions | UPPERCASE (`ROUND()`, `CAST()`, `COALESCE()`) |

## Column Organization Order

1. Identifiers (primary keys, foreign keys)
2. Dimensions (categories, hierarchies)
3. Measures (quantities, amounts)
4. Derived/calculated fields
5. Data quality flags
6. **Audit columns LAST** (`audit_timestamp`, `source_system`)

## Clustering

Add `CLUSTER BY AUTO` for `STREAMING TABLE` definitions.

## Joins

- Use `LIVE.table_name` to reference tables within the same pipeline
- Use fully qualified names for tables outside the pipeline
- Always use explicit `JOIN` syntax with table aliases

## Example

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
