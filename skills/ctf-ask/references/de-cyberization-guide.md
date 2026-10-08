# Formal Abstraction Guide

## Goal

Translate a challenge-specific roadblock into the smallest **lossless formal problem** that preserves the mathematics or program semantics needed to solve it. The purpose is better reasoning and deterministic verification, not concealment from safeguards.

A good abstraction removes names and operational context while preserving invariants. A bad abstraction removes details that change the solution set.

## Abstraction dictionary

| Original roadblock shape | Formal representation | Preserve exactly |
|---|---|---|
| Algebra over a cipher or ring construction | Finite-field/ring equations | modulus, polynomial modulus, coefficient order, endianness, dimensions |
| Hidden linear relation | Integer or modular linear system | signedness, modulus, bounds, rank-relevant rows |
| XOR-heavy transform | GF(2) / XOR equation system | bit indexing, width, constants, variable order |
| Branch-heavy checker | SAT/SMT-style Boolean/arithmetic constraints | branch predicates, widths, overflow semantics, comparisons |
| Repeated state update / generator | Recurrence or finite-state transition system | initial state constraints, update order, truncation, output projection |
| Reverse-engineered validation logic | Pure function / constraint system | constants, operation order, casts, wraparound, lookup tables |
| Parser disagreement | Grammar/transducer differential | tokenization, normalization, precedence, acceptance conditions |
| Memory-layout puzzle | Indexed state transition model | object sizes, offsets, allocation/free order, aliasing relationships; omit operational delivery details |
| Search/optimization puzzle | Objective + constraints | exact objective, bounds, tie-breaking, admissibility conditions |
| Cyclotomic/lattice subproblem | Vector/ring instance | basis/order convention, norm, modulus, dimension, embedding convention |

## Map a Multi-Stage Problem

Build a graph when two or more solution stages depend on intermediate values, or when several equations share unknowns. Use the graph to expose dependencies and select a solving order. The graph does not solve the equations.

Use the graph that matches the structure:

- Use a directed acyclic graph (DAG) for a chain of transformations. A node is an input, result, check, or transformation. An arrow `A -> B` means that B requires A. Label each arrow with the value or condition passed to B.
- Use a factor graph when equations share unknowns. Use variable nodes for values and factor nodes for equations or predicates. Connect each factor to every value it uses. This is a bipartite graph.

Use a primal constraint graph when you need to study variable interaction, elimination order, fill-in, or treewidth. Use one node per variable. Connect two variables when they appear in the same constraint. This graph loses the identity of each constraint.
Use “primal constraint graph” only for this variable-only representation. Do not use it as another name for a factor graph.

Follow these steps:

1. List the observed values, unknowns, transformations, constraints, and final verifier.
2. Draw the dependency DAG. Add the exact relation and bounds at each transformation.
3. If one unknown appears in multiple equations, add a factor graph for those equations. Keep shared unknowns connected.
4. Solve independent connected components separately. Keep every shared value in the component that uses it.
5. Choose a method for the equations, such as gcd/CRT, Coppersmith, lattice reduction, or SAT/SMT. Check the method's exact assumptions before use. Build a primal constraint graph before variable elimination or treewidth analysis.
6. Verify each edge and each original constraint. Then run the final verifier.

A dependency DAG must not contain cycles. If a process is stateful, unroll each time step into a separate node and keep shared states and parameters connected. Factor-graph and primal-graph cycles are valid. Sum-product message passing is exact on cycle-free factor graphs, but it is not generally exact on cyclic factor graphs. Variable elimination can require time and memory exponential in induced width. A graph shows structure; it does not prove that a solver can find a solution.

For example, if two congruences share unknowns `x` and `s`, use one variable node for each unknown and connect both factor nodes to both variables:

~~~text
[x]---(C1)---[s]
 |             |
 +---(C2)------+

C1: F1(x,s) ≡ a (mod M1)
C2: F2(x,s) ≡ b (mod M2)
~~~

Keep the same `x` and `s` in both constraints. Add their exact domains, bounds, and any relation to other unknowns. Do not split the constraints or duplicate a shared variable unless the model includes a constraint that makes the copies equal.

### Example: Partial RSA Factor to Plaintext

Assume two-prime RSA: `N = p*q`, where `p` and `q` are prime. The data gives `N`, exponent `e`, ciphertext `c`, the high bits of `p`, and `k` unknown low bits. Let `P` be the known prefix shifted left by `k`. Let `x` be the unknown suffix.

