#!/usr/bin/env bash
#
# Deploy the Bakehouse Marketplace install notebook to a Databricks workspace
# and optionally run it as a one-time job. Reads configuration from the local
# (gitignored) bakehouse_config.yaml under local_deployment/.
#
# Prerequisites:
#   - Databricks CLI installed and configured with a profile
#   - yq (https://github.com/mikefarah/yq) for YAML parsing, or set env vars
#
# Usage:
#   ./deploy.sh              # upload only
#   ./deploy.sh --run        # upload and run

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${REPO_ROOT}/local_deployment/bakehouse_config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE"
    echo "Copy marketplace_data/bakehouse_config.example.yaml to"
    echo "local_deployment/bakehouse_config.yaml and fill in your values."
    exit 1
fi

if command -v yq &> /dev/null; then
    WORKSPACE_HOST=$(yq '.workspace_host' "$CONFIG_FILE")
    PROFILE=$(yq '.profile' "$CONFIG_FILE")
    CANDIDATE_SOURCE_CATALOGS=$(yq '.candidate_source_catalogs' "$CONFIG_FILE")
    SCRATCH_CATALOG=$(yq '.scratch_catalog_name' "$CONFIG_FILE")
    LISTING_NAME=$(yq '.listing_name' "$CONFIG_FILE")
    SHARE_PROVIDER_NAME=$(yq '.share_provider_name' "$CONFIG_FILE")
    DEMO_CATALOG=$(yq '.demo_catalog' "$CONFIG_FILE")
    DEMO_SCHEMA=$(yq '.demo_schema' "$CONFIG_FILE")
else
    echo "yq not found. Set environment variables instead:"
    echo "  export WORKSPACE_HOST=... PROFILE=... SCRATCH_CATALOG=... DEMO_CATALOG=... DEMO_SCHEMA=..."
    WORKSPACE_HOST="${WORKSPACE_HOST:?}"
    PROFILE="${PROFILE:?}"
    CANDIDATE_SOURCE_CATALOGS="${CANDIDATE_SOURCE_CATALOGS:-bakehouse}"
    SCRATCH_CATALOG="${SCRATCH_CATALOG:?}"
    LISTING_NAME="${LISTING_NAME:-AI/BI Bakehouse}"
    SHARE_PROVIDER_NAME="${SHARE_PROVIDER_NAME:-databricks}"
    DEMO_CATALOG="${DEMO_CATALOG:?}"
    DEMO_SCHEMA="${DEMO_SCHEMA:-bakehouse}"
fi

NOTEBOOK_SRC="${SCRIPT_DIR}/install_bakehouse.py"
WORKSPACE_PATH="${WORKSPACE_DEST:-/Workspace/Shared/genie-code-demo/install_bakehouse}"

echo "=== Deploying Bakehouse Install Notebook ==="
echo "Workspace:       ${WORKSPACE_HOST}"
echo "Profile:         ${PROFILE}"
echo "Target:          ${WORKSPACE_PATH}"
echo "Scratch catalog: ${SCRATCH_CATALOG}"
echo "Mirror target:   ${DEMO_CATALOG}.${DEMO_SCHEMA}"
echo ""

databricks workspace import \
    --profile "$PROFILE" \
    --format SOURCE \
    --language PYTHON \
    --overwrite \
    "$WORKSPACE_PATH" \
    "$NOTEBOOK_SRC"

echo "Notebook uploaded to ${WORKSPACE_PATH}"

if [[ "${1:-}" == "--run" ]]; then
    echo ""
    echo "=== Running notebook as one-time job ==="

    JOB_JSON=$(cat <<ENDJSON
{
    "run_name": "install-bakehouse",
    "existing_cluster_id": "",
    "notebook_task": {
        "notebook_path": "${WORKSPACE_PATH}",
        "base_parameters": {
            "candidate_source_catalogs": "${CANDIDATE_SOURCE_CATALOGS}",
            "scratch_catalog_name": "${SCRATCH_CATALOG}",
            "listing_name": "${LISTING_NAME}",
            "share_provider_name": "${SHARE_PROVIDER_NAME}",
            "demo_catalog": "${DEMO_CATALOG}",
            "demo_schema": "${DEMO_SCHEMA}"
        }
    }
}
ENDJSON
)

    RUN_ID=$(echo "$JOB_JSON" | databricks jobs submit --profile "$PROFILE" --json @-)
    echo "Submitted run: ${RUN_ID}"
    echo "Monitor at: ${WORKSPACE_HOST}/#job/runs"
fi
