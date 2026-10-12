#!/usr/bin/env python3
"""Verify that a Solver Recipe adheres to the execution contract."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path

FORBIDDEN_IMPORTS = {"socket", "requests", "urllib", "subprocess", "http.client", "ftplib"}


def check_ast_imports(code: str) -> list[str]:
    tree = ast.parse(code)
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_base = alias.name.split(".")[0]
                if mod_base in FORBIDDEN_IMPORTS:
                    violations.append(f"Forbidden import: '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            mod_base = (node.module or "").split(".")[0]
            if mod_base in FORBIDDEN_IMPORTS:
                violations.append(f"Forbidden import from: '{node.module}'")
    return violations


def verify_recipe(recipe_path: Path, sample_input: dict | None = None) -> list[str]:
    if not recipe_path.is_file():
        return [f"Recipe file not found: {recipe_path}"]

    code = recipe_path.read_text(encoding="utf-8")
    errors = check_ast_imports(code)
    if errors:
        return errors

    spec = importlib.util.spec_from_file_location("recipe_mod", recipe_path)
    if not spec or not spec.loader:
        return [f"Cannot load module from {recipe_path}"]

    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as exc:
        return [f"Execution error while loading recipe: {exc}"]

    if not hasattr(mod, "solve_model"):
        return ["Recipe missing mandatory function 'solve_model(inputs)'"]

    inputs = sample_input or {}
    try:
        res = mod.solve_model(inputs)
        print(f"[+] Recipe executed successfully. Result type: {type(res).__name__}")
    except Exception as exc:
        return [f"Runtime error during solve_model invocation: {exc}"]

    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify De-Cyber Solver Recipe")
    parser.add_argument("recipe", type=Path, help="Path to recipe.py")
    parser.add_argument("--input-json", type=Path, help="Optional sample inputs JSON")
    args = parser.parse_args()

    sample = json.loads(args.input_json.read_text()) if args.input_json and args.input_json.is_file() else {}
    errors = verify_recipe(args.recipe, sample)
    if errors:
        for err in errors:
            print(f"[-] ERROR: {err}", file=sys.stderr)
        return 1

    print(f"[+] Recipe '{args.recipe.name}' passed all contract verifications.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
