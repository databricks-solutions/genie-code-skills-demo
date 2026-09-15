---
name: sdp-basics
description: Apply basic SDP pipeline best practices for table naming, comments, and table properties. Use when creating or modifying tables in Spark Declarative Pipelines. Always generate SDP pipelines using SQL, not Python.
---

# SDP Pipeline Basics

Always build SDP pipelines using SQL (not Python). When creating or modifying tables in SDP pipelines, follow these rules.

For copy-paste SQL patterns (bronze CREATE, audit columns, data-quality flag), read [sql-templates.md](sql-templates.md).

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

Do **not** use `CREATE OR REFRESH LIVE TABLE` (deprecated) or the `LIVE.` virtual schema. In default publishing mode, `LIVE.` is ignored. Reference other datasets in the same pipeline by unqualified table name (pipeline catalog/schema) or a fully qualified `catalog.schema.table`. See [LIVE schema (legacy)](https://docs.databricks.com/aws/en/ldp/live-schema).

## Comments

Every table MUST have a `COMMENT` clause describing its purpose:

| Layer | Pattern |
|-------|---------|
| Bronze | `COMMENT "Raw <entity> data from <source>"` |
| Silver | `COMMENT "Cleaned and validated <entity> with derived metrics"` |
| Gold | `COMMENT "Business aggregation for <use case>"` |

## Table Properties

Every table MUST have `TBLPROPERTIES` with at least `quality` (add `domain` where known). Do **not** set `"owner"` -- Databricks reserves that key and raises an error. Table ownership is the pipeline run-as identity ([reserved table property keys](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-tblproperties)).

```sql
TBLPROPERTIES ("quality" = "bronze", "domain" = "finance")
TBLPROPERTIES ("quality" = "silver", "domain" = "finance", "delta.enableChangeDataFeed" = "true", "delta.enableRowTracking" = "true")
TBLPROPERTIES ("quality" = "gold", "domain" = "finance", "delta.enableChangeDataFeed" = "true")
```

## Audit Columns

Every table MUST include these two columns as the LAST columns in the SELECT. See [sql-templates.md](sql-templates.md) for the exact expressions.

## Data Quality Constraints

- **Bronze**: Use `WHERE` clause filtering only (preserve raw data)
- **Silver**: Use `CONSTRAINT` clauses for validation
  - `ON VIOLATION FAIL UPDATE` for critical fields
  - `ON VIOLATION DROP ROW` for non-critical fields
- **Gold**: Generally no constraints (data validated in Silver)

## Data Quality Flag

Silver tables MUST include a `data_quality_flag` column. Use the CASE pattern in [sql-templates.md](sql-templates.md).

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

- Reference other datasets in the same pipeline by table name (`FROM bronze_articles`), not `LIVE.bronze_articles`
- Use fully qualified names for tables outside the pipeline
- Read streaming sources with the `STREAM` keyword (`FROM STREAM read_files(...)` or `FROM STREAM source_table`). Do not use `STREAM` when creating a materialized view.
- Always use explicit `JOIN` syntax with table aliases
