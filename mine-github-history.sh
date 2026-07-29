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

    jq -n \
        --argfile pr "$pr_file" \
        --argfile files "$files_file" \
        --argfile commits "$commits_file" \
        --argfile reviews "$reviews_file" \
        --argfile comments "$comments_file" \
        '
        def corpus:
            (($pr.title // "") + " " + ($pr.body // "") + " " + ($files | map(.filename) | join(" ")));
        def matches($pattern): corpus | test($pattern; "i");
        {
            repository: $pr.base.repo.full_name,
            number: $pr.number,
            title: $pr.title,
            url: $pr.html_url,
            state: $pr.state,
            draft: ($pr.draft // false),
            merged: ($pr.merged_at != null),
            created_at: $pr.created_at,
            updated_at: $pr.updated_at,
            closed_at: $pr.closed_at,
            merged_at: $pr.merged_at,
            body: ($pr.body // ""),
            labels: [$pr.labels[].name],
            base_branch: $pr.base.ref,
            head_branch: $pr.head.ref,
            additions: ($pr.additions // 0),
            deletions: ($pr.deletions // 0),
            changed_files: ($pr.changed_files // 0),
            commit_count: ($commits | length),
            review_count: ($reviews | length),
            comment_count: ($comments | length),
            approving_reviewers: ([$reviews[] | select(.state == "APPROVED") | .user.login] | unique),
            files: [$files[] | {filename, status, additions, deletions, changes}],
            commits: [$commits[] | {sha, message: (.commit.message | split("\n")[0]), authored_at: .commit.author.date, author: (.author.login // .commit.author.name // "unknown")}],
            categories: {
                ci_cd: matches("github.?actions|circleci|workflow|pipeline|continuous integration|ci/|\\.github/"),
                release_engineering: matches("release|publish|publishing|npm|version|changelog|artifact|slack"),
                testing: matches("test|spec|jest|selenium|fixture|mock|coverage|regression|e2e|integration"),
                security: matches("security|encrypt|wallet|password|authentication|secret recovery|srp|keyring|vault"),
                reliability: matches("fix|bug|crash|failure|error|corrupt|restore|recovery|stability|reliability"),
                mobile: matches("android|ios|mobile|react.native|deeplink|biometric"),
                browser: matches("browser|extension|firefox|chrome|webview|dapp"),
                developer_tooling: matches("tool|script|lint|build|workflow|action|automation|developer|cli"),
                performance: matches("performance|optimi[sz]|cache|latency|speed|memory"),
                documentation: matches("docs|documentation|readme|guide|instructions")
            }
        }
        ' > "$detail_file"

    jq --slurpfile item "$detail_file" '. + $item' "$SUMMARY_JSON" > "${SUMMARY_JSON}.tmp"
    mv "${SUMMARY_JSON}.tmp" "$SUMMARY_JSON"
done < <(jq -c '.[]' "$SEARCH_RESULTS")

log "Generating résumé-focused Markdown report"

jq -r \
    --arg user "$USER_LOGIN" \
    --arg org "$ORG" \
    --arg start_date "$START_DATE" \
    --arg end_date "$END_DATE" \
    '
    def merged_prs: [.[] | select(.merged)];
    def category_count($name): [.[] | select(.categories[$name])] | length;
    def pr_line:
        "- [\(.repository)#\(.number): \(.title)](\(.url)) — " +
        (if .merged then "merged \(.merged_at[0:10])" else .state end) +
        "; +\(.additions)/-\(.deletions), \(.changed_files) files";
    def section($title; $items):
        "## " + $title + "\n\n" +
        (if ($items | length) == 0 then "_No matching pull requests._" else ($items | sort_by(.merged_at // .created_at) | reverse | map(pr_line) | join("\n")) end) + "\n";
    [
        "# GitHub career-history report",
        "",
        "**User:** @" + $user,
        "**Organization:** " + $org,
        "**Period:** " + $start_date + " through " + $end_date,
        "",
        "## Headline metrics",
        "",
        "- Authored pull requests: **\(length)**",
        "- Merged pull requests: **\(merged_prs | length)**",
        "- Repositories touched: **\([.[].repository] | unique | length)**",
        "- Changed files: **\([.[].changed_files] | add // 0)**",
        "- Additions: **\([.[].additions] | add // 0)**",
        "- Deletions: **\([.[].deletions] | add // 0)**",
        "",
        "## Category counts",
        "",
        "- CI/CD: **\(category_count("ci_cd"))**",
        "- Release engineering: **\(category_count("release_engineering"))**",
        "- Testing and validation: **\(category_count("testing"))**",
        "- Security-sensitive work: **\(category_count("security"))**",
        "- Reliability and defect fixes: **\(category_count("reliability"))**",
        "- Mobile: **\(category_count("mobile"))**",
        "- Browser and extension: **\(category_count("browser"))**",
        "- Developer tooling: **\(category_count("developer_tooling"))**",
        "- Performance: **\(category_count("performance"))**",
        "",
        "## Repository summary",
        "",
        (group_by(.repository) | sort_by(-length) | map("- **\(.[0].repository):** \(length) authored; \([.[] | select(.merged)] | length) merged") | join("\n")),
        "",
        section("CI/CD"; [.[] | select(.categories.ci_cd)]),
        section("Release engineering"; [.[] | select(.categories.release_engineering)]),
        section("Testing and validation"; [.[] | select(.categories.testing)]),
        section("Security-sensitive work"; [.[] | select(.categories.security)]),
        section("Reliability and defect fixes"; [.[] | select(.categories.reliability)]),
        section("Mobile engineering"; [.[] | select(.categories.mobile)]),
        section("Browser and extension work"; [.[] | select(.categories.browser)]),
        section("Developer tooling"; [.[] | select(.categories.developer_tooling)]),
        section("Performance"; [.[] | select(.categories.performance)]),
        "## Largest merged contributions",
        "",
        ([.[] | select(.merged)] | sort_by(.additions + .deletions) | reverse | .[0:30] | map(pr_line) | join("\n")),
        "",
        "## Most-reviewed merged contributions",
        "",
        ([.[] | select(.merged)] | sort_by(.review_count) | reverse | .[0:30] | map(pr_line + "; \(.review_count) review events, \(.approving_reviewers | length) approving reviewers") | join("\n")),
        "",
        "## Detailed evidence",
        "",
        (sort_by(.merged_at // .created_at) | reverse | map(
            "### \(.repository)#\(.number): \(.title)\n\n" +
            "- URL: \(.url)\n" +
            "- Created: \(.created_at[0:10])\n" +
            "- Merged: " + (if .merged_at then .merged_at[0:10] else "no" end) + "\n" +
            "- Changes: +\(.additions)/-\(.deletions) across \(.changed_files) files\n" +
            "- Commits: \(.commit_count)\n" +
            "- Reviews: \(.review_count)\n" +
            "- Comments: \(.comment_count)\n" +
            "- Categories: " + ([.categories | to_entries[] | select(.value) | .key] | if length == 0 then "uncategorized" else join(", ") end) +
            "\n- Files:\n" + (.files[0:20] | map("  - `\(.filename)` (+\(.additions)/-\(.deletions))") | join("\n")) +
            (if (.files | length) > 20 then "\n  - _...and \((.files | length) - 20) more files_" else "" end) +
            "\n\n" + (if (.body | length) > 0 then "**PR description:**\n\n" + (.body | gsub("\r"; "") | .[0:2500]) else "_No PR description._" end)
        ) | join("\n\n---\n\n"))
    ] | flatten | join("\n")
    ' "$SUMMARY_JSON" > "$REPORT"

log "Done"
printf '\nGenerated:\n'
printf '  %s\n' "$REPORT"
printf '  %s\n' "$SUMMARY_JSON"
printf '  %s\n' "$PR_DIR"
printf '  %s\n' "$ERROR_LOG"
