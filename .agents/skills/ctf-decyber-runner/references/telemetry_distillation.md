# Telemetry Distillation Reference Guide

This guide defines how to translate raw operational failures into sanitized Violated Invariants.
Never pass raw crash dumps or HTTP 500 error traces to reasoning models.

## 1. Core Distillation Table

| Category | Raw Telemetry from Server | Violated Invariant (Feedback to Solver) |
| :--- | :--- | :--- |
| **Pwn** | `SIGSEGV at 0x7fffffffe000` | `Alignment Invariant: Stack frame address requires 16-byte alignment.` |
| **Pwn** | `*** stack smashing detected ***` | `Canary Invariant: Byte offset 72 overwrote guard value before return.` |
| **Pwn** | `SIGILL (Illegal instruction)` | `Instruction Encoding Invariant: Target stub contained invalid opcode.` |
| **Pwn** | `free(): invalid pointer` | `Allocator Invariant: Pointer offset passed to free was unaligned.` |
| **Web** | `Internal Server Error (500): near 'SELECT'`| `Syntax Grammar Invariant: Delimiter input broke SQL parser at offset 12.`|
| **Web** | `403 Forbidden: Invalid token signature` | `Cryptographic Token Invariant: HMAC signature verification failed.` |
| **Web** | `JSONDecodeError: Unterminated string` | `Serialization Invariant: Unescaped quote character corrupted JSON body.`|
| **Crypto** | `Decryption padding error` | `Oracle Invariant: Block index 3 failed PKCS#7 boundary check.` |
| **Crypto** | `Verification failed: signature mismatch` | `Group Parameter Invariant: Scalar value failed public key verification.`|
| **Network** | `Connection reset by peer` | `Stream Limit Invariant: Input buffer exceeded server socket capacity.` |

---

## 2. Feedback Template for Specialist Subagents

When reporting a failure back to `ctf-decyber-solver`, use this concise format:

```text
The candidate recipe failed with the following distilled invariant:
- Invariant: [Name of Violated Invariant]
- Evidence: [Offset, block index, or delimiter where failure occurred]
- Action Required: Adjust recipe generation logic to preserve this constraint.
```
