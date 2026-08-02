#!/usr/bin/env bash
set -Eeuo pipefail

readonly DEFAULT_USER="rickycodes"
readonly DEFAULT_ORG="MetaMask"
readonly DEFAULT_START="2019-11-01"
readonly DEFAULT_END="2024-10-31"

USER_LOGIN="${1:-$DEFAULT_USER}"
ORG="${2:-$DEFAULT_ORG}"
START_DATE="${3:-$DEFAULT_START}"
END_DATE="${4:-$DEFAULT_END}"
OUTPUT_DIR="${5:-metamask-github-history}"

readonly PR_DIR="${OUTPUT_DIR}/prs"
readonly SEARCH_RESULTS="${OUTPUT_DIR}/search-results.json"
readonly SUMMARY_JSON="${OUTPUT_DIR}/pull-requests.json"
readonly REPORT="${OUTPUT_DIR}/report.md"
readonly ERROR_LOG="${OUTPUT_DIR}/errors.log"

require_command() {
    command -v "$1" >/dev/null 2>&1 || {
        printf 'Error: required command not found: %s\n' "$1" >&2
        exit 1
    }
}

log() {
    printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" >&2
}

require_command gh
require_command jq
require_command python3

if ! gh auth status >/dev/null 2>&1; then
    printf 'Error: GitHub CLI is not authenticated. Run: gh auth login\n' >&2
    exit 1
fi

mkdir -p "$PR_DIR"
: > "$ERROR_LOG"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

start_year="${START_DATE%%-*}"
end_year="${END_DATE%%-*}"

log "Searching PRs by ${USER_LOGIN} in ${ORG}"
log "Date range: ${START_DATE} through ${END_DATE}"

for ((year = start_year; year <= end_year; year++)); do
    year_start="${year}-01-01"
    year_end="${year}-12-31"

    (( year == start_year )) && year_start="$START_DATE"
    (( year == end_year )) && year_end="$END_DATE"

    output_file="${tmp_dir}/${year}.json"

    log "Searching ${year_start}..${year_end}"

    if ! gh search prs \
        --author "$USER_LOGIN" \
        --owner "$ORG" \
        --created "${year_start}..${year_end}" \
        --limit 1000 \
        --json number,title,url,state,repository,createdAt,updatedAt,closedAt,labels \
        > "$output_file" 2>>"$ERROR_LOG"
    then
        printf 'Search failed for %s..%s\n' "$year_start" "$year_end" >> "$ERROR_LOG"
        printf '[]\n' > "$output_file"
    fi
done

jq -s '
    add
    | unique_by(.url)
    | sort_by(.createdAt)
' "$tmp_dir"/*.json > "$SEARCH_RESULTS"

pr_count="$(jq 'length' "$SEARCH_RESULTS")"
log "Found ${pr_count} authored pull requests"

printf '[]\n' > "$SUMMARY_JSON"

index=0
while IFS= read -r search_pr; do
    index=$((index + 1))

    repo="$(jq -r '.repository.nameWithOwner' <<<"$search_pr")"
    number="$(jq -r '.number' <<<"$search_pr")"
    repo_slug="${repo//\//_}"
    detail_file="${PR_DIR}/${repo_slug}-${number}.json"
    endpoint="repos/${repo}/pulls/${number}"

    log "[${index}/${pr_count}] ${repo}#${number}"

    pr_file="${tmp_dir}/pr-${index}.json"
    if ! gh api "$endpoint" > "$pr_file" 2>>"$ERROR_LOG"; then
        printf 'Failed to retrieve PR: %s#%s\n' "$repo" "$number" >> "$ERROR_LOG"
        continue
    fi

    files_file="${tmp_dir}/files-${index}.json"
    commits_file="${tmp_dir}/commits-${index}.json"
    reviews_file="${tmp_dir}/reviews-${index}.json"
    comments_file="${tmp_dir}/comments-${index}.json"

    gh api --paginate --slurp "${endpoint}/files?per_page=100" 2>>"$ERROR_LOG" \
        | jq 'add // []' > "$files_file" || printf '[]\n' > "$files_file"
    gh api --paginate --slurp "${endpoint}/commits?per_page=100" 2>>"$ERROR_LOG" \
        | jq 'add // []' > "$commits_file" || printf '[]\n' > "$commits_file"
    gh api --paginate --slurp "${endpoint}/reviews?per_page=100" 2>>"$ERROR_LOG" \
        | jq 'add // []' > "$reviews_file" || printf '[]\n' > "$reviews_file"
    gh api --paginate --slurp "repos/${repo}/issues/${number}/comments?per_page=100" 2>>"$ERROR_LOG" \
        | jq 'add // []' > "$comments_file" || printf '[]\n' > "$comments_file"

    python3 normalize-github-pr.py \
        --pr "$pr_file" \
        --files "$files_file" \
        --commits "$commits_file" \
        --reviews "$reviews_file" \
        --comments "$comments_file" \
        --output "$detail_file"

    jq --slurpfile item "$detail_file" '. + $item' "$SUMMARY_JSON" > "${SUMMARY_JSON}.tmp"
    mv "${SUMMARY_JSON}.tmp" "$SUMMARY_JSON"
done < <(jq -c '.[]' "$SEARCH_RESULTS")

log "Generating résumé-focused Markdown report"

python3 generate-github-report.py \
    --input "$SUMMARY_JSON" \
    --user "$USER_LOGIN" \
    --org "$ORG" \
    --start-date "$START_DATE" \
    --end-date "$END_DATE" \
    --output "$REPORT"

log "Done"
printf '\nGenerated:\n'
printf '  %s\n' "$REPORT"
printf '  %s\n' "$SUMMARY_JSON"
printf '  %s\n' "$PR_DIR"
printf '  %s\n' "$ERROR_LOG"
