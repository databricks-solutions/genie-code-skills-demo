---
name: table-governance
description: Enforce table and column documentation standards across all tables. Use for every table you create or modify. Covers COMMENT clauses, TBLPROPERTIES, column descriptions, PII labeling at the table level, and Unity Catalog tags. This is the baseline governance skill -- apply it before any other skill.
---

# Table and Column Governance Standards

Apply these documentation and governance rules to **every** table, regardless of layer or domain. This skill takes priority and should be applied first, before domain-specific skills like `sdp-basics` or `pii-management`.

For a complete CREATE + ALTER TABLE + SET TAGS example, read [governance-template.md](governance-template.md).

## Table-Level Documentation

### COMMENT Clause (Required)

Every table MUST have a `COMMENT` clause. The comment must describe:
1. What the table contains
2. The data source or upstream table
3. Whether the table contains PII (if applicable)

| Layer | Pattern |
|-------|---------|
| Bronze | `COMMENT "Raw <entity> data ingested from <source>"` |
| Silver | `COMMENT "Cleaned and validated <entity> with derived metrics from bronze_<entity>"` |
| Gold | `COMMENT "Business aggregation: <metric> by <dimensions>"` |
| PII | Append ` - CONTAINS PII: <column_list>` to any table with personal data |

### TBLPROPERTIES (Required)

Every table MUST have `TBLPROPERTIES` with at minimum:

```sql
TBLPROPERTIES (
  "quality" = "<bronze|silver|gold>",
  "owner" = "<team-or-domain>",
  "domain" = "<business-domain>"
)
```

Additional required properties by context:

| Condition | Additional Properties |
|-----------|-----------------------|
| Contains PII | `"contains_pii" = "true"`, `"pii_columns" = "<column_list>"` |
| Silver/Gold layer | `"delta.enableChangeDataFeed" = "true"` |
| Streaming table | `"delta.enableRowTracking" = "true"` |
| Subject to retention | `"retention_days" = "<number>"` |

## Column-Level Documentation

After creating a table, add column descriptions for key columns using `ALTER TABLE`. See [governance-template.md](governance-template.md) for the full statement.

At minimum, add descriptions for:
- Primary keys and foreign keys
- Derived or calculated columns (explain the logic)
- PII columns (note the risk level and any masking applied)
- Data quality flag columns
- Audit columns
- Any column whose meaning is not obvious from its name

| Column Type | Description Pattern |
|-------------|---------------------|
| Primary key | `'Unique <entity> identifier from <source>'` |
| Foreign key | `'References <parent_table>.<parent_column>'` |
| Derived numeric | `'Calculated as <formula>. Units: <unit>'` |
| Derived category | `'Derived <category> bracket: <value1> / <value2> / ...'` |
| Masked PII | `'<Masking method> of <original_column> for PII protection'` |
| Audit timestamp | `'Pipeline execution timestamp'` |
| Source system | `'Upstream source system identifier'` |
| DQ flag | `'Row-level data quality status: <possible values>'` |

## PII Labeling at Table Level

Tables containing personal data require additional governance:

1. **TBLPROPERTIES** must include `"contains_pii" = "true"` and `"pii_columns"` listing all PII column names
2. **COMMENT** must include `CONTAINS PII: <column_list>`
3. **Column descriptions** for PII columns must note the PII type and risk level
4. **Unity Catalog tags** should be applied where supported (see [governance-template.md](governance-template.md))

## Unity Catalog Tags

Use tags for discoverability and governance automation:

| Tag | Values | Purpose |
|-----|--------|---------|
| `quality` | `bronze`, `silver`, `gold` | Layer classification |
| `domain` | `finance`, `hr`, `marketing`, etc. | Business domain |
| `pii` | `true`, `false` | PII flag for governance scanning |
| `data_classification` | `public`, `internal`, `confidential`, `restricted` | Access control tier |
| `owner` | `<team-name>` | Ownership for accountability |
| `sla` | `daily`, `hourly`, `real-time` | Freshness expectation |

## Governance Checklist

Before completing any table definition, verify ALL of the following:

- [ ] `COMMENT` clause is present and descriptive
- [ ] `TBLPROPERTIES` includes at least `quality` and `owner`
- [ ] If PII is present: `contains_pii` and `pii_columns` are in TBLPROPERTIES
- [ ] If PII is present: COMMENT mentions `CONTAINS PII`
- [ ] Column descriptions added for primary keys, derived columns, and PII columns
- [ ] Unity Catalog tags applied (`quality`, `domain`, `pii`, `data_classification`)
- [ ] `audit_timestamp` and `source_system` are the last two columns
