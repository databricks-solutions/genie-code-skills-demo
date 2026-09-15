# Genie Code Skills Demo

Example [Genie Code](https://docs.databricks.com/aws/en/genie-code/) skills, custom instructions, and MCP setup for enforcing enterprise data engineering standards across Databricks development.

---

## What is Genie Code?

[Genie Code](https://docs.databricks.com/aws/en/genie-code/) is Databricks' AI coding assistant. It can:

- **Author SDP pipelines** -- streaming tables, materialized views, CDC, medallion architecture
- **Develop notebooks** -- Python, SQL, Scala, R
- **Build DSML workflows** -- MLflow experiment tracking, model training, feature engineering
- **Create AI/BI dashboards** -- data visualizations and business intelligence
- **Develop Databricks Apps** -- full-stack applications on the lakehouse
- **Manage Unity Catalog** -- governance, permissions, lineage
- **Orchestrate jobs and workflows** -- scheduling, dependencies, monitoring

Genie Code supports **skills** (task-specific instructions following the open [Agent Skills](https://agentskills.io/) standard -- each skill is a folder with a `SKILL.md`), **instructions** (user- and workspace-level, plus auto-discovered `AGENTS.md` / `CLAUDE.md` files), and **MCP** ([Model Context Protocol](https://modelcontextprotocol.io/)) connections that fetch enterprise standards from external sources like GitHub.

---

## Demo Coverage

This repo provides example skills, instructions, and tooling organized by domain. Each phase adds a new area of coverage.

| Phase | Date | Domain | What's Included |
|-------|------|--------|-----------------|
| **Phase 1** | April 2026 | Data Engineering | SDP pipeline skills, PII management, table governance, MCP-based standards enforcement, sample financial data generation |
| **Phase 2** | May 2026 | DSML | `sentiment-analysis` skill, AI-function patterns (`ai_analyze_sentiment`, `ai_classify`, `ai_extract`), AI/BI Bakehouse Marketplace install |
| Planned | -- | Dashboards, Governance | Additional skill domains and MCP integrations |

---

## What This Repo Contains

| Folder | Contents |
|--------|----------|
| `skills/` | One folder per skill (`SKILL.md` + templates). Deploy with a vibe tool, `./skills/deploy.sh`, or a manual copy; also served via MCP |
| `AGENTS.md` | Auto-discovered enterprise standards -- Genie Code reads this automatically from the workspace directory tree |
| `instructions/` | Instruction **templates** (placeholders). Copy and fill in for your workspace -- by hand or with a vibe tool. Do not treat these as ready-to-upload. |
| `mcp/` | Unity Catalog HTTP MCP connection to GitHub (no-scope PAT). See `mcp/README.md`. |
| `sample_data_gen/` | Synthetic financial data generation notebook (uses `dbldatagen`) |
| `marketplace_data/` | Installer notebook + config template for sourcing datasets from the Databricks Marketplace (currently AI/BI Bakehouse) |
| `local_deployment/` | **Gitignored.** Your workspace-specific DAB config for deploying to your environment. See `local_deployment/README.md` for setup instructions. |

---

## How It Works

This demo shows three stages of Genie Code customization:

### 1. Baseline

Genie Code generates SDP pipeline code with no guidance. The output is functional but lacks naming conventions, audit columns, and PII handling.

### 2. Skills

Add `table-governance`, `sdp-basics`, and `pii-management` skills to your workspace. Genie Code now applies documentation standards, naming conventions, audit columns, TBLPROPERTIES, column descriptions, and PII annotations automatically.

### 3. MCP + Instructions

Connect Genie Code to GitHub through a Unity Catalog MCP connection (`genie-code-skills-mcp`) so it fetches the same skills from this public repo. The result is automatic compliance with organizational policies, maintained centrally in version control.

---

## Quick Start

### Prerequisites

- A Databricks workspace with Genie Code enabled
- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) installed and configured
- A GitHub personal access token with **no scopes** (this repo is public)

### 1. Install Skills

The `skills/` folder is ready to copy into Genie Code's skills directory. Each skill is its own folder with a required `SKILL.md` plus companion template markdown (the layout from [Extend Genie Code with agent skills](https://docs.databricks.com/aws/en/genie-code/skills)).

**Use a vibe tool (Genie Code, Cursor, or similar), or do it by hand.** Either works:

- **Vibe tool:** open this repo and ask it to deploy the `skills/` folders into your workspace skills directory -- user-level `/Users/{you}/.assistant/skills/` or workspace-level `Workspace/.assistant/skills/` (admin).
- **Manual / CLI:** copy the folders in the workspace UI, or from the repo root:

```bash
# User-level -- /Users/{you}/.assistant/skills/  (uses your CLI identity)
./skills/deploy.sh

# Same, with an explicit CLI profile
./skills/deploy.sh --profile <your-cli-profile>

# Workspace-level -- Workspace/.assistant/skills/  (workspace admin)
./skills/deploy.sh --workspace --profile <your-cli-profile>
```

The script creates the target folder if needed and overwrites files already there. Equivalent CLI:

```bash
databricks workspace mkdirs /Workspace/Users/<you>/.assistant/skills
databricks workspace import-dir skills/table-governance \
  /Workspace/Users/<you>/.assistant/skills/table-governance --overwrite
# repeat for sdp-basics, pii-management, sentiment-analysis
```

After install, the workspace looks like:

```
Workspace/.assistant/skills/            # workspace-level
# or /Users/{you}/.assistant/skills/    # user-level
  table-governance/
    SKILL.md
    governance-template.md
  sdp-basics/
    SKILL.md
    sql-templates.md
  pii-management/
    SKILL.md
    masking-templates.md
  sentiment-analysis/
    SKILL.md
    pipeline-templates.md
```

Start a **new Genie Code chat** so the skills load. Genie Code auto-loads a skill when your request matches its `description`. In chat, you can still force a skill with `@table-governance`, `@sdp-basics`, `@pii-management`, or `@sentiment-analysis` (`@` is skill invocation, not instruction syntax).

### 2. Set Up MCP (Optional)

Genie Code fetches `skills/` from this GitHub repo through a Unity Catalog HTTP
MCP connection (`genie-code-skills-mcp`) authenticated with a **no-scope GitHub
PAT**. See [`mcp/README.md`](mcp/README.md).

Do not use managed GitHub OAuth or a PAT belonging to a member of an
IP-allowlisted GitHub org (including a PAT with `repo` / `read:org`).
Those tokens fail from Databricks serverless with
"GitHub MCP is blocked by IP allowlist". Use a **no-scope PAT** from a
GitHub user outside that org.

```bash
cp mcp/mcp_config.example.json mcp/mcp_config.json   # fill in owner/repo/secret scope
python mcp/deploy_mcp.py --config mcp/mcp_config.json
```

Run the printed `CREATE CONNECTION` SQL in a SQL editor so `secret()` resolves.
Then enable the connection in Genie Code settings → MCP Servers
(`get_file_contents`, `search_code`), point the MCP instruction templates at
this repo (or your fork), and start a **new** Genie Code chat.

### 3. Add Instructions

The files in [`instructions/`](instructions/) are **templates with placeholders**. They are not ready to upload as-is. Copy one, fill in `<your-pipeline-name>`, GitHub org/repo, and any other blanks for *your* workspace, then upload. Do that by hand, or ask your vibe tool to adjust the template -- keep the copies in this repo as templates so the next person can fill them in too.

Filled-in copies belong in gitignored `local_deployment/instructions_to_use/` (see `local_deployment/README.md`), not in `instructions/`.

1. Choose your approach (**direct skills** or **MCP**) and scope (**user-level** or **workspace-level**)
2. Start from the matching template (or from a filled-in copy under `local_deployment/instructions_to_use/` if you already made one):

| Scope | Direct Skills | MCP |
|-------|--------------|-----|
| User-level | `user_instructions_skills.md` | `user_instructions_mcp.md` |
| Workspace-level | `workspace_instructions_skills.md` | `workspace_instructions_mcp.md` |

3. Fill in remaining placeholders (GitHub org/repo for MCP files)
4. Upload to your workspace:
   - **User-level** → `/Users/{username}/.assistant_instructions.md`
   - **Workspace-level** → `Workspace/.assistant_workspace_instructions.md`

Workspace instructions take priority over user instructions when both are present.

> **Auto-discovered instructions:** Genie Code also walks up the workspace directory tree and automatically reads any `AGENTS.md` (or `CLAUDE.md`) files it finds -- no upload or configuration needed. This repo ships a root [`AGENTS.md`](AGENTS.md) with the always-on standards, so once the repo is synced into a workspace those conventions apply to every teammate automatically. See [Customize Genie Code with custom instructions](https://docs.databricks.com/aws/en/genie-code/instructions).

---

## Try It Yourself -- Sample Data

Generate synthetic financial data to test the skills end-to-end. The data generation notebook uses [`dbldatagen`](https://github.com/databrickslabs/dbldatagen) (Databricks Labs Data Generator) for Spark-native synthetic data generation.

### Option A: Deploy with DAB (Recommended)

Set up a local deployment folder with your workspace-specific config:

```bash
# See local_deployment/README.md for full setup instructions and examples
# Create databricks.yml at the repo root and resource configs in local_deployment/resources/

# Deploy and run from the repo root
databricks bundle deploy --profile <your-cli-profile>
databricks bundle run generate_financial_data --profile <your-cli-profile>
```

### Option B: Run Interactively

Upload the notebook to your workspace manually and run it interactively -- set the `catalog`, `schema`, and `volume` widget values when prompted.

### Build a Pipeline

With the sample data in your volume, use Genie Code:

> "Create an SDP pipeline that reads the financial CSV files from `/Volumes/{catalog}/{schema}/raw_data/` and builds a bronze-silver-gold medallion architecture."

Genie Code will apply the skills and standards automatically.

### Run the Demo

For a guided walkthrough that progressively adds skills, instructions, and MCP, see [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md). It includes specific prompts, setup/cleanup steps for each stage, and observation checklists showing what to look for.

---

## Try It Yourself -- Bakehouse Sentiment Analysis

Stage 5 of the demo applies the new `@sentiment-analysis` skill to the **AI/BI Bakehouse** dataset from the Databricks Marketplace. The flow is:

1. Install the Marketplace share into a scratch catalog and mirror selected tables into a new schema inside your existing demo catalog. This keeps the demo data under one predictable namespace (`<demo_catalog>.bakehouse.*`).
2. Use Genie Code with `@sentiment-analysis` to generate bronze/silver/gold tables that turn `<demo_catalog>.bakehouse.customer_reviews` into a sentiment dataset using AI functions (`ai_analyze_sentiment`, `ai_classify`, `ai_extract`).

### 1. Install the Bakehouse share + mirror into the demo catalog

Copy the config template and fill in your workspace details:

```bash
cp marketplace_data/bakehouse_config.example.yaml local_deployment/bakehouse_config.yaml
# Edit local_deployment/bakehouse_config.yaml:
#   workspace_host, profile,
#   scratch_catalog_name  (where the share lands -- pick a unique per-user name),
#   demo_catalog          (your existing demo catalog),
#   demo_schema           (default: bakehouse)
```

Then either deploy via DAB:

```bash
databricks bundle deploy --profile <your-cli-profile>
databricks bundle run install_bakehouse --profile <your-cli-profile>
```

…or run the standalone script:

```bash
./marketplace_data/deploy.sh --run
```

The notebook is idempotent: it skips the Marketplace install when `scratch_catalog_name` already exists, and uses `CREATE OR REPLACE TABLE` for the mirror so re-runs are safe.

### 2. Generate the pipeline with Genie Code

In a Genie Code session with the skills available (workspace-uploaded or via MCP):

> Build a bronze, silver, and gold pipeline from `<demo_catalog>.bakehouse.customer_reviews`. Add sentiment, topic, and extracted entities on silver using AI functions, then aggregate sentiment by franchise on gold. Apply `@table-governance`, `@sdp-basics`, `@pii-management`, and `@sentiment-analysis`.

The result is a governed sentiment-analysis pipeline that follows every project standard: layer prefixes, audit columns, AI cost guardrails, sentiment label constraints, and PII annotations on the raw `review_text`.

---

## Project Structure

```
genie-code-skills-demo/
├── .cursor/rules/                          # Cursor IDE rules
│   ├── public-repo-compliance.md
│   ├── coding-standards.md
│   └── branch-conventions.md
├── AGENTS.md                               # Auto-discovered enterprise standards (Genie Code reads this automatically)
├── skills/                                 # One folder per skill (also served via MCP)
│   ├── deploy.sh                           # Optional CLI deploy (vibe tool or manual copy also work)
│   ├── table-governance/
│   │   ├── SKILL.md                        # Governance rules and checklist
│   │   └── governance-template.md          # Reusable CREATE / ALTER / TAG SQL
│   ├── sdp-basics/
│   │   ├── SKILL.md                        # Naming, audit columns, DQ rules
│   │   └── sql-templates.md                # Reusable CREATE SQL
│   ├── pii-management/
│   │   ├── SKILL.md                        # Detection, labeling, layer rules
│   │   └── masking-templates.md            # Reusable masking / derivation SQL
│   └── sentiment-analysis/
│       ├── SKILL.md                        # AI-function rules and guardrails
│       └── pipeline-templates.md           # Bronze / silver / gold SQL
├── instructions/                           # Instruction TEMPLATES (with placeholders)
│   ├── .assistant_instructions.md          # User-level template
│   └── .assistant_workspace_instructions.md # Workspace-level template
├── mcp/
│   ├── README.md                           # No-scope PAT GitHub MCP connection
│   ├── mcp_config.example.json             # Owner / repo / secret scope / connection name
│   └── deploy_mcp.py                       # Stores PAT and prints CREATE CONNECTION SQL
├── sample_data_gen/
│   ├── generate_financial_data.py          # Databricks notebook (dbldatagen, parameterized)
│   ├── deploy_config.example.yaml          # Deploy config template (placeholders)
│   └── deploy.sh                           # Deploy script (reads local config)
├── marketplace_data/
│   ├── install_bakehouse.py                # Databricks notebook (uses databricks-sdk Marketplace API)
│   ├── bakehouse_config.example.yaml       # Bakehouse install config template (placeholders)
│   └── deploy.sh                           # Deploy/run script for the install notebook
├── docs/
│   └── DEMO_SCRIPT.md                     # Five-stage guided demo walkthrough
├── local_deployment/                       # GITIGNORED (except README)
│   ├── README.md                           # How to set up your own local deployment
│   └── instructions_to_use/               # Ready-to-use instruction files (filled in)
│       ├── user_instructions_skills.md    # User-level, direct skills
│       ├── user_instructions_mcp.md       # User-level, MCP
│       ├── workspace_instructions_skills.md # Workspace-level, direct skills
│       └── workspace_instructions_mcp.md  # Workspace-level, MCP
├── README.md
├── LICENSE.md
├── NOTICE.md
├── SECURITY.md
├── CODEOWNERS
└── .gitignore
```

---

## Customization

This repo is a starting point. To adapt it for your organization:

1. **Add your own skills** -- create a new folder in `skills/` with a `SKILL.md` (frontmatter `name` + `description`, matching the folder name). Optionally add companion markdown for templates, as in the official skill layout. Push updates with a vibe tool, `./skills/deploy.sh`, or a manual copy.
2. **Update existing skills** -- edit `SKILL.md` and the companion template files under `skills/<skill-name>/` to match your organization's naming conventions, PII policies, and quality rules
3. **Fork and serve via MCP** -- fork this repo, customize the skills, and point your MCP connection to your fork. Changes in GitHub are picked up automatically by Genie Code.
4. **Customize instructions** -- copy a template from `instructions/`, fill in placeholders for your team (pipeline names, routing, org/repo). Ask a vibe tool to adjust the copy if you want; leave the repo templates as templates.

---

## How to Get Help

Databricks support does not cover this content. For questions or bugs, please [open a GitHub issue](../../issues) and the team will help on a best-effort basis.

---

## License

&copy; 2026 Databricks, Inc. All rights reserved. The source in this repository is provided subject to the [Databricks License](https://databricks.com/db-license-source). All included or referenced third-party libraries are subject to the licenses set forth below.

| Library | Description | License | Source |
|---------|-------------|---------|--------|
| databricks-sdk | Databricks SDK for Python | Apache 2.0 | [PyPI](https://pypi.org/project/databricks-sdk/) |
| dbldatagen | Databricks Labs Data Generator | Apache 2.0 | [PyPI](https://pypi.org/project/dbldatagen/) |
