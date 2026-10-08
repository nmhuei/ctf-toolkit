---
name: ctf-crypto
description: Use when an authorized CTF challenge has a cryptography problem that needs structured analysis and a reproducible local solution.
---

# Solve CTF Cryptography Tasks

Use local evidence first. Build a precise model. Verify every candidate against the original challenge.

## Workflow

1. Keep the original challenge files unchanged.
2. Read the challenge note. Identify the inputs, outputs, and verification rule.
3. Classify the construction. Read references/attack-router.md when needed.
4. Test the simplest likely weakness with a small, repeatable check.
5. Derive the full equations. State widths, signs, byte order, modulus, encoding, and bounds.
6. Write a reproducible local solver. Save its inputs and exact run command.
7. Verify every original sample and constraint. Record the command and result.
8. If a formal math blocker remains, use ctf-ask with a faithful model.

## Build the Exact Math Model

Translate the source relation, not only the name of a known method. Keep each condition that can change the set of solutions.

### Coppersmith Small Root

For a known-prefix problem, define:

~~~text
m = m0 + x
f(x) = (m0 + x)^e - c
f(x) = 0 mod N
0 <= x < X
~~~

Give the exact N, e, c, m0, X, byte order, and padding. State the polynomial degree and why it is monic. Ask the reviewer to check the conditions for the selected small-root method. Verify the root with the original relation.

For a partial factor, define p = p0 + x and p divides N. Give the unknown-bit positions and the bound on x. Verify N mod p = 0. Do not replace divisibility by a congruence modulo N without proof.

### Lattice

For a bounded modular system, define A, b, q, and each bound:

~~~text
A*x = b mod q
-L_i <= x_i <= L_i
~~~

Give matrix dimensions, coordinate order, norm, and any embedding. Check every equation and bound after the solve.

### Generator

For a finite-state generator, define its transition and output:

~~~text
s_(i+1) = F(s_i)
y_i = G(s_i)
~~~

Give the state width, initial-state range, update order, output projection, truncation, and every observed value. Recompute all observations from the candidate state.

When several stages depend on intermediate values, read ctf-ask's references/de-cyberization-guide.md. Map stages with a dependency DAG, shared equation scopes with a factor graph, and variable coupling with a primal graph. Read references/mathematical-handoff.md before a math consultation.

Use standard mathematical terms when they describe the problem. Omit irrelevant operating details. State the authorized CTF scope truthfully. Do not change the objective to avoid a safety check.

## Verify and Submit

Treat each model answer as a candidate. Recompute it locally. Check every equation, bound, format rule, and original observation.

Do not report solved when only an explanation or partial check supports the answer.

For this user's authorized CTF tasks, submit each flag candidate promptly through the official platform. Submit one challenge and one flag at a time. Record the exact result. Continue the same challenge session after a rejection.

## Tool Choice

Use using-gpt-cli for direct, long-running GPT-CLI work.

Do not run scripts/run_astra_expert.py from this skill. The current helper invokes Codex with an approval and sandbox bypass option. Do not use it unless its execution policy changes and the user authorizes that change.

Use ctf-ask only for a mathematical review. The specialist must not replace local implementation or verification.

## References

- Read references/attack-router.md to classify a construction.
- Read references/orchestration.md to select and test a method.
- Read references/mathematical-handoff.md before a math consultation.
- Read references/expert-prompts.md for the current specialist-use limit.
