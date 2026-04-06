#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

repo_arg=""
phase_arg=""
dry_run="false"

print_help() {
  cat <<'EOF'
Bootstrap labels, milestones, and issues for the GitHub repository.

Usage:
  setup_all.sh [--repo <owner/repo>] [--phase <phase-label>] [--dry-run]

Options:
  --repo <owner/repo>   Target GitHub repository. Defaults to GH_REPO or current gh repo.
  --phase <phase-label> Limit issue creation to one phase label. Labels and milestones are still synced.
  --dry-run             Print intended issue creation without creating issues.
  -h, --help            Show this help message.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || { echo "Missing value for --repo" >&2; exit 1; }
      repo_arg="$2"
      shift 2
      ;;
    --phase)
      [[ $# -ge 2 ]] || { echo "Missing value for --phase" >&2; exit 1; }
      phase_arg="$2"
      shift 2
      ;;
    --dry-run)
      dry_run="true"
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

label_cmd=( "${SCRIPT_DIR}/setup_labels.sh" )
milestone_cmd=( "${SCRIPT_DIR}/setup_milestones.sh" )
issue_cmd=( "${SCRIPT_DIR}/setup_issues.sh" )

if [[ -n "${repo_arg}" ]]; then
  label_cmd+=( --repo "${repo_arg}" )
  milestone_cmd+=( --repo "${repo_arg}" )
  issue_cmd+=( --repo "${repo_arg}" )
fi

if [[ -n "${phase_arg}" ]]; then
  issue_cmd+=( --phase "${phase_arg}" )
fi

if [[ "${dry_run}" == "true" ]]; then
  issue_cmd+=( --dry-run )
fi

"${label_cmd[@]}"
"${milestone_cmd[@]}"
"${issue_cmd[@]}"
