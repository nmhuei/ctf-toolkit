---
name: ctf-decyber-formalizer
description: Ingests raw CTF challenges and produces sanitized Formal Task Descriptors and TASK.md documents. Use to decouple computational constraints from live network endpoints and offensive keywords.
---

# De-Cyber Formalizer: Problem Intake & Schema Generation

## 1. Overview

The Formalizer translates raw challenge files into a **Formal Task Descriptor** (`task_descriptor.json`) and a clean specification (`TASK.md`).
This step isolates sensitive operational details (endpoints, credentials, offensive buzzwords) before delegating to reasoning agents.

```
┌─────────────────────────────────────────────────────────────┐
│                      FORMALIZER PIPELINE                    │
├─────────────────────────────────────────────────────────────┤
│ Raw Challenge Files ───────► 1. Strip Offensive Jargon      │
│ (Binaries, Scripts, PCAPs)   2. Quarantine Remote Endpoints │
│                              3. Extract Concrete Bounds     │
│                              4. Generate Schema Descriptors │
│                                      │                      │
│                                      ▼                      │
│                          task_descriptor.json + TASK.md     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. When to Use

- Use immediately upon selecting a challenge that requires non-trivial algorithmic, cryptographic, or reverse-engineering work.
- Use whenever challenge descriptions contain raw URLs (`.nip.io`), IPs, or attack nouns (`exploit`, `payload`).
- Do NOT use for simple single-command triage tasks (e.g., `file`, `strings`, `exiftool`).

---

## 3. The 4-Step Formalization Protocol

### Step 1: Scan and Inventory Assets
Inspect local challenge directory (`challenge/` and `script/`):
- Identify files: binary executables, Python scripts, PCAP traces, or data files.
- Read `metadata.json` and `challenge/NOTE.md` locally.
- Do NOT transmit raw challenge descriptions to external LLMs.

### Step 2: Quarantine Network Endpoints
Move all live connection data to `metadata.json`:
- Replace raw IPs (`10.0.0.5`) with `"local_fixture"`.
- Replace dynamic DNS (`xyz.nip.io`) with `"remote_service"`.
- Store ports and TLS settings in local configuration only.
- Ensure the formal descriptor contains zero network connection strings.

### Step 3: Extract Concrete Systems Invariants
Identify technical constraints while preserving execution fidelity:
- **Bitwidths & Offsets**: Buffer size (e.g., 64 bytes), offset to instruction pointer (e.g., 72 bytes).
- **Endianness**: Pack formats (`<I`, `>Q`).
- **State Space**: Permutation dimensions ($16 \times 16$), modulus ($p = 2^{255}-19$).
- **Delimiter Sequences**: Line endings (`\n`, `\r\n`), packet header offsets.

### Step 4: Write Formal Deliverables
Generate two files in the workspace's `script/` directory:
1. `task_descriptor.json`: Machine-readable JSON contract.
2. `TASK.md`: Human/LLM-readable specification written in ASD-STE100 Systems Software terminology.

Validate the generated files using:
```bash
python3 .agents/skills/ctf-decyber-formalizer/scripts/validate_task_descriptor.py script/task_descriptor.json
```

---

## 4. Formal Task Descriptor Schema

```json
{
  "task_id": "challenge_unique_slug",
  "category": "pwn|rev|crypto|web|network|forensics",
  "objective": "Derive input sequence satisfying target predicate",
  "data_invariants": {
    "endianness": "little",
    "word_size": 64,
    "buffer_capacity": 64,
    "target_offset": 72
  },
  "function_contract": {
    "name": "solve_model",
    "inputs": {"state_vector": "list[int]"},
    "output_type": "bytes"
  },
  "artifacts": [
    "observations.json"
  ]
}
```

---

## 5. Supporting Files

- `templates/task_descriptor.json`: Canonical schema template.
- `templates/TASK_template.md`: Formal specification markdown template.
- `scripts/validate_task_descriptor.py`: Schema validator and forbidden word scanner.
- `references/planning_graph.md`: Planning Graph & Dependency Modeling guide.
