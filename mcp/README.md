# MCP: fetch skills from this public GitHub repo

Genie Code fetches `skills/` through a Unity Catalog HTTP MCP connection to
`https://api.githubcopilot.com/mcp` using a **no-scope GitHub PAT** stored in a
Databricks secret.

Use a classic PAT with **no scopes**, created by a GitHub user who is **not**
a member of an org that has an IP allowlist (including this repo's org if it
has one). Do **not** grant `repo` / `read:org`, and do **not** use managed
GitHub OAuth (`OAUTH_PROVIDER_GITHUB_MCP`). Org-member tokens are subject to
that allowlist when Copilot MCP calls `api.github.com`, and fail with:

> GitHub MCP is blocked by IP allowlist.

## Create the connection

1. Copy the config template and fill in owner/repo/secret scope/connection name:

```bash
cp mcp/mcp_config.example.json mcp/mcp_config.json
```

2. Store the PAT and print the `CREATE CONNECTION` SQL (Databricks CLI must be
   authenticated):

```bash
pip install databricks-sdk
python mcp/deploy_mcp.py --config mcp/mcp_config.json
```

3. Run the printed SQL in a Databricks SQL editor so `secret()` resolves.
4. Genie Code settings → MCP Servers → add the connection. Enable
   `get_file_contents` and `search_code`.
5. Use the MCP instruction templates pointed at this repo (or your fork).
6. Start a **new** Genie Code chat.
