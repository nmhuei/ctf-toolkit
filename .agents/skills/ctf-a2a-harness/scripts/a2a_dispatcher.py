#!/usr/bin/env python3
"""A2A Dispatcher and Recipe Tester for CTF Dual-Tier Harness.

Validates Formal Task Descriptors, runs offline recipe self-checks,
and stitches the Specialist's recipe into the live operational runner.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def validate_descriptor(descriptor_path: Path) -> dict:
    """Validate formal task descriptor schema."""
    if not descriptor_path.is_file():
        raise FileNotFoundError(f"Descriptor not found: {descriptor_path}")
    data = json.loads(descriptor_path.read_text(encoding="utf-8"))
    required = ("task_id", "category", "target_predicate", "function_contract")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Task descriptor missing required keys: {missing}")
    return data


def test_recipe(recipe_path: Path, sample_input: dict) -> bool:
    """Execute recipe module in isolation against sample input."""
    if not recipe_path.is_file():
        raise FileNotFoundError(f"Recipe file not found: {recipe_path}")

    spec = importlib.util.spec_from_file_location("recipe_module", recipe_path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load recipe from {recipe_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if not hasattr(mod, "solve_model"):
        raise AttributeError("Recipe missing mandatory 'solve_model' function")

    result = mod.solve_model(sample_input)
    print(f"[+] Recipe self-check passed. Result preview: {repr(result)[:80]}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="A2A Harness Dispatcher & Tester")
    subparsers = parser.add_subparsers(dest="command", required=True)

    v_p = subparsers.add_parser("validate", help="Validate task descriptor")
    v_p.add_argument("descriptor", type=Path, help="Path to task_descriptor.json")

    t_p = subparsers.add_parser("test", help="Test solver recipe")
    t_p.add_argument("recipe", type=Path, help="Path to recipe.py")
    t_p.add_argument("--input-json", type=Path, help="Path to sample inputs JSON")

    args = parser.parse_args()

    if args.command == "validate":
        validate_descriptor(args.descriptor)
        print(f"[+] Formal Task Descriptor '{args.descriptor.name}' is valid.")
        return 0
    elif args.command == "test":
        inp = json.loads(args.input_json.read_text()) if args.input_json else {}
        test_recipe(args.recipe, inp)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
