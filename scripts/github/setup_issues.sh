#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

repo_arg=""
phase_filter=""
dry_run="false"

print_help() {
  cat <<'EOF'
Create GitHub issues from the Issues Catalog section in ROADMAP.md.

Usage:
  setup_issues.sh [--repo <owner/repo>] [--phase <phase-label>] [--dry-run]

Options:
  --repo <owner/repo>   Target GitHub repository. Defaults to GH_REPO or current gh repo.
  --phase <phase-label> Only create issues that contain the given phase label, for example phase-2.
  --dry-run             Print the issues that would be created without calling the GitHub API.
  -h, --help            Show this help message.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || die "Missing value for --repo"
      repo_arg="$2"
      shift 2
      ;;
    --phase)
      [[ $# -ge 2 ]] || die "Missing value for --phase"
      phase_filter="$2"
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
      die "Unknown argument: $1"
      ;;
  esac
done

require_cmd gh
ensure_gh_auth
ensure_roadmap_exists
repo="$(resolve_repo "${repo_arg}")"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

created_count=0
skipped_count=0

log "Preparing issues from ${ROADMAP_PATH}"

while IFS= read -r -d $'\x1e' record; do
  [[ -n "${record}" ]] || continue

  IFS=$'\x1f' read -r title labels milestone body <<< "${record}"

  if [[ -n "${phase_filter}" ]]; then
    case ",${labels}," in
      *",${phase_filter},"*) ;;
      *)
        continue
        ;;
    esac
  fi

  existing_number="$(find_issue_number "${repo}" "${title}")"
  if [[ -n "${existing_number}" ]]; then
    log "Skipping existing issue #${existing_number}: ${title}"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  if [[ "${dry_run}" == "true" ]]; then
    log "Dry run - would create issue: ${title}"
    log "  labels: ${labels}"
    log "  milestone: ${milestone}"
    created_count=$((created_count + 1))
    continue
  fi

  body_file="${tmp_dir}/issue-body-${created_count}.md"
  printf '%s' "${body}" > "${body_file}"

  label_args=()
  IFS=',' read -r -a label_names <<< "${labels}"
  for label_name in "${label_names[@]}"; do
    label_args+=( --label "${label_name}" )
  done

  gh issue create \
    --repo "${repo}" \
    --title "${title}" \
    --body-file "${body_file}" \
    "${label_args[@]}" \
    --milestone "${milestone}" >/dev/null

  log "Created issue: ${title}"
  created_count=$((created_count + 1))
done < <(parse_roadmap_issues "${ROADMAP_PATH}")

log "Issue bootstrap completed. Created: ${created_count}. Skipped: ${skipped_count}."
