"""Reviewable GitHub repository/protection operations. REQ-GOV-B01/B02.

Default is dry-run. Credentials are read only from GH_TOKEN/GITHUB_TOKEN, never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any

CONTEXTS = ["test-approval", "static-analysis", "schema", "semantic-evaluation", "regression", "ai-use-log"]


def protection(test_baseline: bool = False) -> dict[str, Any]:
    return {
        "required_status_checks": None if test_baseline else {"strict": True, "contexts": CONTEXTS},
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True, "require_code_owner_reviews": True,
            "required_approving_review_count": 1, "require_last_push_approval": True,
        },
        "restrictions": None, "required_linear_history": False,
        "allow_force_pushes": False, "allow_deletions": False,
        "block_creations": False, "required_conversation_resolution": True,
    }


def verify_protection(data: dict[str, Any], test_baseline: bool = False) -> None:
    """Check the requested protection against the returned server configuration."""
    expected = protection(test_baseline)
    flags = ("enforce_admins", "allow_force_pushes", "allow_deletions", "required_conversation_resolution")
    different = [key for key in flags if (data.get(key) or {}).get("enabled") is not expected[key]]
    review = data.get("required_pull_request_reviews") or {}
    for key, value in expected["required_pull_request_reviews"].items():
        if type(review.get(key)) is not type(value) or review[key] != value:
            different.append(f"required_pull_request_reviews.{key}")
    bypass = review.get("bypass_pull_request_allowances") or {}
    if any(bypass.get(key) for key in ("users", "teams", "apps")):
        different.append("required_pull_request_reviews.bypass_pull_request_allowances")
    checks = data.get("required_status_checks")
    if test_baseline:
        if checks is not None:
            different.append("required_status_checks must be off on the tests-only baseline")
    elif not checks or checks.get("strict") is not True or set(checks.get("contexts", [])) != set(CONTEXTS):
        different.append("required_status_checks must enforce the six exact contexts on an up-to-date branch")
    if different:
        raise ValueError("Protection readback differs: " + ", ".join(different))


def request(method: str, endpoint: str, payload: Any = None) -> Any:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("Set GH_TOKEN or GITHUB_TOKEN using your existing authenticated account; never paste it into tracked files")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request("https://api.github.com/" + endpoint, data=data, method=method,
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json", "X-GitHub-Api-Version": "2026-03-10"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response) if response.status != 204 else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", help="actual owner/name")
    parser.add_argument("--create", action="store_true", help="create a private repository, then stop")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="perform the displayed API operations")
    mode.add_argument("--check", action="store_true", help="read and verify existing protection without changing it")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("Use an actual owner/repository, not a URL or shell expression")
    owner, name = args.repository.split("/")
    if args.create and args.check:
        parser.error("--check verifies existing branches and cannot be combined with --create")
    operations: list[dict[str, Any]] = ([{"method": "POST", "path": "user/repos", "body": {
        "name": name, "private": True, "description": "CS5351 GradeAide supervised engineering project", "auto_init": False}}]
        if args.create else [
            {"method": "PUT", "path": f"repos/{args.repository}/branches/{branch}/protection",
             "body": protection(branch == "test-baselines")}
            for branch in ("main", "test-baselines")])
    if not args.apply and not args.check:
        print(json.dumps({"dry_run": True, "operations": operations}, indent=2))
        return 0
    try:
        if args.create:
            user = request("GET", "user")
            if user["login"].lower() != owner.lower():
                raise ValueError("Repository owner must match the authenticated personal account")
        for operation in operations:
            if args.apply:
                request(operation["method"], operation["path"], operation["body"])
            if not args.create:
                verified = request("GET", operation["path"])
                baseline = operation["path"].endswith("/test-baselines/protection")
                verify_protection(verified, baseline)
                print(f"PASS protection {operation['path']}")
        print(f"DONE https://github.com/{args.repository}")
        return 0
    except urllib.error.HTTPError as error:
        print(f"BLOCKED GitHub HTTP {error.code}; check authentication, repo permissions, branch existence and account plan", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError) as error:
        print(f"BLOCKED GitHub setup: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
