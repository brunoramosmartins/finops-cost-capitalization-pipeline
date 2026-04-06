#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

repo_arg=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || die "Missing value for --repo"
      repo_arg="$2"
      shift 2
      ;;
    -h|--help)
      usage_repo_flag
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

require_cmd gh
ensure_gh_auth
repo="$(resolve_repo "${repo_arg}")"

milestones=(
  "Phase 1 - Foundation and Synthetic Data Generation|Bootstrap the repository, agent workflow, synthetic billing generator, and raw lake layout."
  "Phase 2 - Analytics Engineering Pipeline|Build DuckDB plus dbt Bronze, Silver, and Gold layers with accounting classification logic."
  "Phase 3 - Quality, Orchestration and CI/CD|Add data quality controls, Dagster orchestration, observability, and GitHub automation."
  "Phase 4 - Gold Product and ML Handoff|Publish versioned Gold exports, define the downstream contract, and prepare the ML handoff."
)

log "Syncing milestones to ${repo}"

for milestone in "${milestones[@]}"; do
  IFS='|' read -r title description <<< "${milestone}"
  number="$(find_milestone_number "${repo}" "${title}")"

  if [[ -n "${number}" ]]; then
    gh api "repos/${repo}/milestones/${number}" \
      --method PATCH \
      -f title="${title}" \
      -f description="${description}" \
      -f state="open" >/dev/null
    log "Updated milestone: ${title}"
  else
    gh api "repos/${repo}/milestones" \
      --method POST \
      -f title="${title}" \
      -f description="${description}" \
      -f state="open" >/dev/null
    log "Created milestone: ${title}"
  fi
done

log "Milestone sync completed successfully."
