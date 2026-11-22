"""Review E's declared controls using inert examples, without invoking OpenCode tools."""

import json
import re
import unittest
from pathlib import Path

from tools.gates import normalized_sha256, read

ROOT = Path(__file__).resolve().parents[2]
PERMISSIONS = ".opencode/permissions.jsonc"


def declared_config():
    # This project file has standalone line comments and no inline comments.
    return json.loads(re.sub(r"^\s*//[^\n]*", "", (ROOT / PERMISSIONS).read_text(encoding="utf-8"),
                             flags=re.MULTILINE))


def effect(rules, action, resource):
    """Check this file's documented ordered matching, without executing any action."""
    for rule in reversed(rules):
        pattern = re.escape(rule["resource"]).replace(r"\*", ".*").replace(r"\?", ".")
        if rule["action"] == action and re.fullmatch(pattern, resource):
            return rule["effect"]
    return "ask"


class EControlReadbackTests(unittest.TestCase):
    def test_protected_defaults_match_the_declared_permission_policy(self):
        """REQ-GOV-E01: byte-bound E policy should enforce its declared protection precedence."""
        snapshot = read("docs/verification/permissions-snapshot.json", ROOT)
        self.assertEqual(snapshot["permissions_sha256"], normalized_sha256(ROOT / PERMISSIONS))
        rules = declared_config()["permissions"]
        cases = [("read", "examples/fictional.env"), ("edit", "docs/verification/fixture.json"),
                 ("edit", "src/score_calculator.py")]
        for action, resource in cases:
            with self.subTest(action=action, resource=resource):
                self.assertEqual(effect(rules, action, resource), "deny")

    def test_frozen_calculator_has_owners_from_the_active_policy(self):
        """REQ-GOV-E02: active reviewer identities, frozen path owners and deny-edit rule agree."""
        policy = read("docs/verification/policy.json", ROOT)
        self.assertEqual(policy["status"], "active")
        path = "src/score_calculator.py"
        owners = []
        for line in (ROOT / ".github/CODEOWNERS").read_text(encoding="utf-8").splitlines():
            words = line.split()
            if words and words[0] == f"/{path}":
                owners.extend(words[1:])
        self.assertTrue(owners)
        self.assertEqual(set(owners), {f"@{name}" for name in policy["reviewers"]})
        self.assertEqual(effect(declared_config()["permissions"], "edit", path), "deny")

    def test_verify_role_denies_commands_outside_the_declared_surface(self):
        """REQ-GOV-E04: unlisted and role-inappropriate operations must resolve to deny."""
        config = declared_config()
        rules = config["permissions"] + config["agents"]["verify"]["permissions"]
        self.assertEqual(effect(rules, "edit", "examples/fictional.txt"), "deny")
        self.assertEqual(effect(rules, "shell", "python -m unittest"), "allow")
        for specimen in ("fictional_unlisted_command", "python tools/fictional_unlisted.py"):
            with self.subTest(command=specimen):
                self.assertEqual(effect(rules, "shell", specimen), "deny")
