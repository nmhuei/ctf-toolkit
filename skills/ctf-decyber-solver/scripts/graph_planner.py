#!/usr/bin/env python3
"""Dependency Graph Planner and Reachability Analyzer (ASD-STE100)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class ActionOperator:
    def __init__(self, name: str, preconditions: set[str], postconditions: set[str]):
        self.name = name
        self.preconditions = preconditions
        self.postconditions = postconditions


class DependencyGraph:
    def __init__(self, known_facts: set[str], target_goal: str):
        self.known_facts = set(known_facts)
        self.target_goal = target_goal
        self.operators: list[ActionOperator] = []

    def add_operator(self, name: str, pre: list[str], post: list[str]):
        self.operators.append(ActionOperator(name, set(pre), set(post)))

    def solve(self) -> tuple[bool, list[str] | set[str]]:
        """Evaluate graph reachability and identify missing preconditions."""
        current = set(self.known_facts)
        plan = []
        progress = True

        while progress:
            progress = False
            for op in self.operators:
                if op.name not in plan and op.preconditions.issubset(current):
                    current.update(op.postconditions)
                    plan.append(op.name)
                    progress = True
                    if self.target_goal in current:
                        return True, plan

        # Goal is unreachable: find missing preconditions via backward regression
        missing = set()
        for op in self.operators:
            if self.target_goal in op.postconditions:
                unmet = op.preconditions - current
                if unmet:
                    missing.update(unmet)

        if not missing:
            # Fallback: check any operator that expands frontier towards goal
            missing = {self.target_goal}

        return False, missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Dependency Graph Planner")
    parser.add_argument("--facts", nargs="+", default=[], help="Initial known facts")
    parser.add_argument("--goal", default="SINK_REACHED", help="Target goal state")
    parser.add_argument("--operators-json", type=Path, help="JSON file defining operators")
    args = parser.parse_args()

    graph = DependencyGraph(set(args.facts), args.goal)

    if args.operators_json and args.operators_json.is_file():
        ops_data = json.loads(args.operators_json.read_text(encoding="utf-8"))
        for item in ops_data:
            graph.add_operator(item["name"], item["preconditions"], item["postconditions"])
    else:
        # Default standard protocol verification operators
        graph.add_operator(
            "resolve_offset",
            ["BUFFER_OVERRUN_FEASIBLE"],
            ["OFFSET_RESOLVED"]
        )
        graph.add_operator(
            "resolve_runtime_base",
            ["POINTER_LEAK_OBSERVED"],
            ["IMAGE_BASE_RESOLVED"]
        )
        graph.add_operator(
            "redirect_control_flow",
            ["OFFSET_RESOLVED", "IMAGE_BASE_RESOLVED"],
            ["SINK_REACHED"]
        )

    reachable, result = graph.solve()
    if reachable:
        print("[+] Goal is reachable. Solution plan sequence:")
        for idx, step in enumerate(result, 1):
            print(f"  {idx}. {step}")
        return 0
    else:
        print("[-] Goal is UNREACHABLE. Missing Precondition Gap:")
        for missing in sorted(result):
            print(f"  * {missing}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
