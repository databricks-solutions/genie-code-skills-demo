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

Genie Code supports **skills** (task-specific instructions following the open [Agent Skills](https://agentskills.io/) standard) and **MCP** ([Model Context Protocol](https://modelcontextprotocol.io/)) connections that fetch enterprise standards from external sources like GitHub.

---

## Demo Coverage

This repo provides example skills, instructions, and tooling organized by domain. Each phase adds a new area of coverage.

| Phase | Date | Domain | What's Included |
|-------|------|--------|-----------------|
| **Phase 1** | April 2026 | Data Engineering | SDP pipeline skills, PII management, table governance, MCP-based standards enforcement, sample financial data generation |
| Planned | -- | DSML, Dashboards, Governance | Additional skill domains and MCP integrations |

---

## What This Repo Contains

| Folder | Contents |
|--------|----------|
| `skills/data_eng/` | Skills for SDP pipelines, PII management, and table/column governance |
| `instructions/` | Custom instruction templates (user-level and workspace-level) |
| `mcp/` | MCP connection setup: deploy script and config template |
| `sample_data_gen/` | Synthetic financial data generation notebook (uses `dbldatagen`) |
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

Copy the skill files to your Databricks workspace:

```
Workspace/
  .assistant/
    skills/
      table-governance/
        SKILL.md          # paste content from skills/data_eng/table-governance.md
      sdp-basics/
        SKILL.md          # paste content from skills/data_eng/sdp-basics.md
      pii-management/
        SKILL.md          # paste content from skills/data_eng/pii-management.md
```

Skills can be installed at the workspace level (`Workspace/.assistant/skills/`) or user level (`/Users/{username}/.assistant/skills/`).

Once installed, Genie Code picks them up automatically. You can also invoke them explicitly with `@table-governance`, `@sdp-basics`, or `@pii-management`.

### 2. Set Up MCP (Optional)

Connect Genie Code to a GitHub MCP server to fetch the same skills dynamically -- no need to copy files into the workspace manually. The MCP connection points directly to the `skills/data_eng/` folder in this repo (or your fork of it).

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

Choose user-level, workspace-level, or both:

- **User-level**: Copy `instructions/.assistant_instructions.md` to `/Users/{username}/.assistant_instructions.md` in your workspace
- **Workspace-level**: Copy `instructions/.assistant_workspace_instructions.md` to `Workspace/.assistant_workspace_instructions.md`

Each template contains two options -- choose one based on your setup:
- **Option A**: Reference skills directly (if you uploaded skills to the workspace)
- **Option B**: Fetch skills via MCP (if you set up a GitHub MCP connection)

Workspace instructions take priority over user instructions when both are present.

---

## Try It Yourself -- Sample Data

Generate synthetic financial data to test the skills end-to-end. The data generation notebook uses [`dbldatagen`](https://github.com/databrickslabs/dbldatagen) (Databricks Labs Data Generator) for Spark-native synthetic data generation.

### Option A: Deploy with DAB (Recommended)

Set up a local deployment folder with your workspace-specific config:

```bash
# The local_deployment/ folder is gitignored -- create your own config
# See local_deployment/README.md for full instructions and examples
cd local_deployment/

# Deploy and run
databricks bundle deploy --profile <your-cli-profile>
databricks bundle run generate_financial_data --profile <your-cli-profile>
```

### Option B: Run Interactively

Upload the notebook to your workspace manually and run it interactively -- set the `catalog`, `schema`, and `volume` widget values when prompted.

### Build a Pipeline

With the sample data in your volume, use Genie Code:

> "Create an SDP pipeline that reads the financial CSV files from `/Volumes/{catalog}/{schema}/raw_data/` and builds a bronze-silver-gold medallion architecture."

Genie Code will apply the skills and standards automatically.

---

## Project Structure

```
genie-code-skills-demo/
├── .cursor/rules/                          # Cursor IDE rules
│   ├── public-repo-compliance.md
│   ├── coding-standards.md
│   └── branch-conventions.md
├── skills/
│   └── data_eng/                           # Data engineering skills (also served via MCP)
│       ├── table-governance.md             # Table/column documentation, UC tags, PII labeling
│       ├── sdp-basics.md                   # SDP naming, audit columns, TBLPROPERTIES
│       └── pii-management.md               # PII detection and labelling
├── instructions/
│   ├── .assistant_instructions.md          # User-level instructions template
│   └── .assistant_workspace_instructions.md # Workspace-level instructions template
├── mcp/
│   ├── mcp_config.example.json             # MCP config template (points to skills/ folder)
│   └── deploy_mcp.py                       # MCP connection deploy script
├── sample_data_gen/
│   ├── generate_financial_data.py          # Databricks notebook (dbldatagen, parameterized)
│   ├── deploy_config.example.yaml          # Deploy config template (placeholders)
│   └── deploy.sh                           # Deploy script (reads local config)
├── local_deployment/                       # GITIGNORED (except README)
│   └── README.md                           # How to set up your own local deployment
├── README.md
├── LICENSE.md
├── NOTICE.md
├── SECURITY.md
├── CODEOWNERS.txt
└── .gitignore
```

---

## Customization

This repo is a starting point. To adapt it for your organization:

1. **Add your own skills** -- create new `.md` files in `skills/data_eng/` or add new domain folders (e.g., `skills/dsml/`, `skills/dashboards/`)
2. **Update existing skills** -- edit the skill files in `skills/data_eng/` to match your organization's naming conventions, PII policies, and quality rules
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