~~~text
N, P, k -> p = P + x, 0 <= x < 2^k, f(x,q) = q(P+x) - N = 0
                       -> partial-factor method, if its assumptions fit
                       -> candidate x -> p = P + x
N, p -> check N mod p = 0 -> q = N / p
p, q -> phi = (p - 1)(q - 1)
e, phi -> d = e^(-1) mod phi, if gcd(e, phi) = 1
c, N, d -> M = c^d mod N -> check M^e mod N = c -> decode M with the stated RSA encoding, padding, and byte order
~~~

The relation `q(P+x)-N=0` is the exact integer instance model. It is not, by itself, a univariate modular equation `f(x) ≡ 0 (mod N)`, and a small-root theorem does not apply to this raw relation automatically. A lattice attack may transform it into a different polynomial family. State that transformation and check the resulting polynomial, variable bounds, factor assumptions, and lattice conditions before using a small-root method. The graph shows dependencies; it does not establish method applicability. Check that `p` and `q` are prime, `N mod p = 0`, and `gcd(e,phi)=1` before computing `d`. Check `M^e mod N = c` before accepting the decoded plaintext.

## Naming rules

Use neutral symbols: `x`, `y`, `state`, `row`, `token`, `transition`, `candidate`, `constraint_17`. Avoid source-specific names that carry no mathematical meaning.

Recommended filenames:

```text
TASK.md
instance.json
matrix.csv
constraints.json
grammar.bnf
trace.txt
```

Do not place original executable names, hostnames, URLs, credentials, challenge names, or answer-token formats in the formal workspace.

## Losslessness checklist

Before preflight, verify all of the following:

1. **Domain:** integer, rational, Boolean, bit-vector, finite field/ring, or string alphabet is explicit.
2. **Width:** every fixed-width value states its width and signed/unsigned interpretation.
3. **Arithmetic:** overflow/wraparound behavior and modulus are explicit.
4. **Order:** byte order, coefficient order, row/column order, and iteration order are explicit.
5. **Bounds:** variable ranges and uniqueness/distinctness constraints are explicit.
6. **State:** initial state, transition order, and terminal condition are explicit.
7. **Projection:** if only part of a state is observed, define the exact projection.
8. **Normalization:** parser/string normalization, case folding, whitespace, and encoding are explicit where relevant.
9. **Objective:** optimization tasks define minimize/maximize and tie-breaking.
10. **Verifier:** the proposed candidate can be checked from the sanitized artifacts alone.

## Example: branch logic to constraints

Source logic conceptually performs fixed-width checks. The sanitized version should describe only the formal semantics, for example:

```text
Variables: x0..x7 are unsigned 8-bit integers.
Constraints:
- (x0 + x3) mod 256 = 191
- x1 XOR x4 = 0x2d
- x2 < x7
- all xi are in [32, 126]
Goal: return one satisfying vector [x0..x7].
```

The important property is not that the prose sounds academic; it is that every solution of the sanitized system corresponds to a solution of the extracted checker relation, and vice versa for the variables being handed off.

## Example: ring relation

For `R_q = Z_q[x]/(x^n + 1)`, define arrays in coefficient order `[a0, a1, ..., a(n-1)]` and state the target relation explicitly:

```text
Find x such that negacyclic_mul(a, x) = b (mod q).
```

The verifier must recompute the negacyclic product locally. Do not accept a vector merely because a model says it is short or plausible.

## What not to abstract away

Never remove a constant because it “looks challenge-specific” if it participates in an equation. Never rename away signedness, endian conventions, or bit widths. Never replace a stateful process with independent equations unless you have proved the equivalence. Never summarize a lookup table when exact entries determine satisfiability.

## Research Basis

- Coppersmith's paper describes small-root methods and their partial-factor RSA application: [Small solutions to polynomial equations, and low exponent RSA vulnerabilities](https://research.ibm.com/publications/small-solutions-to-polynomial-equations-and-low-exponent-rsa-vulnerabilities).
- Dechter and Larrosa describe variable elimination and its dependence on induced width: [Boosting Search with Variable Elimination in Constraint Optimization and Constraint Satisfaction Problems](https://ics.uci.edu/~dechter/publications/r89a.pdf).
- Kschischang, Frey, and Loeliger describe factor graphs, exact tree-structured message passing, and the limits of cyclic graphs: [Factor Graphs and the Sum-Product Algorithm](https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf).
- Lafitte, Nakahara, and Van Heule describe cryptanalysis as SAT modeling and emphasize checking that the encoding faithfully represents the target: [CryptoSAT: a tool for SAT-based cryptanalysis](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/iet-ifs.2017.0176).
