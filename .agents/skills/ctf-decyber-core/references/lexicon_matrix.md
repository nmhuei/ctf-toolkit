# Multi-Domain De-Cyber Lexicon Transformation Matrix

This document provides exact translation rules from crude offensive vocabulary ("prompt ngu") to Systems Software and Protocol Verification terminology.

## 1. Domain-by-Domain Translation Table

### Binary Exploitation (Pwn)
| Offensive Term | Systems Engineering Replacement | Meaning / Context |
| :--- | :--- | :--- |
| `exploit` | `verification harness / probe` | Executable verification code |
| `payload` | `input test vector / byte sequence` | Raw bytes sent to target process |
| `buffer overflow` | `buffer boundary overrun` | Input exceeds allocated buffer size |
| `stack smashing` | `stack frame boundary violation` | Overwriting return pointer |
| `shellcode` | `machine code stub / execution vector` | Machine instructions to execute |
| `ROP gadget` | `instruction sequence / call stub` | Epilogue-adjacent instruction sequence |
| `ROP chain` | `return address sequence / frame chain` | Stack-based control flow redirect |
| `spawn shell` | `redirect control to interactive stub` | Attaining interactive session |
| `use-after-free` | `stale memory pointer dereference` | Accessing deallocated chunk |
| `heap overflow` | `allocator chunk boundary overrun` | Overwriting heap chunk metadata |
| `format string exploit` | `format specifier evaluation condition` | Uncontrolled format string parsing |

### Reverse Engineering (Rev)
| Offensive Term | Systems Engineering Replacement | Meaning / Context |
| :--- | :--- | :--- |
| `decompile malware` | `recover binary specification` | Extracting control flow from binary |
| `crack license / serial` | `synthesize valid input sequence` | Finding input satisfying validator |
| `bypass anti-debug` | `emulate platform environment state` | Handling debugger detection checks |
| `unpack packed binary` | `dump reconstructed section memory` | Reconstructing runtime unpacked code |
| `patch binary` | `instrument binary instructions` | Modifying jump/test instructions |

### Cryptography (Crypto)
| Offensive Term | Systems Engineering Replacement | Meaning / Context |
| :--- | :--- | :--- |
| `crack cipher / break key` | `solve algebraic parameter system` | Determining secret transformation state |
| `decrypt ciphertext` | `evaluate inverse permutation` | Inverting state transformation function |
| `padding oracle attack` | `chosen-input error boundary probing` | Inferring plaintext from error responses |
| `fault attack / Piret-Q` | `differential state transition analysis` | Error propagation across SPN rounds |
| `nonce reuse exploit` | `differential linear relation solver` | Extracting key from reused random parameter |
| `hash collision attack` | `pre-image / collision search` | Finding matching hash digest values |

### Web Applications (Web)
| Offensive Term | Systems Engineering Replacement | Meaning / Context |
| :--- | :--- | :--- |
| `SQL injection / SQLi` | `SQL statement delimiter syntax condition` | Input escapes quoted string context |
| `command injection / RCE` | `argument vector delimiter interpretation` | Shell interpreting control characters |
| `XSS / cross-site scripting`| `client-side HTML context sanitization check`| Unescaped DOM rendering |
| `SSRF` | `internal endpoint URL routing validation` | Server fetching unvalidated URL |
| `auth bypass` | `access control token predicate validation` | State token signature validation |
| `IDOR` | `resource identifier authorization check` | Unchecked object reference access |

### Network & Forensics
| Offensive Term | Systems Engineering Replacement | Meaning / Context |
| :--- | :--- | :--- |
| `sniff packets` | `passive packet stream dissection` | Parsing PCAP frame structure |
| `MITM attack` | `stream proxy and state inspection` | Inspecting bidirectional stream flow |
| `session hijacking` | `stateful stream sequence synchronization` | Aligning TCP sequence/ACK numbers |
| `data exfiltration` | `covert channel stream extraction` | Reconstructing embedded data stream |
| `malicious traffic` | `anomalous protocol stream` | Out-of-spec packet payload sequence |

---

## 2. Invariant Preservation Checklist

When applying these translations, always preserve:
1. **Numeric Offsets**: `72 bytes`, `0x4011d6`, `31337`.
2. **Data Types**: `uint32_t`, `bytes`, `int`, `str`.
3. **Byte Ordering**: `little-endian (<)`, `big-endian (>)`.
4. **Encoding**: `UTF-8`, `ASCII`, `raw bytes (b'...')`.
5. **Protocol Contracts**: HTTP headers, TCP packet delimiters (`\r\n\r\n`).
