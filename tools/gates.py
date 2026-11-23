"""Fail-closed verification gates. REQ-GOV-B01 through REQ-GOV-B06."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if __name__ == "__main__":
    sys.modules["tools.gates"] = sys.modules[__name__]
IMPLEMENTATION = ("src/", "tools/", "scripts/", "prompts/", "config/", ".github/", ".opencode/", ".agent/")
SAFETY = IMPLEMENTATION + ("docs/verification/", "docs/code-governance/", "AGENTS.md")
DEPENDENCIES = ("requirements-ci.txt", "requirements-app.txt", "requirements-dev.txt", "requirements-b-supplement.txt", "pyproject.toml")
REQUIRED = (
    "docs/req/requirements.yaml", "docs/req/req-schema.json", "architecture-blueprint.md",
    "docs/architecture/invariants.md", "docs/architecture/trace-matrix.md", "AGENTS.md",
    "Prompt.md", "docs/code-governance/structural-constraints.md", ".opencode/permissions.jsonc",
    "docs/ai-use-log.yaml", "src/feedback_engine.py", "src/score_calculator.py",
    "src/grade_store.py", "docs/verification/model-evaluation.json", "requirements-app.txt",
    "docs/verification/api-surface.json", "docs/verification/permissions-snapshot.json",
)


class GateError(RuntimeError):
    """An actionable blocking failure."""


def require(condition: Any, message: str) -> None:
    if not condition:
        raise GateError(message)


def read(path: str, root: Path = ROOT) -> Any:
    target = root / path
    require(target.is_file(), f"Missing required artifact: {path}")
    return yaml.safe_load(target.read_text(encoding="utf-8"))


def git(*args: str, root: Path = ROOT, check: bool = True) -> str:
    result = subprocess.run([os.environ.get("GIT_BIN", "git"), *args], cwd=root,
                            capture_output=True, text=True, encoding="utf-8", check=False)
    if check:
        require(result.returncode == 0, f"Git failed: {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def base_read(path: str, base: str, root: Path = ROOT) -> Any:
    return yaml.safe_load(git("show", f"{base}:{path}", root=root))


def changed(base: str, head: str = "HEAD", root: Path = ROOT) -> list[str]:
    # --no-renames exposes removed baseline tests instead of hiding them as a rename.
    return git("diff", "--no-renames", "--name-only", base, head, root=root).splitlines()


def is_implementation(path: str) -> bool:
    return (path.startswith(IMPLEMENTATION) or path in DEPENDENCIES
            or path == "docs/verification/model-evaluation.json"
            or (not path.startswith("test/") and path.endswith((".py", ".ps1", ".sh", ".cmd", ".bat"))))


def readiness(root: Path = ROOT) -> None:
    missing = [p for p in REQUIRED if not (root / p).is_file()]
    require(not missing, "Upstream handoff incomplete:\n- " + "\n- ".join(missing))
    policy = read("docs/verification/policy.json", root)
    require(policy.get("status") == "active", "Artifacts exist, but real human baseline approval remains pending")


def validate_registry(data: Any, schema: Any, all_types: bool = True) -> None:
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(data, schema)
    require(isinstance(data, list) and len(data) > 0, "Requirements must be a nonempty list")
    ids = [r["id"] for r in data]
    require(len(ids) == len(set(ids)), "Duplicate requirement IDs")
    for req in data:
        require(all(k in req for k in ("id", "type", "statement", "fit_criterion", "priority", "tradeoff")),
                "Requirement missing mandatory fields")
        fit = req["fit_criterion"]
        require(isinstance(fit, dict) and all(k in fit for k in ("metric", "threshold", "verification")),
                f"{req['id']}: incomplete fit criterion")
        if req["type"] == "invariant":
            require(fit["threshold"] in (0, "0", "zero escapes"), f"{req['id']}: invariant must be zero tolerance")
    if all_types:
        required = {"functional", "invariant", "quality", "performance", "cost", "governance", "security"}
        require(required <= {r["type"] for r in data}, "Official registry must cover all seven requirement types")


def traceability(registry: list[dict[str, Any]], root: Path = ROOT) -> None:
    mapping = read("docs/verification/test-map.yaml", root)
    for req in registry:
        entry = mapping.get(req["id"], {})
        require(entry.get("tests"), f"No tests mapped for {req['id']}")
        if req["type"] == "invariant":
            require(entry.get("negative") is True, f"No negative test declared for {req['id']}")
        for locator in entry["tests"]:
            path, _, symbol = locator.partition("::")
            require(symbol, f"Test locator must name a collected test: {locator}")
            tree = ast.parse((root / path).read_text(encoding="utf-8"))
            found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for fn in node.body:
                        if isinstance(fn, ast.FunctionDef) and f"{node.name}.{fn.name}" == symbol:
                            found = req["id"] in (ast.get_docstring(fn) or "")
            require(found, f"Missing test or REQ docstring: {req['id']} -> {locator}")
    # Validate the whole suite against C's full registry, even when checking a B proposal subset.
    official = root / "docs/req/requirements.yaml"
    active = read("docs/req/requirements.yaml", root) if official.is_file() else registry
    ids = {r["id"] for r in active}
    require(set(mapping) <= ids, "Test map contains unregistered IDs")
    from tools.integration_checks import check_registered_test_ids
    for path in (root / "test").rglob("test_*.py"):
        for test_node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(test_node, ast.FunctionDef) and test_node.name.startswith("test_"):
                doc = ast.get_docstring(test_node) or ""
                check_registered_test_ids(doc, ids)


def check_history(implementation_parent: str, head: str = "HEAD", root: Path = ROOT) -> None:
    paths = git("diff", "--no-renames", "--name-only", implementation_parent, head, "--", "test/", root=root)
    require(not paths, f"Tests changed during or after implementation: {paths}")


def check_ai_log(before: Any, after: Any, paths: list[str]) -> None:
    relevant = [p for p in paths if is_implementation(p) or p.startswith("test/")
                or p == "docs/req/requirements.yaml"]
    if not relevant:
        return
    require(isinstance(after, list), "AI-use log must be a list")
    require(after[:len(before or [])] == (before or []), "AI-use log is append-only; do not rewrite previous entries")
    ids = [row.get("id") for row in after]
    require(len(ids) == len(set(ids)), "AI-use log entry IDs must be unique")
    previous = {json.dumps(row, sort_keys=True) for row in (before or [])}
    additions = [r for r in after if json.dumps(r, sort_keys=True) not in previous]
    require(additions, "Code/prompt change requires a substantive new AI-use log entry")
    covered: set[str] = set()
    for entry in additions:
        require(all(entry.get(k) for k in ("id", "date", "agent", "purpose", "files", "evidence", "human_review")),
                "Incomplete AI-use log entry")
        require(isinstance(entry["files"], list), "AI-use files must be an exact path list")
        covered.update(entry["files"])
    require(set(relevant) <= covered, f"Unlogged changed files: {sorted(set(relevant) - covered)}")


def check_imports(source: str, component: str) -> None:
    tree = ast.parse(source)
    forbidden = {"grade_store", "subprocess", "os", "pathlib", "importlib", "shutil", "builtins"}
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [x.name.split(".")[0] for x in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [(node.module or "").split(".")[0]]
            names.extend(x.name for x in node.names if x.name in forbidden)
        if component == "feedback_engine":
            require(not (set(names) & forbidden), f"Forbidden feedback import: {names}")
        if component == "score_calculator":
            require(set(names) <= {"decimal", "fractions", "contracts", "typing", "dataclasses", "__future__", "collections"},
                    f"Calculator must remain deterministic: {names}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            require(node.func.id not in {"eval", "exec", "__import__", "open", "compile"},
                    f"Forbidden dynamic/file operation in {component}: {node.func.id}")


class GitHub:
    def __init__(self, repository: str, token: str) -> None:
        require(repository.count("/") == 1, "Expected owner/repository")
        require(token, "GITHUB_TOKEN is required for independently verified review evidence")
        self.repository = repository
        self.token = token

    def get(self, endpoint: str, *, api_version: str = "2026-03-10") -> Any:
        url = f"https://api.github.com/repos/{self.repository}/{endpoint}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": api_version})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)

    def pages(self, endpoint: str) -> list[Any]:
        result: list[Any] = []
        for page in range(1, 101):
            rows = self.get(f"{endpoint}?per_page=100&page={page}")
            require(isinstance(rows, list), "Unexpected GitHub API response")
            result.extend(rows)
            if len(rows) < 100:
                return result
        raise GateError("GitHub pagination limit exceeded; refusing incomplete evidence")


def human_approval(reviews: list[dict[str, Any]], author: str, sha: str,
                   reviewers: list[str]) -> dict[str, Any]:
    latest: dict[str, dict[str, Any]] = {}
    for review in sorted(reviews, key=lambda r: r.get("submitted_at", "")):
        if review.get("state") in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            latest[review["user"]["login"]] = review
    valid = [r for name, r in latest.items() if name in reviewers and name != author
             and r["user"].get("type") == "User" and r.get("state") == "APPROVED"
             and r.get("commit_id") == sha]
    require(valid, "No current independent human approval on the exact head SHA")
    return min(valid, key=lambda r: r["submitted_at"])


def approval_evidence(pr: dict[str, Any], reviews: list[dict[str, Any]],
                      files: list[str], policy: dict[str, Any], first_code_time: str) -> None:
    require(pr.get("merged") is True, "Tests PR was not merged before implementation")
    require(files and any(f.startswith("test/") for f in files), "Tests PR has no tests")
    require(not any(is_implementation(f) and f != "requirements-b-supplement.txt" for f in files), "Tests PR also changes implementation")
    review = human_approval(reviews, pr["user"]["login"], pr["head"]["sha"], policy["reviewers"])
    def parse(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parse(review["submitted_at"]) < parse(first_code_time), "Test approval happened after implementation")
    require(parse(pr["merged_at"]) < parse(first_code_time), "Tests baseline merged after implementation")


def trusted_policy(base: str) -> dict[str, Any]:
    require(git("ls-tree", base, "--", "docs/verification/policy.json"),
            "The base commit has no reviewed governance policy; a human must approve the baseline first")
    policy = base_read("docs/verification/policy.json", base)
    require(policy.get("status") == "active" and policy.get("reviewers"),
            "Human baseline/reviewer allowlist not activated on base branch")
    return dict(policy)


def approved_scope(plan: dict[str, Any], entry: dict[str, Any], files: list[str],
                   reviewed_mapping: dict[str, Any], current_mapping: dict[str, Any]) -> None:
    require(plan.get("implementation_paths") and plan.get("requirement_ids") and plan.get("test_paths"),
            "Reviewed test plan must declare implementation, requirements and tests")
    require(set(entry["implementation_paths"]) <= set(plan["implementation_paths"]),
            "Implementation scope exceeds the reviewed tests plan")
    require(set(entry["requirement_ids"]) <= set(plan["requirement_ids"]),
            "Requirement scope exceeds the reviewed tests plan")
    test_paths = set(plan["test_paths"])
    require(test_paths <= set(files) and all(p.startswith("test/") and p.endswith(".py") for p in test_paths),
            "Reviewed test plan points outside its executable tests in the reviewed PR")
    locators = plan.get("test_locators", {})
    for req_id in entry["requirement_ids"]:
        approved_tests = set(locators.get(req_id, []))
        require(approved_tests and all("::" in test and test.split("::", 1)[0] in test_paths
                                       for test in approved_tests),
                f"{req_id} has no executable locator in the reviewed scope")
        for mapping in (reviewed_mapping, current_mapping):
            require(approved_tests <= set(mapping.get(req_id, {}).get("tests", [])),
                    f"{req_id} lacks the exact reviewed test locators in the requirements map")


def implementation_commits(base: str, paths: list[str]) -> list[str]:
    commits = git("rev-list", "--reverse", "--topo-order", f"{base}..HEAD", "--", *paths).splitlines()
    require(commits, "Cannot establish implementation commit order")
    return commits


def reviewed_merge_sha(api: GitHub, number: int, pr: dict[str, Any]) -> str:
    merge_sha = pr.get("merge_commit_sha")
    if merge_sha is None:
        legacy = api.get(f"pulls/{number}", api_version="2022-11-28")
        require(isinstance(legacy, dict)
                and legacy.get("number") == pr.get("number") == number
                and legacy.get("merged") is True
                and legacy.get("merged_at") == pr["merged_at"]
                and legacy["head"]["sha"] == pr["head"]["sha"]
                and legacy["base"]["ref"] == pr["base"]["ref"],
                "Compatibility response does not match the reviewed tests PR")
        merge_sha = legacy.get("merge_commit_sha")
    require(isinstance(merge_sha, str) and re.fullmatch(r"[0-9a-f]{40}", merge_sha),
            "Verified tests baseline merge SHA is unavailable")
    return str(merge_sha)


def approval_gate(base: str, paths: list[str], api: GitHub) -> None:
    implementations = [p for p in paths if is_implementation(p) and p != "requirements-b-supplement.txt"]
    if not implementations:
        return
    policy = trusted_policy(base)
    commits = implementation_commits(base, implementations)
    parent = git("rev-parse", f"{commits[0]}^")
    check_history(parent)
    times = [git("show", "-s", "--format=%cI", c) for c in commits]
    first_time = min(times, key=lambda s: datetime.fromisoformat(s))
    entries = read("docs/verification/implementation-approvals.json")["approvals"]
    covered: set[str] = set()
    reviewed_tests: set[str] = set()
    map_path = "docs/verification/test-map.yaml"
    current_mapping = read(map_path)
    for entry in entries:
        number = int(entry["test_pr"])
        pr = api.get(f"pulls/{number}")
        require(pr["base"]["ref"] == policy["test_baseline_ref"], "Unapproved tests baseline branch")
        files = [row["filename"] for row in api.pages(f"pulls/{number}/files")]
        approval_evidence(pr, api.pages(f"pulls/{number}/reviews"), files, policy, first_time)
        merge_sha = reviewed_merge_sha(api, number, pr)
        plan_path = entry.get("plan_path", "")
        require(plan_path.startswith("docs/verification/test-plans/") and plan_path.endswith(".json")
                and plan_path in files, "Tests PR must contain the reviewed scope plan")
        require(map_path in files, "Tests PR must contain its reviewed test map")
        approved_scope(base_read(plan_path, merge_sha), entry, files,
                       base_read(map_path, merge_sha), current_mapping)
        require(git("merge-base", parent, merge_sha) == merge_sha,
                "Approved test merge was not an ancestor before the first implementation commit")
        for path in files:
            if path.startswith("test/"):
                require(git("rev-parse", f"HEAD:{path}") == git("rev-parse", f"{merge_sha}:{path}"),
                        f"Approved test changed since review: {path}")
                reviewed_tests.add(path)
        require(entry.get("requirement_ids"), "Approval must name requirement IDs")
        covered.update(entry["implementation_paths"])
    require(set(implementations) <= covered, f"Implementation paths lack prior test approval: {sorted(set(implementations) - covered)}")
    unreviewed = {p for p in paths if p.startswith("test/")} - reviewed_tests
    require(not unreviewed, f"Changed tests lack a previously reviewed baseline: {sorted(unreviewed)}")


def safety_gate(base: str, paths: list[str], api: GitHub | None, pr_number: int) -> None:
    for name in ("feedback_engine", "score_calculator"):
        path = ROOT / f"src/{name}.py"
        require(path.exists(), f"Missing safety component: {path.name}")
        check_imports(path.read_text(encoding="utf-8"), name)
    from tools.integration_checks import public_api
    snapshots = read("docs/verification/api-surface.json")
    for module in ("feedback_engine", "score_calculator", "grade_store", "contracts", "cli"):
        relative = f"src/{module}.py"
        surface = public_api((ROOT / relative).read_text(encoding="utf-8"))
        require(snapshots.get("modules", {}).get(module) == surface, f"API method/signature snapshot mismatch: {module}")
        require(snapshots.get("source_sha256", {}).get(relative) == normalized_sha256(ROOT / relative),
                f"API source fingerprint mismatch: {relative}")
    permissions = read("docs/verification/permissions-snapshot.json")
    digest = normalized_sha256(ROOT / ".opencode/permissions.jsonc")
    require(permissions.get("permissions_sha256") == digest, "Permission snapshot hash mismatch")
    for relative in ("AGENTS.md", ".opencode/permissions.jsonc", ".opencode/rules.md", ".agent/rules.md",
                     "docs/code-governance/structural-constraints.md", "docs/code-governance/mcp-tool-manifest.md"):
        require(permissions.get("policy_files_sha256", {}).get(relative) == normalized_sha256(ROOT / relative),
                f"Governance file fingerprint mismatch: {relative}")
    require(snapshots.get("status") == "reviewed", "API snapshot awaits independent review")
    require(permissions.get("feedback_grade_store_write") is False, "Feedback cannot write grade store")
    require(permissions.get("runtime_enforcement_verified") is True, "E runtime isolation evidence is missing")
    require(permissions.get("tool_manifest_enforcement_verified") is True, "E tool enforcement evidence is missing")
    if pr_number and any(p.startswith(SAFETY) or p in DEPENDENCIES for p in paths):
        require(any(p.startswith("docs/architecture/adr/") and p.endswith(".md") for p in paths), "Safety change requires an accompanying ADR")
        required = {"docs/verification/api-surface.json", "docs/verification/permissions-snapshot.json",
                    "docs/member-b/02-interface-contract.md"}
        require(required <= set(paths), "Safety PR must update contract, API and permission evidence")
        if api is None:
            raise GateError("Review API unavailable")
        pr = api.get(f"pulls/{pr_number}")
        human_approval(api.pages(f"pulls/{pr_number}/reviews"), pr["user"]["login"],
                       pr["head"]["sha"], trusted_policy(base)["reviewers"])


def normalized_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", choices=["proposal", "readiness", "schema", "ai-log", "approval", "safety", "history", "semantic-needed", "coevolution", "secrets"])
    parser.add_argument("--base", default=os.environ.get("BASE_SHA", ""))
    args = parser.parse_args()
    try:
        if args.gate == "proposal":
            data = read("docs/member-b/requirements-proposal.yaml")
            validate_registry(data, read("docs/member-b/proposal-schema.json"), all_types=False)
            traceability(data)
        elif args.gate == "readiness":
            readiness()
        elif args.gate == "schema":
            data = read("docs/req/requirements.yaml")
            validate_registry(data, read("docs/req/req-schema.json"))
            traceability(data)
        elif args.gate == "secrets":
            from tools.integration_checks import scan_secret_files
            paths = [p for p in git("ls-files", "-z").split("\0") if p]
            scan_secret_files(ROOT, paths)
        else:
            require(args.base, "A real base SHA is required; no default HEAD~1 diff")
            paths = changed(args.base)
            if args.gate == "coevolution":
                from tools.integration_checks import check_requirement_coevolution
                check_requirement_coevolution(paths)
            elif args.gate == "ai-log":
                from tools.integration_checks import check_requirement_coevolution
                check_requirement_coevolution(paths)
                check_ai_log(base_read("docs/ai-use-log.yaml", args.base), read("docs/ai-use-log.yaml"), paths)
            elif args.gate == "history":
                implementations = [p for p in paths if is_implementation(p) and p != "requirements-b-supplement.txt"]
                if implementations:
                    first = implementation_commits(args.base, implementations)[0]
                    check_history(git("rev-parse", f"{first}^"))
            elif args.gate == "semantic-needed":
                need = any(p.startswith(("prompts/", "config/", "src/feedback_engine", "scripts/evaluate_live.py", "scripts/live_from_env.py", "test/live/fixed-cases.json", "docs/verification/model-evaluation.json", "test/fixtures/semantic-cases-adr.json")) for p in paths)
                print("true" if need else "false")
                return 0
            else:
                number = int(os.environ.get("PR_NUMBER", "0"))
                api = GitHub(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")) if number else None
                if args.gate == "approval":
                    if number:
                        if api is None:
                            raise GateError("GitHub evidence unavailable")
                        approval_gate(args.base, paths, api)
                    else:
                        require(not any(is_implementation(path) for path in paths),
                                "Implementation changes require a pull request with independent review evidence")
                else:
                    safety_gate(args.base, paths, api, number)
        print(f"PASS {args.gate}")
        return 0
    except (GateError, jsonschema.ValidationError, jsonschema.SchemaError, OSError, ValueError,
            KeyError, TypeError, urllib.error.URLError) as error:
        print(f"BLOCKED {args.gate}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
