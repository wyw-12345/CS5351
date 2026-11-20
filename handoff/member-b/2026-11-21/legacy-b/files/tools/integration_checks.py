"""ADR-B0005 proposed structural checks; no runtime authority or approval is granted."""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from tools.gates import GateError, require


def check_requirement_coevolution(paths: list[str]) -> None:
    """REQ-GOV-C01: a registry change updates its actual dependent artifacts."""
    if "docs/req/requirements.yaml" not in paths:
        return
    needed = {"docs/req/requirement-id-map.yaml", "docs/architecture/trace-matrix.md",
              "docs/verification/test-map.yaml", "docs/ai-use-log.yaml"}
    require(needed <= set(paths), f"Requirement change lacks co-evolution files: {sorted(needed - set(paths))}")
    require(any(p.startswith("test/") and p.endswith(".py") for p in paths),
            "Requirement change must update affected executable tests")


def check_registered_test_ids(docstring: str, allowed_ids: set[str]) -> None:
    """REQ-GOV-C02: exact IDs, not substring matches or mixed registered/unknown IDs."""
    found = set(re.findall(r"\bREQ-[A-Z]+-[A-Za-z0-9]+\b", docstring))
    require(found, "Test must name an explicit registered requirement")
    require(found <= allowed_ids, f"Unregistered requirement IDs: {sorted(found - allowed_ids)}")


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    args = node.args
    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)

    def parameter(arg: ast.arg, default: ast.expr | None, kind: str) -> dict[str, Any]:
        return {"name": arg.arg, "kind": kind,
                "annotation": ast.unparse(arg.annotation) if arg.annotation else None,
                "default": ast.unparse(default) if default is not None else None}

    fields = [parameter(arg, default, "positional_only" if i < len(args.posonlyargs) else "positional")
              for i, (arg, default) in enumerate(zip(positional, defaults))]
    if args.vararg:
        fields.append(parameter(args.vararg, None, "vararg"))
    fields.extend(parameter(arg, default, "keyword_only")
                  for arg, default in zip(args.kwonlyargs, args.kw_defaults))
    if args.kwarg:
        fields.append(parameter(args.kwarg, None, "kwargs"))
    return {"parameters": fields, "returns": ast.unparse(node.returns) if node.returns else None,
            "async": isinstance(node, ast.AsyncFunctionDef)}


def public_api(source_text: str) -> dict[str, Any]:
    """REQ-GOV-B02/E03: snapshot constructors, public methods and function signatures."""
    result: dict[str, Any] = {}
    for node in ast.parse(source_text).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            result[node.name] = {"signature": _signature(node), "methods": {}}
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            methods = {m.name: {"signature": _signature(m)} for m in node.body
                       if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and (not m.name.startswith("_") or m.name == "__init__")}
            fields = {m.target.id: ast.unparse(m.annotation) for m in node.body
                      if isinstance(m, ast.AnnAssign) and isinstance(m.target, ast.Name)
                      and not m.target.id.startswith("_")}
            result[node.name] = {"signature": {"bases": [ast.unparse(x) for x in node.bases]},
                                 "methods": methods, "fields": fields}
    return result


SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def check_secret_text(text: str, label: str = "source") -> None:
    """REQ-SEC-004: never echo the matched token in diagnostics."""
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        raise GateError(f"Secret pattern detected in {label}; value redacted")


def scan_secret_files(root: Path, paths: list[str]) -> None:
    """Scan explicit tracked text inputs; credential files are refused without being read."""
    for rel in paths:
        path = (root / rel).resolve()
        require(path.is_relative_to(root.resolve()), "Secret scan path escaped project root")
        if path.name == ".env" or path.suffix in {".pem", ".key"}:
            raise GateError(f"Credential material must not be tracked: {rel}")
        if not path.is_file() or path.suffix not in {".py", ".md", ".json", ".yaml", ".yml", ".txt", ".toml", ".ps1", ".jsonc"}:
            continue
        require(path.stat().st_size <= 5_000_000, f"Oversized text needs explicit secret review: {rel}")
        check_secret_text(path.read_text(encoding="utf-8"), label=rel)
