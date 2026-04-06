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
parsed_count=0
current_title=""
current_labels=""
current_milestone=""
current_body=""
in_body="false"

log "Preparing issues from ${ROADMAP_PATH}"

create_issue_from_buffer() {
  [[ -n "${current_title}" ]] || return 0

  if [[ -n "${phase_filter}" ]]; then
    case ",${current_labels}," in
      *",${phase_filter},"*) ;;
      *)
        return 0
        ;;
    esac
  fi

  existing_number="$(find_issue_number "${repo}" "${current_title}")"
  if [[ -n "${existing_number}" ]]; then
    log "Skipping existing issue #${existing_number}: ${current_title}"
    skipped_count=$((skipped_count + 1))
    return 0
  fi

  if [[ "${dry_run}" == "true" ]]; then
    log "Dry run - would create issue: ${current_title}"
    log "  labels: ${current_labels}"
    log "  milestone: ${current_milestone}"
    created_count=$((created_count + 1))
    return 0
  fi

  body_file="${tmp_dir}/issue-body-${created_count}.md"
  printf '%s' "${current_body}" > "${body_file}"

  label_args=()
  IFS=',' read -r -a label_names <<< "${current_labels}"
  for label_name in "${label_names[@]}"; do
    label_args+=( --label "${label_name}" )
  done

  gh issue create \
    --repo "${repo}" \
    --title "${current_title}" \
    --body-file "${body_file}" \
    "${label_args[@]}" \
    --milestone "${current_milestone}" >/dev/null

  log "Created issue: ${current_title}"
  created_count=$((created_count + 1))
}

while IFS= read -r line || [[ -n "${line}" ]]; do
  case "${line}" in
    "<<<ISSUE_START>>>")
      current_title=""
      current_labels=""
      current_milestone=""
      current_body=""
      in_body="false"
      ;;
    "TITLE: "*)
      current_title="${line#TITLE: }"
      ;;
    "LABELS: "*)
      current_labels="${line#LABELS: }"
      ;;
    "MILESTONE: "*)
      current_milestone="${line#MILESTONE: }"
      ;;
    "BODY_START")
      in_body="true"
      ;;
    "BODY_END")
      in_body="false"
      ;;
    "<<<ISSUE_END>>>")
      parsed_count=$((parsed_count + 1))
      create_issue_from_buffer
      current_title=""
      current_labels=""
      current_milestone=""
      current_body=""
      in_body="false"
      ;;
    *)
      if [[ "${in_body}" == "true" ]]; then
        current_body+="${line}"$'\n'
      fi
      ;;
  esac
done < <(parse_roadmap_issues "${ROADMAP_PATH}")

if [[ "${parsed_count}" -eq 0 ]]; then
  die "No issues were parsed from ROADMAP.md. Check the issue catalog format."
fi

log "Issue bootstrap completed. Created: ${created_count}. Skipped: ${skipped_count}."
