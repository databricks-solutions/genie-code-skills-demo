# AGENTS.md -- Enterprise Data Engineering Standards

Genie Code automatically discovers and reads `AGENTS.md` (and `CLAUDE.md`) files in the workspace directory tree and injects them into its context - no configuration required. Keep this file checked in so every teammate gets the same conventions automatically. See [Customize Genie Code with custom instructions](https://docs.databricks.com/aws/en/genie-code/instructions).

These are always-on standards. For detailed, task-specific guidance, Genie Code loads the matching skill from `skills/` (auto-loaded by description, or invoked in chat with `@<skill-name>`).

## Always

- Build Spark Declarative Pipelines (SDP) in **SQL, not Python**. Define tables as `CREATE OR REFRESH MATERIALIZED VIEW` or `CREATE OR REFRESH STREAMING TABLE` in `.sql` files.
- Name tables `lowercase_snake_case` with a layer prefix: `bronze_`, `silver_`, `gold_`. No PascalCase, UPPERCASE, kebab-case, or camelCase.
- Give every table a `COMMENT` and `TBLPROPERTIES` with at least `quality` (add `domain` where known). Do not set TBLPROPERTIES `owner` -- that key is reserved; Unity Catalog table owner is the pipeline run-as identity.
- Make `audit_timestamp` and `source_system` the LAST two columns of every table.
- For tables with personal data, set `contains_pii = "true"` and `pii_columns` in `TBLPROPERTIES`, and annotate PII columns inline (for example `-- [PII: EMAIL - HIGH]`).

## Skills

Genie Code should apply these skills when relevant (auto-loaded, or `@` mention in chat to force):

- `@table-governance` -- COMMENT, TBLPROPERTIES, column descriptions, UC tags, table-level PII labeling. Apply first, to every table.
- `@sdp-basics` -- SDP naming, table types, audit columns, data-quality constraints, SQL formatting.
- `@pii-management` -- detect, label, annotate, and mask PII in tables with personal data.
- `@sentiment-analysis` -- AI-function patterns (`ai_analyze_sentiment`, `ai_classify`, `ai_extract`) for tables built from free-form text.

## Routing

- Every pipeline table: apply `@table-governance` and `@sdp-basics`.
- Customer or personal data: also apply `@pii-management`.
- Sentiment / topics / entities from text via AI functions: also apply `@sentiment-analysis`.

## Compliance

This is a public repository. Never hard-code workspace URLs, catalog/schema names, connection names, secrets, or other environment-specific values in committed files. Keep real configuration in the gitignored `local_deployment/` folder.
