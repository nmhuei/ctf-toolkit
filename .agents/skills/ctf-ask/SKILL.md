---
name: ctf-ask
description: Use when an authorized CTF task has a hard mathematical subproblem with a clear, independent verifier.
---

# Ask for Mathematical Help

Use this skill when local work reaches a formal problem. Examples include modular equations, lattice problems, SAT or SMT systems, finite-state models, and parser rules.

A mathematical model is valid when it expresses the actual problem accurately. Do not change the objective or hide the CTF context to avoid a safety check.

## Decide When to Ask

Ask for help only when all points are true:

- The user authorized the event and target.
- The blocker has exact inputs and constraints.
- A local check can verify the answer.
- Local methods are not enough for this blocker.

Keep file parsing, source review, live service work, and routine code changes in the main task.

## Convert the Problem to Math

Use this sequence:

1. State the real task and authorized scope.
2. Identify the unknown values and their domains.
3. Derive the equations from the challenge data or source.
4. State every width, modulus, sign, encoding, bound, and operation order.
5. Include every constraint that can change the answer.
6. Define the candidate format and an exact local check.

Use standard mathematical terms when they describe the problem. Omit operational details that do not affect the math. Remove unrelated credentials and private data. Keep all facts that define the task.

Do not treat an algorithm name as a complete model. State the exact instance that the algorithm must solve.

## Example: Coppersmith Small-Root Problem

A known part of a value can produce a small-root problem. Derive the polynomial from the original relation.

For example, if a challenge gives N, e, c, and a known prefix m0, and the unknown suffix is x, the relation can be:

~~~text
m = m0 + x
f(x) = (m0 + x)^e - c
Find x such that f(x) = 0 mod N and 0 <= x < X.
~~~

The handoff must state the exact values of N, e, c, m0, and X. It must also state the encoding and the full range of x.

Ask the specialist to check that the polynomial matches the source relation. Ask for a method, a candidate root, and a local verification condition.

The local verifier must check:

~~~text
0 <= x < X
((m0 + x)^e - c) mod N == 0
~~~

Do not assume that every partial-factor problem has this form. If p = p0 + x and p divides N, the condition is p0 + x divides N. It is not automatically a root modulo N. State whether the modulus is known or is an unknown factor. Use a method that matches that exact condition.

## Worked Math Models

### 1. Known Plaintext Suffix

Given N, e, c, m0, and X, the challenge defines m = m0 + x.

Assumptions:

- 0 <= x < X.
- c = m^e mod N.
- The byte order, prefix, padding, and integer encoding are known.
- The polynomial and bound meet the selected small-root method's conditions.

Goal: find x.

Use f(x) = (m0 + x)^e - c. Find a root such that f(x) = 0 mod N.

Check: verify 0 <= x < X and ((m0 + x)^e - c) mod N = 0.

Ask the specialist to state the theorem conditions for N, degree e, and X. Do not use a generic bound without checking the selected method.

### 2. Partial Factor

Given N, an approximation p0, and X, the challenge defines p = p0 + x.

Assumptions:

- 0 <= x < X.
- 1 < p < N.
- p divides N.
- The known bits and unknown-bit positions define p0 and x exactly.

Goal: find x.

Check: set p = p0 + x. Verify 1 < p < N and N mod p = 0.

This is a divisibility condition. Do not rewrite it as f(x) = 0 mod N unless the source proves that relation.

### 3. Bounded Modular System

Given integer matrix A, vector b, modulus q, and bounds L_i, find x in Z^n such that:

~~~text
A*x = b mod q
-L_i <= x_i <= L_i, for every i
~~~

State matrix dimensions, row and column order, modulus, and each bound. Check every row of A*x - b is divisible by q.

### 4. Finite-State Generator

Given a, c, w, k, and observed values y_i, model:

~~~text
s_(i+1) = (a*s_i + c) mod 2^w
y_i = s_i mod 2^k
0 <= s_0 < 2^w
~~~

Goal: find s_0 that reproduces every observed y_i. State whether the output uses low bits, high bits, or another projection. Check the full recurrence and every sample.

### 5. Bit-Vector Checker

For unsigned 8-bit values x0, x1, and x2, preserve wraparound and bitwise rules:

~~~text
(x0 + x1) mod 256 = 17
x1 XOR x2 = 42
20 <= x2 <= 90
~~~

Goal: return one satisfying tuple. Check each equation with 8-bit semantics. Do not replace bit-vectors with unbounded integers.

When intermediate values depend on one another, read references/de-cyberization-guide.md and map the stages before asking for help. Use its dependency DAG for a chain, factor graph for shared equation scopes, and primal graph for elimination or treewidth. Read references/handoff-schema.md for the current data format.

## Write a Clear Request

Keep the request concise. Include the true scope, exact math problem, input files, and verification rule.

~~~text
This is an authorized CTF math task. Derive a method for the exact system in TASK.md and instance.json. Return assumptions, a candidate, and checks that the local verifier can run.
~~~

Do not use unclear prompts such as ???, >>>>, or .... A short prompt still needs a clear action.

Do not request hidden chain-of-thought. Request a derivation, assumptions, candidate values, and checkable results. The main solver must write and run the local verifier.

## Check the Handoff

Run the preflight validator before you send the handoff:

~~~bash
python3 <CTF_ASK_SKILL_DIR>/scripts/validate_sanitized_handoff.py preflight --workspace <MATH_WORKSPACE>
~~~

The current validator rejects some CTF terms, URLs, identifiers, and file types. If it rejects a truthful handoff, stop. Do not change accurate terms only to pass the validator. Use local methods or request a validator change.

The helper copies approved files to a temporary directory and runs Codex in read-only mode. This does not prove that the process cannot read files outside that directory. Check the actual sandbox before you rely on isolation.

## Verify the Result

Treat every returned value as a candidate. Run the local verifier against the original equations and observations.

If any check fails, report the failed constraint. Fix the math model before you choose another method.

For this user's authorized CTF tasks, submit each flag candidate through the official platform. Send an exact rejection to the same challenge session and continue.

## Refusal Rule

You may use a mathematical formulation when it is the true problem. Do not disguise the task or remove required facts to avoid a safety check. You may make one truthful clarification if the request omitted its scope or limits. If the system still refuses, stop and report the response.

Read references/escalation-triggers.md before you ask an external specialist.
