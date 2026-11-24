"""Checks for release chronology in disposable Git histories and synthetic PRs."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import gates


class ReviewedScopesTests(unittest.TestCase):
    AGGREGATE = "docs/verification/implementation-approvals.json"
    TEST_MAP = "docs/verification/test-map.yaml"
    SOURCE = "src/feature.py"
    REQUIREMENT = "REQ-GOV-B01"

    def setUp(self) -> None:
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.now = datetime(2025, 4, 1, tzinfo=timezone.utc)
        self.pull_requests = {}
        self.reviewed_files = {}
        self.reviews = {}
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Fixture Author")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "core.autocrlf", "false")
        self.write_json("docs/verification/policy.json", {
            "status": "active", "reviewers": ["fixture-reviewer"], "test_baseline_ref": "test-baselines",
        })
        self.write_json(self.TEST_MAP, {})
        self.write_json(self.AGGREGATE, {"approvals": []})
        self.write(self.SOURCE, "revision = 0\n")
        self.base = self.commit("Release base")
        self.git("branch", "test-baselines")
        self.git("switch", "-q", "-c", "candidate")

    def tick(self) -> str:
        self.now += timedelta(minutes=1)
        return self.now.isoformat()

    def git(self, *args, date=None):
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_CONFIG_")}
        if date is not None:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        command = [os.environ.get("GIT_BIN", "git"), *args]
        return subprocess.check_output(command, cwd=self.root, env=env, text=True).strip()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def write_json(self, name, value):
        self.write(name, json.dumps(value) + "\n")

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "-qm", message, date=self.tick())
        return self.git("rev-parse", "HEAD")

    def approve_tests(self, number, test_path, *, maintenance=False):
        topic = f"tests-{number}"
        self.git("switch", "-q", "-c", topic, "test-baselines")
        self.write(test_path, f"def test_requirement():\n    return {number}\n")
        scope = f"docs/verification/test-plans/change-{number}.json"
        if not maintenance:
            locator = f"{test_path}::test_requirement"
            self.write_json(scope, {
                "implementation_paths": [self.SOURCE],
                "requirement_ids": [self.REQUIREMENT],
                "test_paths": [test_path],
                "test_locators": {self.REQUIREMENT: [locator]},
            })
            mapping = json.loads((self.root / self.TEST_MAP).read_text(encoding="utf-8"))
            mapping.setdefault(self.REQUIREMENT, {"tests": []})["tests"].append(locator)
            self.write_json(self.TEST_MAP, mapping)
        head = self.commit(f"Tests only {number}")
        reviewed_at = self.tick()
        self.git("switch", "-q", "test-baselines")
        merged_at = self.tick()
        self.git("merge", "-q", "--no-ff", "-m", f"Approved tests {number}", topic, date=merged_at)
        merge = self.git("rev-parse", "HEAD")
        self.pull_requests[number] = {
            "number": number, "merged": True, "merged_at": merged_at, "merge_commit_sha": merge,
            "base": {"ref": "test-baselines"}, "head": {"sha": head}, "user": {"login": "fixture-author"},
        }
        self.reviewed_files[number] = [{"filename": test_path}]
        if not maintenance:
            self.reviewed_files[number].extend({"filename": name} for name in (scope, self.TEST_MAP))
        self.reviews[number] = [{
            "user": {"login": "fixture-reviewer", "type": "User"}, "state": "APPROVED",
            "commit_id": head, "submitted_at": reviewed_at,
        }]
        self.git("switch", "-q", "candidate")
        self.git("merge", "-q", "--no-ff", "-m", f"Take approved tests {number}", merge, date=self.tick())
        return scope

    def implement(self, number, test_path):
        plan = self.approve_tests(number, test_path)
        self.write(self.SOURCE, f"revision = {number}\n")
        commit = self.commit(f"Implement approved scope {number}")
        return {"test_pr": number, "plan_path": plan, "implementation_paths": [self.SOURCE],
                "implementation_commits": [commit], "requirement_ids": [self.REQUIREMENT]}

    def record(self, *entries, maintenance=()):
        self.write_json(self.AGGREGATE, {"approvals": list(entries), "test_maintenance": list(maintenance)})
        self.commit("Record scope and review links")

    def get(self, endpoint, **kwargs):
        namespace, number = endpoint.split("/")
        self.assertEqual(namespace, "pulls")
        return self.pull_requests[int(number)]

    def pages(self, endpoint):
        namespace, number, resource = endpoint.split("/")
        self.assertEqual(namespace, "pulls")
        return {"files": self.reviewed_files, "reviews": self.reviews}[resource][int(number)]

    def assert_gate(self, gate_name, code):
        git_from = gates.git
        read_from = gates.read
        out = StringIO()
        with (
            patch("tools.gates.git", side_effect=lambda *args, **kw: git_from(
                *args, root=self.root, check=kw.get("check", True))),
            patch("tools.gates.read", side_effect=lambda path, **kw: read_from(path, root=self.root)),
            patch("tools.gates.GitHub", return_value=self),
            patch("sys.argv", ["gates.py", gate_name, "--base", self.base]),
            patch.dict(os.environ, {"PR_NUMBER": "1", "GITHUB_REPOSITORY": "fixture/project",
                                    "GITHUB_TOKEN": "synthetic-review-token"}),
            redirect_stderr(out),
            redirect_stdout(out),
        ):
            result = gates.main()
        self.assertEqual(result, code, out.getvalue())

    def test_independently_approved_scopes_can_change_the_same_file(self) -> None:
        """REQ-GOV-B01: verify separate reviewed implementation revisions even on one path."""
        first = self.implement(101, "test/test_first.py")
        second = self.implement(102, "test/test_second.py")
        self.record(first, second)
        self.assert_gate("approval", 0)

    def test_regression_history_uses_the_scope_that_introduced_the_test(self) -> None:
        """REQ-GOV-B05: later approved tests can precede their own implementation."""
        first = self.implement(101, "test/test_first.py")
        second = self.implement(102, "test/test_second.py")
        self.record(first, second)
        self.assert_gate("history", 0)

    def test_separately_approved_fixture_change_keeps_earlier_evidence(self) -> None:
        """REQ-GOV-B01 REQ-GOV-B05: later test-only maintenance has its own protected review."""
        path = "test/test_first.py"
        first = self.implement(101, path)
        self.approve_tests(103, path, maintenance=True)
        self.record(first, maintenance=({"test_pr": 103, "supersedes_test_pr": 101, "test_paths": [path]},))
        self.assert_gate("approval", 0)
        self.assert_gate("history", 0)

    def test_reviewed_path_does_not_authorize_a_later_unreviewed_commit(self) -> None:
        """REQ-GOV-B01: a valid approval cannot cover an unrelated later change to the same path."""
        first = self.implement(101, "test/test_first.py")
        self.write(self.SOURCE, "revision = 999\n")
        self.commit("Unreviewed subsequent change")
        self.record(first)
        self.assert_gate("approval", 1)

    def test_concurrent_code_and_test_with_no_prior_approval_are_blocked(self) -> None:
        """REQ-GOV-B01 REQ-GOV-B05: mixed historical commits without prior evidence stay blocked."""
        self.write(self.SOURCE, "revision = 999\n")
        self.write("test/test_mixed.py", "def test_mixed():\n    return True\n")
        self.commit("Code and test arrive together")
        self.assert_gate("approval", 1)
        self.assert_gate("history", 1)

    def test_unreviewed_edits_to_the_later_fixture_are_blocked(self) -> None:
        """REQ-GOV-B01 REQ-GOV-B05: later maintenance approval pins the final test blob."""
        path = "test/test_first.py"
        first = self.implement(101, path)
        self.approve_tests(103, path, maintenance=True)
        self.write(path, "def test_requirement():\n    return False\n")
        self.commit("Unreviewed edit to approved fixture")
        self.record(first, maintenance=({"test_pr": 103, "supersedes_test_pr": 101, "test_paths": [path]},))
        self.assert_gate("approval", 1)
        self.assert_gate("history", 1)
