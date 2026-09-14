#!/usr/bin/env bash
#
# Deploy the skill folders in this directory to a Databricks workspace so
# Genie Code can load them. Each skill is a folder with SKILL.md plus optional
# companion markdown (templates).
#
# Prerequisites:
#   - Databricks CLI installed and authenticated
#
# Usage:
#   ./deploy.sh                         # user-level skills for the CLI identity
#   ./deploy.sh --workspace             # workspace-level skills (admin)
#   ./deploy.sh --profile <cli-profile> # use a named ~/.databrickscfg profile
#   ./deploy.sh --user <email>          # override the user-level target path
#
# A vibe tool (Genie Code, Cursor, or similar) can also deploy these folders
# for you. Manual copy in the workspace UI works too.
#
# See: https://docs.databricks.com/aws/en/genie-code/skills

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCOPE="user"
PROFILE="${DATABRICKS_PROFILE:-}"
USER_NAME=""

usage() {
  sed -n '3,18p' "$0" | sed 's/^# \?//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) SCOPE="workspace"; shift ;;
    --profile)
      PROFILE="${2:?--profile requires a profile name}"
      shift 2
      ;;
    --user)
      USER_NAME="${2:?--user requires a workspace username (email)}"
      shift 2
      ;;
    -h|--help) usage 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage 1
      ;;
  esac
done

PROFILE_ARGS=()
if [[ -n "$PROFILE" ]]; then
  PROFILE_ARGS=(--profile "$PROFILE")
fi

cli() {
  databricks "${PROFILE_ARGS[@]}" "$@"
}

if [[ "$SCOPE" == "workspace" ]]; then
  TARGET="/Workspace/.assistant/skills"
else
  if [[ -z "$USER_NAME" ]]; then
    ME_JSON="$(cli current-user me -o json)"
    USER_NAME="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["userName"])' <<<"$ME_JSON")"
  fi
  TARGET="/Workspace/Users/${USER_NAME}/.assistant/skills"
fi

echo "=== Deploying Genie Code skills ==="
echo "Source:  ${SCRIPT_DIR}"
echo "Target:  ${TARGET}"
if [[ -n "$PROFILE" ]]; then
  echo "Profile: ${PROFILE}"
fi
echo ""

cli workspace mkdirs "$TARGET"

imported=0
for skill_dir in "$SCRIPT_DIR"/*/ ; do
  [[ -f "${skill_dir}SKILL.md" ]] || continue
  name="$(basename "$skill_dir")"
  dest="${TARGET}/${name}"
  echo "Importing ${name}/"
  cli workspace mkdirs "$dest"
  cli workspace import-dir "$skill_dir" "$dest" --overwrite
  imported=$((imported + 1))
done

if [[ "$imported" -eq 0 ]]; then
  echo "ERROR: no skill folders with SKILL.md found in ${SCRIPT_DIR}" >&2
  exit 1
fi

echo ""
echo "Imported ${imported} skill folder(s) to ${TARGET}:"
cli workspace list "$TARGET"
echo ""
echo "Start a new Genie Code chat so the skills load. Force one in chat with"
echo "@table-governance, @sdp-basics, @pii-management, or @sentiment-analysis."
