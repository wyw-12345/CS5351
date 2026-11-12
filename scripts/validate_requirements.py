"""C's D1 validation helper: registry schema, seven types, ID-map coverage, traceability status.

This is intentionally separate from tools/gates.py. The course gate remains the authority
for CI; this script produces a readable local report and does not modify the registry.

Exit codes:
  0 = registry/schema/ID-map structure valid (traceability may still be incomplete)
  1 = structural validation failure
  2 = structural validation passed but traceability is incomplete and --strict was requested
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TYPES = {
    "functional",
    "invariant",
    "quality",
    "performance",
    "cost",
    "governance",
    "security",
}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_structure() -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    registry = load_yaml(ROOT / "docs/req/requirements.yaml")
    schema = json.loads((ROOT / "docs/req/req-schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    try:
        jsonschema.validate(registry, schema)
    except jsonschema.ValidationError as exc:
        errors.append(f"schema validation failed: {exc.message} at {list(exc.absolute_path)}")

    if not isinstance(registry, list) or not registry:
        errors.append("registry must be a nonempty list")
        return registry, errors

    ids = [item.get("id") for item in registry]
    if len(ids) != len(set(ids)):
        errors.append("duplicate requirement IDs")
    types = {item.get("type") for item in registry}
    missing_types = REQUIRED_TYPES - types
    if missing_types:
        errors.append(f"missing requirement types: {sorted(missing_types)}")

    for item in registry:
        if item.get("type") == "invariant" and item.get("fit_criterion", {}).get("threshold") not in (0, "0", "zero escapes"):
            errors.append(f"{item.get('id')}: invariant threshold is not zero-tolerance")

    id_map = load_yaml(ROOT / "docs/req/requirement-id-map.yaml")
    mapped_ids = {
        entry.get("formal_id")
        for entry in id_map.get("mappings", [])
        if entry.get("formal_id")
    } | {entry.get("formal_id") for entry in id_map.get("new_requirements", []) if entry.get("formal_id")}
    unmapped = sorted(set(ids) - mapped_ids)
    if unmapped:
        errors.append(f"formal IDs absent from requirement-id-map.yaml: {unmapped}")

    proposals = [
        entry.get("proposal_id")
        for entry in id_map.get("mappings", [])
        if entry.get("proposal_id")
    ]
    if len(proposals) != len(set(proposals)):
        errors.append("duplicate proposal IDs in requirement-id-map.yaml")
    if len(proposals) != id_map.get("summary", {}).get("source_proposals"):
        errors.append(
            "source_proposals summary does not match mappings: "
            f"{len(proposals)} != {id_map.get('summary', {}).get('source_proposals')}"
        )

    return registry, errors


def traceability_status(registry: list[dict[str, Any]]) -> dict[str, Any]:
    test_map = load_yaml(ROOT / "docs/verification/test-map.yaml") or {}
    ids = [item["id"] for item in registry]
    mapped = [rid for rid in ids if test_map.get(rid, {}).get("tests")]
    missing = [rid for rid in ids if rid not in mapped]
    function_docstring_ok: dict[str, bool] = {}
    for rid in mapped:
        ok = False
        for locator in test_map[rid]["tests"]:
            path_text, _, symbol = locator.partition("::")
            path = ROOT / path_text
            if not path.exists() or not symbol:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for fn in node.body:
                        if isinstance(fn, ast.FunctionDef) and f"{node.name}.{fn.name}" == symbol:
                            if rid in (ast.get_docstring(fn) or ""):
                                ok = True
        function_docstring_ok[rid] = ok
    tests_without_req = []
    for path in (ROOT / "test").rglob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                doc = ast.get_docstring(node) or ""
                if not any(rid in doc for rid in ids):
                    tests_without_req.append(f"{path.relative_to(ROOT)}::{node.name}")
    return {
        "registry_ids": len(ids),
        "mapped_ids": len(mapped),
        "unmapped_ids": missing,
        "mapped_but_missing_function_docstring": [
            rid for rid, ok in function_docstring_ok.items() if not ok
        ],
        "tests_without_registered_req_docstring": tests_without_req,
        "complete": not missing and not any(not ok for ok in function_docstring_ok.values()) and not tests_without_req,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="exit 2 when traceability is incomplete")
    parser.add_argument("--json", action="store_true", help="print JSON only")
    args = parser.parse_args()

    registry, errors = validate_structure()
    report: dict[str, Any] = {
        "command": "scripts/validate_requirements.py",
        "date": "2026-11-12",
        "registry": "docs/req/requirements.yaml",
        "schema": "docs/req/req-schema.json",
        "schema_and_registry_status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "counts": {
            "requirements": len(registry) if isinstance(registry, list) else 0,
            "types": sorted({item.get("type") for item in registry}) if isinstance(registry, list) else [],
        },
    }
    if not errors and isinstance(registry, list):
        report["traceability"] = traceability_status(registry)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["schema_and_registry_status"])
        for error in errors:
            print(f"ERROR {error}")
        if "traceability" in report:
            trace = report["traceability"]
            print(f"TRACEABILITY {'PASS' if trace['complete'] else 'INCOMPLETE'}")
            print(f"  mapped {trace['mapped_ids']}/{trace['registry_ids']}")
            if trace["unmapped_ids"]:
                print("  unmapped: " + ", ".join(trace["unmapped_ids"]))
            if trace["tests_without_registered_req_docstring"]:
                print(f"  tests missing REQ docstrings: {len(trace['tests_without_registered_req_docstring'])}")
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if errors:
        return 1
    if args.strict and not report.get("traceability", {}).get("complete"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
