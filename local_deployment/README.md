# Local Deployment (Gitignored)

**Everything in this folder except this README is gitignored.** This is intentional.

This folder contains workspace-specific deployment configuration -- workspace URLs, CLI profiles, catalog/schema names, and DAB bundle settings that are unique to your environment. These must never be committed to a public repository.

## Why This Folder Exists

The skills, instructions, and standards in this repo are designed to be portable across any Databricks workspace. But to actually deploy and demo them, you need environment-specific config (which workspace, which catalog, which profile). That config lives here, locally, and never leaves your machine.

## What Goes Here

| File / Folder | Location | Purpose |
|---------------|----------|---------|
| `databricks.yml` | **Repo root** | DAB bundle config -- workspace host, catalog, schema, variables |
| `resources/datagen_job.yml` | `local_deployment/` | DAB job resource -- deploys and runs the data generation notebook |
| `resources/bakehouse_install_job.yml` | `local_deployment/` | DAB job resource -- installs the AI/BI Bakehouse Marketplace share and mirrors selected tables into the demo catalog |
| `bakehouse_config.yaml` | `local_deployment/` | Local Bakehouse install/mirror config (copy from `marketplace_data/bakehouse_config.example.yaml`) |
| `mcp_config.json` | `local_deployment/` | Local MCP connection config (copy from `mcp/mcp_config.example.json`) |
| `instructions_to_use/` | `local_deployment/` | Ready-to-use instruction files with your org/repo values filled in |
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
  bakehouse_scratch_catalog:
    description: Scratch catalog where the AI/BI Bakehouse Marketplace share is installed (data is mirrored from here into the demo catalog)
    default: bakehouse_share_scratch
  bakehouse_listing_name:
    description: Marketplace listing name to install
    default: AI/BI Bakehouse
  bakehouse_share_provider_name:
    description: Provider filter applied when searching the Marketplace listing
    default: databricks
  bakehouse_demo_schema:
    description: Schema (inside the existing demo catalog) where Bakehouse tables are mirrored for the Stage 5 demo
    default: bakehouse

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
      bakehouse_scratch_catalog: <your-scratch-catalog-eg-bakehouse_share_scratch_alice>
      bakehouse_demo_schema: bakehouse
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

### Example `resources/bakehouse_install_job.yml`

```yaml
resources:
  jobs:
    install_bakehouse:
      name: "[${bundle.target}] Install AI/BI Bakehouse"
      tasks:
        - task_key: install_bakehouse
          existing_cluster_id: ${var.shared_cluster_id}
          notebook_task:
            notebook_path: ../../marketplace_data/install_bakehouse.py
            base_parameters:
              scratch_catalog_name: ${var.bakehouse_scratch_catalog}
              listing_name: ${var.bakehouse_listing_name}
              share_provider_name: ${var.bakehouse_share_provider_name}
              demo_catalog: ${var.catalog_name}
              demo_schema: ${var.bakehouse_demo_schema}
```

### Bakehouse Marketplace install

The `@sentiment-analysis` skill demo (Stage 5 in [`docs/DEMO_SCRIPT.md`](../docs/DEMO_SCRIPT.md)) reads from the **AI/BI Bakehouse** Marketplace share. The install notebook is **detect-then-install**:

1. Probes each catalog in `${var.bakehouse_candidate_source_catalogs}` (default: `bakehouse`) to see if any are already readable as the running user. On shared field demo workspaces Bakehouse is usually pre-installed, so this avoids a redundant Marketplace install.
2. **Only if no candidate is readable**, falls back to installing the Marketplace share into a scratch catalog (`${var.bakehouse_scratch_catalog}`).
3. CTAS-mirrors the tables we use (`customer_reviews`, `franchises`, `transactions`, `customers`) into `${var.catalog_name}.${var.bakehouse_demo_schema}` so the rest of the demo lives under the same catalog as the synthetic financial datasets.

Steps:

1. Copy the config template:

```bash
cp marketplace_data/bakehouse_config.example.yaml local_deployment/bakehouse_config.yaml
```

2. Edit `local_deployment/bakehouse_config.yaml` and fill in `workspace_host`, `profile`, `candidate_source_catalogs` (catalogs to probe before installing -- e.g. `bakehouse` on shared field demo workspaces), `scratch_catalog_name` (per-user fallback), `demo_catalog` (your existing demo catalog), and `demo_schema` (default: `bakehouse`).

3. Deploy and run via DAB (preferred):

```bash
databricks bundle deploy --profile <your-cli-profile>
databricks bundle run install_bakehouse --profile <your-cli-profile>
```

4. Or, deploy and run via the standalone script (no DAB):

```bash
./marketplace_data/deploy.sh --run
```

Re-runs are safe: the Marketplace install is skipped if the scratch catalog already exists, and the mirror tables use `CREATE OR REPLACE TABLE`. After the job succeeds the demo data is available at `${var.catalog_name}.${var.bakehouse_demo_schema}.customer_reviews` and the other mirrored tables.

### MCP Connection

The MCP connection must be created in a **SQL context** so that the `secret()` function resolves -- the SQL Editor works, and so does the SQL Statement Execution API (run against a SQL warehouse). Plain REST/CLI catalog APIs and DAB do **not** resolve `secret()`, so use one of the SQL paths below.

1. Store your GitHub PAT in a secret scope. Because this repo is **public**, the token needs **no scopes** -- a classic PAT with no scopes selected, or a fine-grained PAT with read-only `Contents` access to the public repo, is enough (do not grant `repo` / `read:org`):

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

### Instructions

The `instructions/` folder at the repo root contains **templates** with placeholders. To create ready-to-use versions:

1. Create `local_deployment/instructions_to_use/` (gitignored)
2. Pick the files that match your approach:

| Scope | Direct Skills | MCP |
|-------|--------------|-----|
| User-level | `user_instructions_skills.md` | `user_instructions_mcp.md` |
| Workspace-level | `workspace_instructions_skills.md` | `workspace_instructions_mcp.md` |

3. Fill in your GitHub org/repo (MCP files only) and any pipeline names
4. Upload to your workspace:
   - User-level → `/Users/{username}/.assistant_instructions.md`
   - Workspace-level → `Workspace/.assistant_workspace_instructions.md`

### Deploy

```bash
databricks bundle deploy --profile <your-cli-profile>
databricks bundle run generate_financial_data --profile <your-cli-profile>
```
