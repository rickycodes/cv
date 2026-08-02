#!/usr/bin/env python3
"""Combine the GitHub API responses for one pull request."""

import argparse
import json
import re
from pathlib import Path


CATEGORIES = {
    "ci_cd": r"github.?actions|circleci|workflow|pipeline|continuous integration|ci/|\.github/",
    "release_engineering": r"release|publish|publishing|npm|version|changelog|artifact|slack",
    "testing": r"test|spec|jest|selenium|fixture|mock|coverage|regression|e2e|integration",
    "security": r"security|encrypt|wallet|password|authentication|secret recovery|srp|keyring|vault",
    "reliability": r"fix|bug|crash|failure|error|corrupt|restore|recovery|stability|reliability",
    "mobile": r"android|ios|mobile|react.native|deeplink|biometric",
    "browser": r"browser|extension|firefox|chrome|webview|dapp",
    "developer_tooling": r"tool|script|lint|build|workflow|action|automation|developer|cli",
    "performance": r"performance|optimi[sz]|cache|latency|speed|memory",
    "documentation": r"docs|documentation|readme|guide|instructions",
}


def read_json(path: Path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=Path, required=True)
    parser.add_argument("--files", type=Path, required=True)
    parser.add_argument("--commits", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--comments", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    pr = read_json(args.pr)
    files = read_json(args.files)
    commits = read_json(args.commits)
    reviews = read_json(args.reviews)
    comments = read_json(args.comments)
    corpus = " ".join([
        pr.get("title") or "",
        pr.get("body") or "",
        " ".join(item.get("filename", "") for item in files),
    ])

    detail = {
        "repository": pr["base"]["repo"]["full_name"],
        "number": pr["number"],
        "title": pr["title"],
        "url": pr["html_url"],
        "state": pr["state"],
        "draft": pr.get("draft") or False,
        "merged": pr.get("merged_at") is not None,
        "created_at": pr["created_at"],
        "updated_at": pr["updated_at"],
        "closed_at": pr.get("closed_at"),
        "merged_at": pr.get("merged_at"),
        "body": pr.get("body") or "",
        "labels": [label["name"] for label in pr.get("labels", [])],
        "base_branch": pr["base"]["ref"],
        "head_branch": pr["head"]["ref"],
        "additions": pr.get("additions") or 0,
        "deletions": pr.get("deletions") or 0,
        "changed_files": pr.get("changed_files") or 0,
        "commit_count": len(commits),
        "review_count": len(reviews),
        "comment_count": len(comments),
        "approving_reviewers": sorted({
            review["user"]["login"]
            for review in reviews
            if review.get("state") == "APPROVED" and review.get("user")
        }),
        "files": [
            {key: item.get(key) for key in ("filename", "status", "additions", "deletions", "changes")}
            for item in files
        ],
        "commits": [
            {
                "sha": commit["sha"],
                "message": commit["commit"]["message"].split("\n")[0],
                "authored_at": commit["commit"]["author"]["date"],
                "author": (commit.get("author") or {}).get("login")
                or commit["commit"]["author"].get("name")
                or "unknown",
            }
            for commit in commits
        ],
        "categories": {
            name: re.search(pattern, corpus, re.IGNORECASE) is not None
            for name, pattern in CATEGORIES.items()
        },
    }

    args.output.write_text(json.dumps(detail, indent=2) + "\n")


if __name__ == "__main__":
    main()
