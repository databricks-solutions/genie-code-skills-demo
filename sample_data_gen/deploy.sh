#!/usr/bin/env bash
#
# Deploy the data generation notebook to a Databricks workspace and optionally
# run it as a one-time job. Reads configuration from deploy_config.yaml.
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
CONFIG_FILE="${SCRIPT_DIR}/deploy_config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE"
    echo "Copy deploy_config.example.yaml to deploy_config.yaml and fill in your values."
    exit 1
fi

if command -v yq &> /dev/null; then
    WORKSPACE_HOST=$(yq '.workspace_host' "$CONFIG_FILE")
    PROFILE=$(yq '.profile' "$CONFIG_FILE")
    CATALOG=$(yq '.catalog' "$CONFIG_FILE")
    SCHEMA=$(yq '.schema' "$CONFIG_FILE")
    VOLUME=$(yq '.volume' "$CONFIG_FILE")
else
    echo "yq not found. Set environment variables instead:"
    echo "  export WORKSPACE_HOST=... PROFILE=... CATALOG=... SCHEMA=... VOLUME=..."
    WORKSPACE_HOST="${WORKSPACE_HOST:?}"
    PROFILE="${PROFILE:?}"
    CATALOG="${CATALOG:?}"
    SCHEMA="${SCHEMA:?}"
    VOLUME="${VOLUME:-raw_data}"
fi

NOTEBOOK_SRC="${SCRIPT_DIR}/generate_financial_data.py"
WORKSPACE_PATH="${WORKSPACE_DEST:-/Workspace/Shared/genie-code-demo/generate_financial_data}"

echo "=== Deploying Data Generation Notebook ==="
echo "Workspace: ${WORKSPACE_HOST}"
echo "Profile:   ${PROFILE}"
echo "Target:    ${WORKSPACE_PATH}"
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
    "run_name": "generate-financial-data",
    "existing_cluster_id": "",
    "notebook_task": {
        "notebook_path": "${WORKSPACE_PATH}",
        "base_parameters": {
            "catalog": "${CATALOG}",
            "schema": "${SCHEMA}",
            "volume": "${VOLUME}"
        }
    }
}
ENDJSON
)

    RUN_ID=$(echo "$JOB_JSON" | databricks jobs submit --profile "$PROFILE" --json @-)
    echo "Submitted run: ${RUN_ID}"
    echo "Monitor at: ${WORKSPACE_HOST}/#job/runs"
fi
