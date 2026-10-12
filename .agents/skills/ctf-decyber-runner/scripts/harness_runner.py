#!/usr/bin/env python3
"""Operational Harness Runner with Closed-Loop Telemetry Distillation."""

from __future__ import annotations

import argparse
import re
import socket
import sys
from pathlib import Path


def distill_raw_error(raw_text: str) -> str:
    """Translate raw server error or crash into a clean Violated Invariant."""
    lowered = raw_text.lower()
    if "syntax error" in lowered or "near '" in lowered:
        return "Grammar Boundary Invariant: Delimiter syntax rejected by parser."
    if "sigsegv" in lowered or "segmentation fault" in lowered:
        return "Memory Alignment Invariant: Unaligned pointer or invalid return address."
    if "padding" in lowered and "invalid" in lowered:
        return "Encoding Invariant: Block delimiter failed padding check."
    if "connection reset" in lowered or "broken pipe" in lowered:
        return "Stream Boundary Invariant: Length exceeded remote buffer ceiling."
    if "bad key" in lowered or "authentication failed" in lowered:
        return "Credential Invariant: Candidate parameter failed validation check."

    # Generic sanitized fallback
    return f"Execution Invariant Failed: Service returned unparseable response ({len(raw_text)} bytes)."


def run_tcp_harness(host: str, port: int, payload: bytes, timeout: float = 10.0) -> tuple[bool, str]:
    """Execute socket communication with timeout handling."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        sock.sendall(payload)
        chunks = []
        while True:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
            except socket.timeout:
                break
        response = b"".join(chunks).decode("utf-8", errors="replace")
        return True, response
    except Exception as exc:
        return False, str(exc)
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Operational Harness Runner")
    parser.add_argument("--host", default="127.0.0.1", help="Target host")
    parser.add_argument("--port", type=int, default=1337, help="Target port")
    parser.add_argument("--payload-file", type=Path, help="File containing byte payload")
    parser.add_argument("--distill-error", type=str, help="Distill raw error string directly")
    args = parser.parse_args()

    if args.distill_error:
        distilled = distill_raw_error(args.distill_error)
        print(f"[!] Distilled Feedback: {distilled}")
        return 0

    if not args.payload_file or not args.payload_file.is_file():
        print("[-] Error: Payload file required", file=sys.stderr)
        return 1

    payload = args.payload_file.read_bytes()
    success, resp = run_tcp_harness(args.host, args.port, payload)

    flag_match = re.search(r"FLAG\{[^\}]+\}", resp)
    if flag_match:
        print(f"[+] Verified acceptance token found: {flag_match.group(0)}")
        return 0

    if not success:
        print(f"[-] Distilled Telemetry: {distill_raw_error(resp)}")
        return 1

    print(f"[*] Response received ({len(resp)} bytes). No flag pattern matched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
