#!/usr/bin/env python3
"""Generate a CV-focused Markdown report from normalized pull requests."""

import argparse
import json
from pathlib import Path


def line(pr):
    status = f"merged {pr['merged_at'][:10]}" if pr["merged"] else pr["state"]
    return (
        f"- [{pr['repository']}#{pr['number']}: {pr['title']}]({pr['url']}) — "
        f"{status}; +{pr['additions']}/-{pr['deletions']}, {pr['changed_files']} files"
    )


def section(title, items):
    if not items:
        content = "_No matching pull requests._"
    else:
        content = "\n".join(line(pr) for pr in sorted(
            items, key=lambda pr: pr["merged_at"] or pr["created_at"], reverse=True
        ))
    return f"## {title}\n\n{content}\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--org", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prs = json.loads(args.input.read_text())
    merged = [pr for pr in prs if pr["merged"]]

    def category_count(name):
        return sum(pr["categories"].get(name, False) for pr in prs)

    def details(pr):
        categories = ", ".join(name for name, value in pr["categories"].items() if value) or "uncategorized"
        files = "\n".join(
            f"  - `{item['filename']}` (+{item['additions']}/-{item['deletions']})"
            for item in pr["files"][:20]
        )
        if len(pr["files"]) > 20:
            files += f"\n  - _...and {len(pr['files']) - 20} more files_"
        body = pr["body"].replace("\r", "")[:2500] if pr["body"] else None
        description = f"**PR description:**\n\n{body}" if body else "_No PR description._"
        return (
            f"### {pr['repository']}#{pr['number']}: {pr['title']}\n\n"
            f"- URL: {pr['url']}\n"
            f"- Created: {pr['created_at'][:10]}\n"
            f"- Merged: {pr['merged_at'][:10] if pr['merged_at'] else 'no'}\n"
            f"- Changes: +{pr['additions']}/-{pr['deletions']} across {pr['changed_files']} files\n"
            f"- Commits: {pr['commit_count']}\n- Reviews: {pr['review_count']}\n"
            f"- Comments: {pr['comment_count']}\n- Categories: {categories}\n"
            f"- Files:\n{files}\n\n{description}"
        )

    repository_summary = "\n".join(
        f"- **{repository}:** {len(items)} authored; "
        f"{sum(pr['merged'] for pr in items)} merged"
        for repository, items in sorted(
            ((repository, [pr for pr in prs if pr["repository"] == repository])
             for repository in {pr["repository"] for pr in prs}),
            key=lambda pair: len(pair[1]), reverse=True,
        )
    )
    category_sections = [
        ("CI/CD", "ci_cd"),
        ("Release engineering", "release_engineering"),
        ("Testing and validation", "testing"),
        ("Security-sensitive work", "security"),
        ("Reliability and defect fixes", "reliability"),
        ("Mobile engineering", "mobile"),
        ("Browser and extension work", "browser"),
        ("Developer tooling", "developer_tooling"),
        ("Performance", "performance"),
    ]
    largest = "\n".join(line(pr) for pr in sorted(merged, key=lambda pr: pr["additions"] + pr["deletions"], reverse=True)[:30])
    reviewed = "\n".join(
        line(pr) + f"; {pr['review_count']} review events, {len(pr['approving_reviewers'])} approving reviewers"
        for pr in sorted(merged, key=lambda pr: pr["review_count"], reverse=True)[:30]
    )

    parts = [
        "# GitHub career-history report", "", f"**User:** @{args.user}",
        f"**Organization:** {args.org}", f"**Period:** {args.start_date} through {args.end_date}", "",
        "## Headline metrics", "", f"- Authored pull requests: **{len(prs)}**",
        f"- Merged pull requests: **{len(merged)}**",
        f"- Repositories touched: **{len({pr['repository'] for pr in prs})}**",
        f"- Changed files: **{sum(pr['changed_files'] for pr in prs)}**",
        f"- Additions: **{sum(pr['additions'] for pr in prs)}**",
        f"- Deletions: **{sum(pr['deletions'] for pr in prs)}**", "",
        "## Category counts", "",
        *[f"- {title}: **{category_count(name)}**" for title, name in category_sections], "",
        "## Repository summary", "", repository_summary, "",
        *[section(title, [pr for pr in prs if pr["categories"].get(name)]) for title, name in category_sections],
        "## Largest merged contributions", "", largest, "",
        "## Most-reviewed merged contributions", "", reviewed, "",
        "## Detailed evidence", "", "\n\n---\n\n".join(details(pr) for pr in sorted(prs, key=lambda pr: pr["merged_at"] or pr["created_at"], reverse=True)),
    ]
    args.output.write_text("\n".join(parts))


if __name__ == "__main__":
    main()
