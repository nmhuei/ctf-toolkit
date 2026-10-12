# Backward Goal-Regression from Canonical Sinks (ASD-STE100)

## 1. Overview
When the exact location of the target artifact is unknown, trace backward from **Canonical I/O Sinks**.
Do not search file systems blindly.
Analyze output channels to identify required preconditions.

```
┌─────────────────────────────────────────────────────────────┐
│                 THE 3 CANONICAL SINK MODELS                 │
├─────────────────────────────────────────────────────────────┤
│ 1. Predicate Branch Sink    │ Code branch prints output     │
│ 2. File / Process Sink      │ Read file or spawn diagnostic │
│ 3. Mathematical Pre-image   │ Invert output transformation  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Sink Model 1: Predicate Branch in Code

Use when the program contains logic to print the acceptance token.

### Execution Steps:
1. Scan binary or source code for output calls (`printf`, `puts`, `write`, `send`).
2. Trace cross-references (Xrefs) backward to find the enclosing basic block.
3. Identify the conditional jump leading to this block (e.g., `cmp eax, ebx; jz target`).
4. Derive the input constraints required to satisfy `eax == ebx`.
5. Solve constraints with SMT or Z3.

---

## 3. Sink Model 2: File System & Process Sink

Use when the token resides in an external file or environment variable.

### Execution Steps:
1. Identify code paths capable of reading external data (`fopen`, `open`, `read`, `execve`).
2. Determine if user input reaches the file path argument (path parameter).
3. If path parameter is controllable:
   - Construct path traversal or direct file reference.
4. If path parameter is not controllable:
   - Identify memory corruption or control-flow redirection operators.
   - Redirect execution flow to process spawning primitives.

---

## 4. Sink Model 3: Mathematical Pre-image Inversion

Use when the challenge provides an encrypted or scrambled output.

### Execution Steps:
1. Map the transformation function $F(X) = Y$ from disassembled logic.
2. Determine if $F$ is a reversible permutation or has algebraic weakness.
3. Formulate the inverse function $F^{-1}(Y)$ step by step:
   - For SPN permutations: Invert final round transformations first.
   - For differential observations: Solve polynomial equations over finite fields.
4. Verify candidate input against nominal test observations.

---

## 5. Decision Matrix for Backward Tracing

| Observation in Assets | Active Sink Model | First Backward Search Target |
| :--- | :--- | :--- |
| Binary references string `"Correct!"` | Predicate Branch | Branch condition prior to success string |
| Challenge includes `flag.txt` fixture | File System Sink | File opening or process execution calls |
| Script outputs 32 hex bytes | Mathematical Pre-image | Final state transformation operations |
