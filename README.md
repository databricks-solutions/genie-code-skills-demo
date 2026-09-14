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
| `skills/` | One folder per skill: `SKILL.md` plus companion template markdown (`table-governance`, `sdp-basics`, `pii-management`, `sentiment-analysis`; also served via MCP) |
| `AGENTS.md` | Auto-discovered enterprise standards -- Genie Code reads this automatically from the workspace directory tree |
| `instructions/` | Custom instruction templates (user-level and workspace-level) |
| `mcp/` | MCP connection setup: deploy script and config template |
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

Connect a GitHub MCP server that points to the same skills in this repo. Add custom instructions that tell Genie Code to fetch and apply them dynamically. The result is automatic compliance with organizational policies, maintained centrally in version control.

---

## Quick Start

### Prerequisites

- A Databricks workspace with Genie Code enabled
- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) installed and configured
- A GitHub account (for MCP setup)
- Python 3.9+ with `databricks-sdk` installed (for MCP deploy script)

### 1. Install Skills

Copy each skill **folder** from `skills/` to your Databricks workspace. Each skill is its own folder with a required `SKILL.md` plus companion template markdown (the layout from [Extend Genie Code with agent skills](https://docs.databricks.com/aws/en/genie-code/skills)):

```
Workspace/.assistant/skills/
  table-governance/
    SKILL.md
    governance-template.md
  sdp-basics/
    SKILL.md
    sql-templates.md
  pii-management/
    SKILL.md
    masking-templates.md
```

Skills can be installed at the workspace level (`Workspace/.assistant/skills/`) or user level (`/Users/{username}/.assistant/skills/`).

Once installed, Genie Code auto-loads a skill when your request matches its `description`. In chat, you can still force a skill with `@table-governance`, `@sdp-basics`, or `@pii-management` (`@` is skill invocation, not instruction syntax).

### 2. Set Up MCP (Optional)

Connect Genie Code to a GitHub MCP server to fetch the same skills dynamically -- no need to copy files into the workspace manually. The MCP connection points directly to the `skills/` folder in this repo (or your fork of it).

> **About the GitHub token:** the GitHub-hosted MCP server requires a token to authenticate, but because this repo is **public** the token needs **no scopes**. A classic PAT with **no scopes selected**, or a fine-grained PAT with **read-only `Contents` access to the public repo**, is sufficient. Do not grant `repo`, `read:org`, or other privileged scopes.

**a. Configure**

```bash
cd mcp/
cp mcp_config.example.json mcp_config.json
# Edit mcp_config.json with your GitHub org, repo, and secret scope details
```

**b. Deploy**

```bash
pip install databricks-sdk
python deploy_mcp.py
```

The script will:
1. Create a Databricks secret scope and store your GitHub PAT
2. Print the SQL to create the MCP connection

**c. Create the connection**

Copy the printed SQL and run it in a Databricks SQL Editor.

### 3. Add Instructions

The `instructions/` folder contains **templates** with placeholders. To create ready-to-use instruction files for your workspace:

1. Set up your local deployment folder (see `local_deployment/README.md`)
2. Choose your approach (**direct skills** or **MCP**) and scope (**user-level** or **workspace-level**)
3. Copy the matching ready-to-use file from `local_deployment/instructions_to_use/`:

| Scope | Direct Skills | MCP |
|-------|--------------|-----|
| User-level | `user_instructions_skills.md` | `user_instructions_mcp.md` |
| Workspace-level | `workspace_instructions_skills.md` | `workspace_instructions_mcp.md` |

4. Fill in any remaining placeholders (GitHub org/repo for MCP files)
5. Upload to your workspace:
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
│   ├── mcp_config.example.json             # MCP config template (points to skills/ folder)
│   └── deploy_mcp.py                       # MCP connection deploy script
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

1. **Add your own skills** -- create a new folder in `skills/` with a `SKILL.md` (frontmatter `name` + `description`, matching the folder name). Optionally add companion markdown for templates, as in the official skill layout.
2. **Update existing skills** -- edit `SKILL.md` and the companion template files under `skills/<skill-name>/` to match your organization's naming conventions, PII policies, and quality rules
3. **Fork and serve via MCP** -- fork this repo, customize the skills, and point your MCP connection to your fork. Changes in GitHub are picked up automatically by Genie Code.
4. **Customize instructions** -- edit the templates in `instructions/` to include your team's specific pipeline names, routing tables, and preferences

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
