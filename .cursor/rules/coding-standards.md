# Coding Standards

## General Rules

- Do not put emojis in SQL, Python, or general code files.
- Do not hallucinate. If you are unsure about an API, SDK method, or behavior, say so.
- **Always ask before committing.** Never `git commit` or `git push` without explicit user approval.
- Never make architecture changes without asking the user first.
- Always try programmatic approaches (Databricks SDK, REST API, CLI, DAB resources) before suggesting manual UI steps.

## Databricks Development

- Always build SDP (Spark Declarative Pipelines) using **SQL, not Python**. All tables must be defined as `CREATE OR REFRESH MATERIALIZED VIEW` or `CREATE OR REFRESH STREAMING TABLE` in `.sql` files.
- Use `dbldatagen` (Databricks Labs Data Generator) for synthetic data generation. Prefer it over hand-rolling random data with pandas/Faker for Spark-scale data.
- For Databricks-specific patterns and best practices, refer to the [Databricks AI Dev Kit](https://github.com/databricks-solutions/ai-dev-kit).

## Documentation

- Keep documentation concise. Consolidate rather than scatter across many files.
- The README is the primary user-facing document. Keep it comprehensive but scannable.

## Code Quality

- Read existing code before editing.
- Fix linter errors you introduce.
- Do not add comments that just narrate what the code does.
