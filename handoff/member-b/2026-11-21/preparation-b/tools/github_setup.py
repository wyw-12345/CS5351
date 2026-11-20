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
    parser.add_argument("--apply", action="store_true", help="perform the displayed API operations")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("Use an actual owner/repository, not a URL or shell expression")
    owner, name = args.repository.split("/")
    operations: list[dict[str, Any]] = ([{"method": "POST", "path": "user/repos", "body": {
        "name": name, "private": True, "description": "CS5351 GradeAide supervised engineering project", "auto_init": False}}]
        if args.create else [
            {"method": "PUT", "path": f"repos/{args.repository}/branches/{branch}/protection",
             "body": protection(branch == "test-baselines")}
            for branch in ("main", "test-baselines")])
    print(json.dumps({"dry_run": not args.apply, "operations": operations}, indent=2))
    if not args.apply:
        return 0
    try:
        user = request("GET", "user")
        if args.create and user["login"].lower() != owner.lower():
            raise ValueError("Repository owner must match the authenticated personal account")
        for operation in operations:
            request(operation["method"], operation["path"], operation["body"])
            if not args.create:
                verified = request("GET", operation["path"])
                expected = operation["body"]
                if not verified.get("enforce_admins", {}).get("enabled"):
                    raise ValueError("Protection readback: administrators are not enforced")
                if not verified.get("required_pull_request_reviews", {}).get("require_last_push_approval"):
                    raise ValueError("Protection readback: latest push review is not required")
                if expected["required_status_checks"]:
                    actual = set(verified.get("required_status_checks", {}).get("contexts", []))
                    if set(CONTEXTS) - actual:
                        raise ValueError("Protection readback: missing required gate contexts")
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
