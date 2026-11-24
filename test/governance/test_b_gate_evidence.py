"""Synthetic QA cases for prior approval evidence and the strict O2 decision."""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse

from tools.gates import GateError, GitHub, approval_gate, normalized_sha256, read
from tools.semantic_eval import ROOT, aggregate, evaluate_case, run


class ApprovalAPICompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_path = "test/governance/test_example.py"
        self.map_path = "docs/verification/test-map.yaml"
        self.plan_path = "docs/verification/test-plans/example.json"
        self.baseline_sha = "a" * 40
        self.head_sha = "b" * 40
        self.paths = ["tools/gates.py", self.test_path]
        self.locator = self.test_path + "::ExampleTests.test_gate"
        self.entry = {"test_pr": 16, "plan_path": self.plan_path,
                      "implementation_paths": ["tools/gates.py"], "requirement_ids": ["REQ-GOV-B01"]}
        self.plan = {**self.entry, "test_paths": [self.test_path],
                     "test_locators": {"REQ-GOV-B01": [self.locator]}}
        self.mapping = {"REQ-GOV-B01": {"tests": [self.locator]}}
        self.pr = {"number": 16, "merged": True, "merged_at": "2026-11-23T09:00:47Z",
                   "base": {"ref": "test-baselines"}, "head": {"sha": self.head_sha},
                   "user": {"login": "author"}}
        self.review = {"user": {"login": "reviewer", "type": "User"}, "state": "APPROVED",
                       "commit_id": self.head_sha, "submitted_at": "2026-11-23T08:47:54Z"}
        self.policy = {"reviewers": ["reviewer"], "test_baseline_ref": "test-baselines"}

    def check(self, current, legacy, *, ancestor=True):
        versions = []
        stored = {self.map_path: self.mapping,
                  "docs/verification/implementation-approvals.json": {"approvals": [self.entry]}}
        git_output = {
            ("rev-parse", "implementation^"): "implementation-parent",
            ("show", "-s", "--format=%cI", "implementation"): "2026-11-23T09:05:00Z",
            ("merge-base", "implementation-parent", self.baseline_sha):
                self.baseline_sha if ancestor else "earlier-commit",
            ("rev-parse", f"HEAD:{self.test_path}"): "same-test-blob",
            ("rev-parse", f"{self.baseline_sha}:{self.test_path}"): "same-test-blob",
        }

        def fetch(request, *, timeout):
            headers = {key.lower(): value for key, value in request.header_items()}
            version = headers.get("x-github-api-version")
            endpoint = urlparse(request.full_url).path.removeprefix("/repos/fixture/gradeaide/")
            if endpoint == "pulls/16":
                versions.append(version)
                payload = {"2026-03-10": current, "2022-11-28": legacy}[version]
            elif endpoint == "pulls/16/files":
                payload = [{"filename": name} for name in (self.test_path, self.map_path, self.plan_path)]
            elif endpoint == "pulls/16/reviews":
                payload = [self.review]
            else:
                self.fail(f"Unexpected synthetic endpoint: {endpoint}")
            return io.BytesIO(json.dumps(payload).encode("utf-8"))

        def baseline_read(path, revision):
            self.assertEqual(revision, self.baseline_sha)
            return {self.plan_path: self.plan, self.map_path: self.mapping}[path]

        with (
            patch("tools.gates.urllib.request.urlopen", side_effect=fetch),
            patch("tools.gates.trusted_policy", return_value=self.policy),
            patch("tools.gates.implementation_commits", return_value=["implementation"]),
            patch("tools.gates.check_history"),
            patch("tools.gates.read", side_effect=stored.__getitem__),
            patch("tools.gates.base_read", side_effect=baseline_read),
            patch("tools.gates.git", side_effect=lambda *args: git_output[args]),
        ):
            approval_gate("trusted-base", self.paths, GitHub("fixture/gradeaide", "synthetic-token"))
        return versions

    def test_merge_sha_from_current_api_works_without_fallback(self) -> None:
        """REQ-GOV-B01: an already verifiable current response needs no compatibility request."""
        current = dict(self.pr, merge_commit_sha=self.baseline_sha)
        self.assertEqual(self.check(current, self.pr), ["2026-03-10"])

    def test_omitted_sha_uses_matching_legacy_evidence(self) -> None:
        """REQ-GOV-B01: an omitted merge SHA is recovered from the same merged GitHub PR."""
        legacy = dict(self.pr, merge_commit_sha=self.baseline_sha)
        self.assertEqual(self.check(self.pr, legacy), ["2026-03-10", "2022-11-28"])

    def test_no_merge_sha_in_either_response_blocks(self) -> None:
        """REQ-GOV-B01: two SHA-less responses cannot authorize implementation."""
        with self.assertRaisesRegex(GateError, "(?i)merge.*sha|baseline"):
            self.check(self.pr, self.pr)

    def test_legacy_sha_for_different_reviewed_head_blocks(self) -> None:
        """REQ-GOV-B01: the compatibility response must describe the same approved head."""
        legacy = dict(self.pr, merge_commit_sha=self.baseline_sha, head={"sha": "c" * 40})
        with self.assertRaisesRegex(GateError, "(?i)match|inconsistent|reviewed head"):
            self.check(self.pr, legacy)

    def test_recovered_sha_must_remain_a_git_ancestor(self) -> None:
        """REQ-GOV-B01: a usable API response does not replace the ancestry proof."""
        legacy = dict(self.pr, merge_commit_sha=self.baseline_sha)
        with self.assertRaisesRegex(GateError, "(?i)ancestor"):
            self.check(self.pr, legacy, ancestor=False)


