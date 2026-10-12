#!/usr/bin/env python3
"""Validate Task Descriptors for De-Cyber compliance."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

FORBIDDEN_TERMS = {
    "exploit",
    "payload",
    "shellcode",
    "reverse-shell",
    "reverse_shell",
    "pwn",
    "hack",
    "victim",
    "target-ip",
    "piret-quisquater",
    "fault-attack",
    "fault_injection",
    "side-channel",
    "malware",
    "ransomware",
    "keylogger",
}

IP_OR_DOMAIN_RE = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:[a-zA-Z0-9-]+\.)+(?:nip\.io|sslip\.io)\b"
)


def extract_strings(obj: Any) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, list):
        return [s for item in obj for s in extract_strings(item)]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in extract_strings(v)]
    return []


def validate(descriptor_path: Path) -> list[str]:
    if not descriptor_path.is_file():
        return [f"File not found: {descriptor_path}"]

    try:
        data = json.loads(descriptor_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: {exc}"]

    errors = []
    required_keys = ("task_id", "category", "objective", "data_invariants", "function_contract")
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required key: '{key}'")

    all_strings = extract_strings(data)
    combined_text = " ".join(all_strings).lower()

    for term in FORBIDDEN_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", combined_text):
            errors.append(f"Contains forbidden attack term: '{term}'")

    matches = IP_OR_DOMAIN_RE.findall(combined_text)
    if matches:
        errors.append(f"Contains forbidden IP or dynamic DNS endpoint: {matches}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Task Descriptor")
    parser.add_argument("descriptor", type=Path, help="Path to task_descriptor.json")
    args = parser.parse_args()

    errors = validate(args.descriptor)
    if errors:
        for err in errors:
            print(f"[-] ERROR: {err}", file=sys.stderr)
        return 1

    print(f"[+] Task Descriptor '{args.descriptor.name}' is valid and sanitized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
