#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ROADMAP_PATH="${REPO_ROOT}/ROADMAP.md"

log() {
  printf '[INFO] %s\n' "$*"
}

warn() {
  printf '[WARN] %s\n' "$*" >&2
}

die() {
  printf '[ERROR] %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

ensure_gh_auth() {
  gh auth status >/dev/null 2>&1 || die "GitHub CLI is not authenticated. Run: gh auth login"
}

jq_quote() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  printf '"%s"' "${value}"
}

resolve_repo() {
  local explicit_repo="${1:-}"

  if [[ -n "${explicit_repo}" ]]; then
    printf '%s\n' "${explicit_repo}"
    return 0
  fi

  if [[ -n "${GH_REPO:-}" ]]; then
    printf '%s\n' "${GH_REPO}"
    return 0
  fi

  gh repo view --json nameWithOwner --jq '.nameWithOwner'
}

find_milestone_number() {
  local repo="$1"
  local title="$2"
  local title_json

  title_json="$(jq_quote "${title}")"

  gh api "repos/${repo}/milestones?state=all&per_page=100" \
    --jq ".[] | select(.title == ${title_json}) | .number" 2>/dev/null || true
}

find_issue_number() {
  local repo="$1"
  local title="$2"
  local title_json

  title_json="$(jq_quote "${title}")"

  gh issue list \
    --repo "${repo}" \
    --state all \
    --limit 500 \
    --json number,title \
    --jq ".[] | select(.title == ${title_json}) | .number" 2>/dev/null || true
}

ensure_roadmap_exists() {
  [[ -f "${ROADMAP_PATH}" ]] || die "ROADMAP.md not found at ${ROADMAP_PATH}"
}

parse_roadmap_issues() {
  local roadmap_file="${1:-${ROADMAP_PATH}}"

  awk '
    function flush_issue() {
      if (title != "" && labels != "" && milestone != "" && body != "") {
        print "<<<ISSUE_START>>>"
        print "TITLE: " title
        print "LABELS: " labels
        print "MILESTONE: " milestone
        print "BODY_START"
        printf "%s", body
        if (body !~ /\n$/) {
          print ""
        }
        print "BODY_END"
        print "<<<ISSUE_END>>>"
      }
      title = ""
      labels = ""
      milestone = ""
      body = ""
      in_body = 0
    }

    /^#### Issue: `/ {
      flush_issue()
      title = $0
      sub(/^#### Issue: `/, "", title)
      sub(/`$/, "", title)
      next
    }

    /^\*\*Labels:\*\*: / {
      labels = $0
      sub(/^\*\*Labels:\*\*: /, "", labels)
      gsub(/`/, "", labels)
      gsub(/, /, ",", labels)
      next
    }

    /^\*\*Milestone:\*\*: / {
      milestone = $0
      sub(/^\*\*Milestone:\*\*: /, "", milestone)
      gsub(/`/, "", milestone)
      next
    }

    /^```md$/ && title != "" {
      in_body = 1
      body = ""
      next
    }

    /^```$/ && in_body == 1 {
      in_body = 0
      next
    }

    in_body == 1 {
      body = body $0 "\n"
      next
    }

    END {
      flush_issue()
    }
  ' "${roadmap_file}"
}

usage_repo_flag() {
  cat <<'EOF'
Usage:
  --repo <owner/repo>   Target GitHub repository. Defaults to GH_REPO or current gh repo.
EOF
}
