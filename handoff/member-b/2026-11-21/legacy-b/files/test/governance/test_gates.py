"""Independent negative self-tests for B's governance tools, not application evidence."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.check_suite import acceptable  # noqa: E402
from tools.gates import (  # noqa: E402
    GateError,
    approval_evidence,
    approved_scope,
    check_ai_log,
    check_history,
    check_imports,
    human_approval,
    read,
    readiness,
    traceability,
    validate_registry,
)
from tools.github_setup import CONTEXTS, protection  # noqa: E402


class GateTests(unittest.TestCase):
    def review(self, **overrides: Any) -> dict[str, Any]:
        row = {"user": {"login": "reviewer", "type": "User"}, "state": "APPROVED",
               "commit_id": "test-head", "submitted_at": "2026-11-01T10:00:00Z"}
        row.update(overrides)
        return row

    def evidence(self, **overrides: Any) -> dict[str, Any]:
        row = {"merged": True, "merged_at": "2026-11-01T11:00:00Z",
               "user": {"login": "author"}, "head": {"sha": "test-head"}}
        row.update(overrides)
        return row

    def test_approval_requires_human(self) -> None:
        """REQ-GOV-B01: bot cannot count as independent human review."""
        with self.assertRaises(GateError):
            human_approval([self.review(user={"login": "reviewer", "type": "Bot"})],
                           "author", "test-head", ["reviewer"])

    def test_self_approval_rejected(self) -> None:
        """REQ-GOV-B01: author cannot approve own tests even if allowlisted."""
        with self.assertRaises(GateError):
            human_approval([self.review()], "reviewer", "test-head", ["reviewer"])

    def test_stale_approval_rejected(self) -> None:
        """REQ-GOV-B01: approval of earlier SHA is stale."""
        with self.assertRaises(GateError):
            human_approval([self.review(commit_id="old-head")], "author", "test-head", ["reviewer"])

    def test_dismissed_approval_rejected(self) -> None:
        """REQ-GOV-B01: later dismissal supersedes earlier approval."""
        with self.assertRaises(GateError):
            human_approval([self.review(), self.review(state="DISMISSED", submitted_at="2026-11-01T12:00:00Z")],
                           "author", "test-head", ["reviewer"])

    def test_changes_requested_supersedes(self) -> None:
        """REQ-GOV-B01: changes requested supersedes prior APPROVED."""
        with self.assertRaises(GateError):
            human_approval([self.review(), self.review(state="CHANGES_REQUESTED", submitted_at="2026-11-01T12:00:00Z")],
                           "author", "test-head", ["reviewer"])

    def test_unlisted_reviewer_rejected(self) -> None:
        """REQ-GOV-B01: contributor cannot self-expand trusted reviewer allowlist."""
        with self.assertRaises(GateError):
            human_approval([self.review()], "author", "test-head", ["someone-else"])

    def test_valid_prior_review(self) -> None:
        """REQ-GOV-B01: independent approval and merge both precede implementation."""
        approval_evidence(self.evidence(), [self.review()], ["test/offline/test_x.py"],
                          {"reviewers": ["reviewer"]}, "2026-11-02T00:00:00Z")

    def test_unrelated_prior_tests_cannot_approve_new_code(self) -> None:
        """REQ-GOV-B01: an old unrelated approved test cannot authorize new source."""
        plan = {"implementation_paths": ["src/old.py"], "requirement_ids": ["REQ-X-001"],
                "test_paths": ["test/offline/test_old.py"]}
        entry = {"implementation_paths": ["src/new.py"], "requirement_ids": ["REQ-X-001"]}
        with self.assertRaises(GateError):
            approved_scope(plan, entry, ["test/offline/test_old.py"],
                           {"REQ-X-001": {"tests": ["test/offline/test_old.py::Tests.test_x"]}})

    def test_reviewed_scope_requires_related_trace(self) -> None:
        """REQ-GOV-B01: requirement tests must be part of the actual approved PR."""
        plan = {"implementation_paths": ["src/x.py"], "requirement_ids": ["REQ-X-001"],
                "test_paths": ["test/offline/test_x.py"]}
        entry = {"implementation_paths": ["src/x.py"], "requirement_ids": ["REQ-X-001"]}
        with self.assertRaises(GateError):
            approved_scope(plan, entry, ["test/offline/test_x.py"],
                           {"REQ-X-001": {"tests": ["test/offline/test_other.py::Tests.test_x"]}})

    def test_approval_after_implementation_rejected(self) -> None:
        """REQ-GOV-B01: approval cannot be added retroactively."""
        with self.assertRaises(GateError):
            approval_evidence(self.evidence(), [self.review()], ["test/offline/test_x.py"],
                              {"reviewers": ["reviewer"]}, "2026-11-01T09:00:00Z")

    def test_equal_time_is_not_before(self) -> None:
        """REQ-GOV-B01: simultaneous timestamp is insufficient ordering evidence."""
        with self.assertRaises(GateError):
            approval_evidence(self.evidence(merged_at="2026-11-01T09:00:00Z"), [self.review()],
                              ["test/offline/test_x.py"], {"reviewers": ["reviewer"]}, "2026-11-01T10:00:00Z")

    def test_unmerged_test_pr_rejected(self) -> None:
        """REQ-GOV-B01: a file claiming approval is not a merged approved baseline."""
        with self.assertRaises(GateError):
            approval_evidence(self.evidence(merged=False), [self.review()], ["test/offline/test_x.py"],
                              {"reviewers": ["reviewer"]}, "2026-11-02T00:00:00Z")

    def test_test_pr_containing_code_rejected(self) -> None:
        """REQ-GOV-B01: mixed tests and implementation PR is not tests-before-code."""
        with self.assertRaises(GateError):
            approval_evidence(self.evidence(), [self.review()], ["test/test_x.py", "src/x.py"],
                              {"reviewers": ["reviewer"]}, "2026-11-02T00:00:00Z")

    def test_forbidden_feedback_import(self) -> None:
        """REQ-GOV-B02: advisory component cannot import grade store or write helper. Additional registry obligations: REQ-INV-007, REQ-QUAL-001."""
        for source in ("import grade_store", "from pathlib import Path", "from . import grade_store", "exec('x')"):
            with self.subTest(source=source), self.assertRaises(GateError):
                check_imports(source, "feedback_engine")

    def test_calculator_network_import_rejected(self) -> None:
        """REQ-GOV-B02: calculator cannot introduce provider or network dependencies. Additional registry obligations: REQ-SEC-006."""
        with self.assertRaises(GateError):
            check_imports("import urllib.request", "score_calculator")
        check_imports("from decimal import Decimal", "score_calculator")

    def test_missing_registry_fails(self) -> None:
        """REQ-GOV-B03: missing handoff must not be treated as a passing schema gate."""
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(GateError):
            read("docs/req/requirements.yaml", Path(tmp))

    def test_missing_upstream_fails(self) -> None:
        """REQ-GOV-B03: missing source/architecture fails release readiness."""
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(GateError):
            readiness(Path(tmp))

    def test_duplicate_requirement_ids_rejected(self) -> None:
        """REQ-GOV-B03: schema-valid duplicate IDs remain a semantic failure."""
        data = read("docs/member-b/requirements-proposal.yaml")
        with self.assertRaises(GateError):
            validate_registry(data + [copy.deepcopy(data[0])], read("docs/member-b/proposal-schema.json"), False)

    def test_nonzero_invariant_threshold_rejected(self) -> None:
        """REQ-GOV-B03: invariant threshold cannot tolerate escapes."""
        data = read("docs/member-b/requirements-proposal.yaml")
        data[0]["fit_criterion"]["threshold"] = 1
        with self.assertRaises(GateError):
            validate_registry(data, read("docs/member-b/proposal-schema.json"), False)

    def test_official_registry_needs_seven_types(self) -> None:
        """REQ-GOV-B03: B-only proposal is not a complete official registry."""
        with self.assertRaises(GateError):
            validate_registry(read("docs/member-b/requirements-proposal.yaml"), read("docs/member-b/proposal-schema.json"))

    def test_proposal_trace_targets_exist(self) -> None:
        """REQ-GOV-B03: every proposed requirement has an actual named test with ID."""
        traceability(read("docs/member-b/requirements-proposal.yaml"))

    def test_history_test_change_rejected(self) -> None:
        """REQ-GOV-B05: editing/deleting an existing test cannot hide a regression."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = os.environ.get("GIT_BIN", "git")
            def run(*args: str) -> str:
                return subprocess.check_output([exe, *args], cwd=root, text=True).strip()
            run("init", "-q")
            run("config", "user.name", "Local Test Fixture")
            run("config", "user.email", "fixture@example.invalid")
            (root / "test").mkdir()
            (root / "test/test_old.py").write_text("# prior suite", encoding="utf-8")
            run("add", ".")
            run("commit", "-qm", "fixture baseline")
            with self.assertRaises(GateError):
                check_history(["test/test_old.py"], "HEAD", root)
            check_history(["test/test_new.py"], "HEAD", root)

    def test_log_whitespace_change_rejected(self) -> None:
        """REQ-GOV-B06: rewriting log whitespace or old records is not new evidence."""
        with self.assertRaises(GateError):
            check_ai_log([], [], ["src/x.py"])

    def test_log_must_cover_changed_paths(self) -> None:
        """REQ-GOV-B06: unrelated log entry does not cover current code change."""
        entry = {"id": "x", "date": "2026-11-06", "agent": "Codex", "purpose": "test",
                 "files": ["src/other.py"], "evidence": "local log", "human_review": "pending"}
        with self.assertRaises(GateError):
            check_ai_log([], [entry], ["src/x.py"])

    def test_log_actual_new_entry_passes(self) -> None:
        """REQ-GOV-B06: explicit honest pending review entry satisfies logging only."""
        entry = {"id": "x", "date": "2026-11-06", "agent": "Codex", "purpose": "test",
                 "files": ["src/x.py"], "evidence": "local log", "human_review": "pending"}
        check_ai_log([], [entry], ["src/x.py"])
        self.assertEqual(json.loads(json.dumps(entry))["human_review"], "pending")

    def test_log_cannot_rewrite_history(self) -> None:
        """REQ-GOV-B06: editing a previous entry cannot substitute for an append."""
        old = {"id": "old", "agent": "Codex"}
        with self.assertRaises(GateError):
            check_ai_log([old], [{"id": "old", "agent": "someone-else"}], ["src/x.py"])

    def test_empty_and_skipped_suites_rejected(self) -> None:
        """REQ-GOV-B05: successful unittest status alone cannot hide skips/no tests."""
        result = unittest.TestResult()
        self.assertFalse(acceptable(result))
        result.testsRun = 1
        self.assertTrue(acceptable(result))
        result.skipped.append((unittest.FunctionTestCase(lambda: None), "missing key"))
        self.assertFalse(acceptable(result))

    def test_protection_requires_six_gates(self) -> None:
        """REQ-GOV-B02: main requires all six checks, reviews and admin enforcement."""
        policy = protection()
        self.assertEqual(set(policy["required_status_checks"]["contexts"]), set(CONTEXTS))
        self.assertTrue(policy["enforce_admins"])
        self.assertTrue(policy["required_pull_request_reviews"]["require_last_push_approval"])
        self.assertFalse(policy["allow_force_pushes"])
        self.assertIsNone(protection(True)["required_status_checks"])


if __name__ == "__main__":
    unittest.main()
