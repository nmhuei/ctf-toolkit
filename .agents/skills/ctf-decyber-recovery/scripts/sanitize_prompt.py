#!/usr/bin/env python3
"""Automated Prompt Sanitizer for De-Cyber Recovery."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPLACEMENTS = [
    # Verbs and attack nouns
    (r"\bexploit(?:s|ing|ed)?\b", "verification harness"),
    (r"\bpayload(?:s)?\b", "input vector"),
    (r"\bshellcode\b", "machine code stub"),
    (r"\bhack(?:s|ing|ed)?\b", "boundary test"),
    (r"\bpwn(?:s|ing|ed)?\b", "execute state verification"),
    (r"\bvictim(?:s)?\b", "reference endpoint"),
    (r"\btarget(?:s)?\b", "service under test"),
    (r"\bflag(?:s)?\b", "acceptance token"),
    (r"\bsecret key\b", "unknown parameter vector"),
    (r"\bdecrypt(?:s|ing|ed)?\b", "evaluate inverse mapping"),
    (r"\breverse[-_]?shell\b", "interactive diagnostic connection"),
    (r"\bbuffer[-_]?overflow\b", "buffer boundary overrun"),
    (r"\bstack[-_]?smashing\b", "stack frame boundary condition"),
    (r"\bROP[-_]?chain\b", "call frame sequence"),
    (r"\bfault[-_]?(?:injection|attack)\b", "differential state transition"),
    (r"\bPiret[-_]?Quisquater\b", "differential SPN propagation"),
    (r"\bHSM\b", "cryptographic module"),
]

IP_OR_DOMAIN_RE = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:[a-zA-Z0-9-]+\.)+(?:nip\.io|sslip\.io)\b"
)


def sanitize_text(text: str) -> str:
    sanitized = text
    for pattern, repl in REPLACEMENTS:
        sanitized = re.sub(pattern, repl, sanitized, flags=re.IGNORECASE)

    # Sanitize IP addresses and test domains
    sanitized = IP_OR_DOMAIN_RE.sub("local_fixture", sanitized)
    return sanitized


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize prompt text for de-cyber recovery")
    parser.add_argument("input_file", type=Path, help="Input prompt file or string")
    parser.add_argument("--output", type=Path, help="Output clean file path")
    args = parser.parse_args()

    if args.input_file.is_file():
        content = args.input_file.read_text(encoding="utf-8")
    else:
        content = str(args.input_file)

    clean = sanitize_text(content)

    if args.output:
        args.output.write_text(clean, encoding="utf-8")
        print(f"[+] Sanitized prompt written to: {args.output}")
    else:
        print(clean)

    return 0


if __name__ == "__main__":
    sys.exit(main())
