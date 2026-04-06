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

labels=(
  "bug|D73A4A|Bug report or regression"
  "feature|0E8A16|New capability or product behavior"
  "data|1D76DB|Data modeling, generation, or contracts"
  "quality|BFDADC|Data quality, validation, or observability"
  "orchestration|5319E7|Scheduling, Dagster, or workflow automation"
  "infra|6F42C1|Repository, platform, or developer tooling"
  "docs|0075CA|Documentation or developer guidance"
  "test|FBCA04|Automated tests or validation coverage"
  "release|C2E0C6|Release management and publication"
  "phase-1|C5DEF5|Phase 1 - Foundation and Synthetic Data Generation"
  "phase-2|C5DEF5|Phase 2 - Analytics Engineering Pipeline"
  "phase-3|C5DEF5|Phase 3 - Quality, Orchestration and CI/CD"
  "phase-4|C5DEF5|Phase 4 - Gold Product and ML Handoff"
  "priority:high|B60205|High-priority work item"
  "priority:medium|D4C5F9|Medium-priority work item"
  "blocked|000000|Work blocked by an external dependency or unresolved decision"
  "needs-review|F9D0C4|Ready for technical review"
)

log "Syncing labels to ${repo}"

for label in "${labels[@]}"; do
  IFS='|' read -r name color description <<< "${label}"
  gh label create "${name}" \
    --repo "${repo}" \
    --color "${color}" \
    --description "${description}" \
    --force >/dev/null
  log "Upserted label: ${name}"
done

log "Label sync completed successfully."
