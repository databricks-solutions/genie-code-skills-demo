"""
Deploy a GitHub MCP connection to a Databricks workspace.

Reads configuration from a local JSON file (mcp_config.json) and:
  1. Creates a Databricks secret scope (if it doesn't exist)
  2. Prompts for a GitHub PAT and stores it in the scope
  3. Prints the SQL to create the GitHub MCP connection
  4. Prints verification SQL to confirm the connection

This public repo needs a *no-scope* PAT from a GitHub user who is **not** a
member of an IP-allowlisted org (org-member tokens fail Copilot MCP with
"GitHub MCP is blocked by IP allowlist"). Do not use managed GitHub OAuth
(`OAUTH_PROVIDER_GITHUB_MCP`) or a PAT with `repo` / `read:org`.

Usage:
    python deploy_mcp.py                        # uses ./mcp_config.json
    python deploy_mcp.py --config path/to.json  # custom config path
    python deploy_mcp.py --skip-secret          # skip secret scope setup
"""

import argparse
import getpass
import json
import sys
from pathlib import Path

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.errors import ResourceAlreadyExists
except ImportError:
    print(
        "ERROR: databricks-sdk is required. Install with:\n"
        "  pip install databricks-sdk"
    )
    sys.exit(1)


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        print(f"ERROR: Config file not found: {path}")
        print(
            "Copy mcp_config.example.json to mcp_config.json and fill in your values."
        )
        sys.exit(1)

    with open(path) as f:
        config = json.load(f)

    required = [
        "github_owner",
        "github_repo",
        "branch",
        "base_path",
        "secret_scope",
        "secret_key",
        "connection_name",
    ]
    missing = [
        k for k in required if not config.get(k) or str(config[k]).startswith("<")
    ]
    if missing:
        print(f"ERROR: These config values are missing or still have placeholders: {missing}")
        sys.exit(1)

    return config


def setup_secret_scope(w: WorkspaceClient, config: dict) -> None:
    scope = config["secret_scope"]
    key = config["secret_key"]

    print("\n--- Secret Scope Setup ---")
    print(f"Scope: {scope}")
    print(f"Key:   {key}")

    try:
        w.secrets.create_scope(scope=scope)
        print(f"Created secret scope: {scope}")
    except ResourceAlreadyExists:
        print(f"Secret scope already exists: {scope}")

    print(
        "\nNOTE: This repo is public. Use a no-scope PAT from a GitHub user who "
        "is not a member of an IP-allowlisted org. Do not grant repo / read:org."
    )
    pat = getpass.getpass("Enter your GitHub PAT (no scopes required): ")
    if not pat.strip():
        print("ERROR: PAT cannot be empty.")
        sys.exit(1)

    w.secrets.put_secret(scope=scope, key=key, string_value=pat.strip())
    print(f"Stored PAT in {scope}/{key}")


def print_connection_sql(config: dict) -> None:
    scope = config["secret_scope"]
    key = config["secret_key"]
    conn_name = config["connection_name"]
    owner = config["github_owner"]
    repo = config["github_repo"]

    create_sql = f"""\
-- Run this in a SQL context so that secret() resolves: the Databricks SQL
-- Editor, or the SQL Statement Execution API against a SQL warehouse.
-- Plain REST/CLI catalog APIs and DAB do NOT resolve secret().
-- Requires CREATE CONNECTION privilege on the metastore.

CREATE CONNECTION IF NOT EXISTS `{conn_name}`
TYPE HTTP
OPTIONS (
  host = 'https://api.githubcopilot.com',
  base_path = '/mcp',
  bearer_token = secret('{scope}', '{key}'),
  is_mcp_connection = 'true'
)
COMMENT 'GitHub MCP connection for {owner}/{repo} - Genie Code skills and standards';"""

    verify_sql = f"""\
-- Verify the connection was created
DESCRIBE CONNECTION `{conn_name}`;"""

    print("\n--- SQL: Create MCP Connection ---\n")
    print(create_sql)
    print("\n--- SQL: Verify Connection ---\n")
    print(verify_sql)
    print(
        "\nCopy and run the CREATE CONNECTION SQL in a Databricks SQL Editor."
        "\nThen run DESCRIBE CONNECTION to verify it was created successfully."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Deploy a GitHub MCP connection to Databricks"
    )
    parser.add_argument(
        "--config",
        default="mcp_config.json",
        help="Path to MCP config JSON (default: mcp_config.json)",
    )
    parser.add_argument(
        "--skip-secret",
        action="store_true",
        help="Skip secret scope setup (if PAT is already stored)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    print("=== Databricks GitHub MCP Connection Deployment ===")
    print(f"GitHub: {config['github_owner']}/{config['github_repo']}")
    print(f"Branch: {config['branch']}")
    print(f"Connection: {config['connection_name']}")

    if not args.skip_secret:
        w = WorkspaceClient()
        setup_secret_scope(w, config)
    else:
        print("\nSkipping secret scope setup (--skip-secret).")

    print_connection_sql(config)


if __name__ == "__main__":
    main()