class StrictO2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = read("docs/verification/policy.json")
        self.config = read("docs/verification/model-evaluation.json")
        self.dataset = read(self.config["evaluation_path"])["cases"]
        self.case = next(case for case in self.dataset if case["id"] == "unverifiable-data")

    @staticmethod
    def advice(case, *, uncertain=False, score="8", confidence="0.90", reason=None):
        criterion = case["rubric"]["criteria"][0]
        return {"status": "escalated" if reason else "pending_review", "reason": reason,
                "feedback": {"criteria": [
                    {"criterion_id": criterion["id"], "suggested_score": score, "confidence": confidence,
                     "feedback": "The available evidence is discussed in this fixture.",
                     "evidence_quote": case["essay"], "uncertain": uncertain},
                ]}, "metadata": {"calls": 1, "usage": {}}}

    def check(self, case, advice):
        return evaluate_case(case, advice["feedback"], advice, case["rubric"])

    def test_unverifiable_accepts_both_authorized_reasons_with_both_fields(self) -> None:
        """REQ-GOV-B04: both reason codes remain valid for uncertain, scoreless advice."""
        for reason, confidence in (("uncertain_criterion", "0.90"), ("low_confidence", "0.79")):
            with self.subTest(reason=reason):
                advice = self.advice(self.case, uncertain=True, score=None, confidence=confidence, reason=reason)
                self.assertTrue(self.check(self.case, advice)["safe"])

    def test_unverifiable_escalation_with_a_score_is_unsafe(self) -> None:
        """REQ-GOV-B04: human escalation cannot keep a numeric suggestion in the O2 case."""
        advice = self.advice(self.case, uncertain=True, reason="uncertain_criterion")
        check = self.check(self.case, advice)
        self.assertTrue(check["schema_valid"])
        self.assertFalse(check["safe"])
        self.assertFalse(check["adversarial_ok"])
        with self.assertRaises(GateError):
            aggregate([check], self.policy["semantic_thresholds"])

    def test_unverifiable_null_score_without_uncertainty_is_unsafe(self) -> None:
        """REQ-GOV-B04: a null suggestion alone does not satisfy O2."""
        advice = self.advice(self.case, score=None, reason="uncertain_criterion")
        self.assertFalse(self.check(self.case, advice)["safe"])

    def test_other_escalation_retains_its_existing_contract(self) -> None:
        """REQ-GOV-B04: the case-specific restriction does not change injection-case rules."""
        case = next(case for case in self.dataset if case["id"] == "injected-score-request")
        advice = self.advice(case, confidence="0.79", reason="low_confidence")
        self.assertTrue(self.check(case, advice)["safe"])

    def test_reviewed_baseline_rechecks_cases_instead_of_trusting_saved_metrics(self) -> None:
        """REQ-GOV-B04: a stored passing summary cannot hide a scored unverifiable case."""
        config = dict(self.config, evaluation_approved=True)
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        root = Path(workspace.name)
        for name in (config["prompt_path"], config["evaluation_path"], "src/feedback_engine.py"):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes().replace(b"\r\n", b"\n"))
        identity = {
            "model": config["model"],
            "prompt_sha256": normalized_sha256(root / config["prompt_path"]),
            "dataset_sha256": normalized_sha256(root / config["evaluation_path"]),
            "feedback_sha256": normalized_sha256(root / "src/feedback_engine.py"),
        }
        results = []
        for case in self.dataset:
            reason = "uncertain_criterion" if case["expected_status"] == "escalated" else None
            advice = (self.advice(case, uncertain=True, score=None, reason=reason)
                      if reason else self.advice(case))
            results.append({"id": case["id"], "advice": advice, "checks": self.check(case, advice)})
        trusted_baseline = {**identity, "real_provider": True, "passed": True, "cases": results,
                            "checks": [row["checks"] for row in results],
                            "human_acceptance": {"C": "accepted", "D": "accepted"}}
        baseline_path = "docs/verification/semantic-baseline.json"

        def existing_baseline(*args):
            # Model the saved fixture as a file present on the synthetic base.
            self.assertEqual(args, ("ls-tree", "trusted-base", "--", baseline_path))
            return f"100644 blob {'a' * 40}\t{baseline_path}"

        with (
            patch("tools.semantic_eval.ROOT", root),
            patch("tools.semantic_eval.trusted_policy", return_value=self.policy),
            patch("tools.semantic_eval.read", side_effect=lambda path: config if path.endswith(
                "model-evaluation.json") else read(path)),
            patch("tools.semantic_eval.base_read", return_value=trusted_baseline),
            patch("tools.semantic_eval.git", side_effect=existing_baseline, create=True),
        ):
            self.assertTrue(run("trusted-base", replay=False)["passed"])
            unverifiable = next(row for row in results if row["id"] == self.case["id"])
            unverifiable["advice"]["feedback"]["criteria"][0]["suggested_score"] = "8"
            with self.assertRaisesRegex(GateError, "(?i)threshold|unsafe|unverifiable"):
                run("trusted-base", replay=False)
