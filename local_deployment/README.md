# Local Deployment (Gitignored)

**Everything in this folder except this README is gitignored.** This is intentional.

This folder contains workspace-specific deployment configuration -- workspace URLs, CLI profiles, catalog/schema names, and DAB bundle settings that are unique to your environment. These must never be committed to a public repository.

## Why This Folder Exists

The skills, instructions, and standards in this repo are designed to be portable across any Databricks workspace. But to actually deploy and demo them, you need environment-specific config (which workspace, which catalog, which profile). That config lives here, locally, and never leaves your machine.

## What Goes Here

| File | Location | Purpose |
|------|----------|---------|
| `databricks.yml` | **Repo root** | DAB bundle config -- workspace host, catalog, schema, variables |
| `resources/datagen_job.yml` | `local_deployment/` | DAB job resource -- deploys and runs the data generation notebook |
| `mcp_config.json` | `local_deployment/` | Local MCP connection config (copy from `mcp/mcp_config.example.json`) |
| Any other `.yml`, `.json`, `.env` | `local_deployment/` | Environment-specific overrides |

## For Other Users of This Repo

If you clone this repo and want to deploy to your own workspace:

1. Create `databricks.yml` at the **repo root** (it's gitignored)
2. Create `local_deployment/resources/` folder with your job configs
3. Run `databricks bundle deploy` from the **repo root**

### Example `databricks.yml`

Place this at the **repo root** (it's gitignored there), with `include` pointing into `local_deployment/resources/`:

```yaml
bundle:
  name: genie-code-skills-demo

variables:
  catalog_name:
    description: Unity Catalog name for demo
    default: <your-catalog>
  schema_name:
    description: Schema name for demo data
    default: <your-schema>
  volume_name:
    description: Volume for raw CSV data
    default: raw_data
  shared_cluster_id:
    description: Existing shared cluster ID (avoids cold start)
    default: ""

workspace:
  host: https://<your-workspace>.cloud.databricks.com

include:
  - local_deployment/resources/*.yml

targets:
  dev:
    mode: development
    default: true
    variables:
      shared_cluster_id: "<your-cluster-id>"
```

### Example `resources/datagen_job.yml`

```yaml
resources:
  jobs:
    generate_financial_data:
      name: "[${bundle.target}] Generate Financial Data"
      tasks:
        - task_key: generate_data
          existing_cluster_id: ${var.shared_cluster_id}
          notebook_task:
            notebook_path: ../../sample_data_gen/generate_financial_data.py
            base_parameters:
              catalog: ${var.catalog_name}
              schema: ${var.schema_name}
              volume: ${var.volume_name}
          libraries:
            - pypi:
                package: dbldatagen
```

### MCP Connection

The MCP connection **must** be created via SQL Editor (not API/CLI/DAB). The `secret()` function only resolves correctly in SQL context.

1. Store your GitHub PAT in a secret scope:

```bash
databricks secrets create-scope <your-scope> --profile <your-cli-profile>
databricks secrets put-secret <your-scope> GITHUB_PAT --string-value "<your-pat>" --profile <your-cli-profile>
```

2. Run this in the **Databricks SQL Editor**:

```sql
CREATE CONNECTION IF NOT EXISTS `genie-code-skills-mcp`
TYPE HTTP
OPTIONS (
  host = 'https://api.githubcopilot.com',
  base_path = '/mcp',
  bearer_token = secret('<your-scope>', 'GITHUB_PAT'),
  is_mcp_connection = 'true'
)
COMMENT 'GitHub MCP - Genie Code skills and standards';
```

3. Verify:

```sql
DESCRIBE CONNECTION `genie-code-skills-mcp`;
```

### Deploy

```bash
databricks bundle deploy --profile <your-cli-profile>
databricks bundle run generate_financial_data --profile <your-cli-profile>
```
