# Agent-to-Agent (A2A) Communication Protocol Specification

## 1. Formal Task Descriptor Schema (JSON)

The Orchestrator serializes this JSON object into `script/task_descriptor.json` before delegating to the Specialist:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "task_id": "string",
  "category": "algebraic | constraint_satisfaction | grammar_boundary | state_machine | signal_dsp",
  "state_space": {
    "variables": {
      "var_name": {
        "type": "bitvector | integer | bytes | finite_field",
        "width": 64,
        "signed": false,
        "endian": "little | big",
        "modulus": "hex_or_dec_str_if_applicable",
        "bounds": [0, "max_val"]
      }
    }
  },
  "invariants": [
    "Algebraic relation or assertion string that must hold true."
  ],
  "target_predicate": {
    "objective": "find_satisfying_assignment | minimize | inverse_image",
    "goal_assertion": "Assertion string defining what constitutes a solved state."
  },
  "function_contract": {
    "name": "solve_model",
    "arguments": ["arg1", "arg2"],
    "return_type": "bytes | int | dict"
  }
}
```

---

## 2. Executable Recipe Schema (Python Module)

The Specialist writes `solver/recipe.py` conforming to this contract:

```python
"""Specialist Solver Recipe.

Deterministic, pure-computational module.
Dependencies allowed: standard library, numpy, scipy, z3-solver, pycryptodome.
Network calls forbidden.
"""
from __future__ import annotations
from typing import Any, Dict

def solve_model(inputs: Dict[str, Any]) -> Any:
    """Compute and return the exact algebraic/logical solution."""
    # 1. Unpack parameters from formal task descriptor
    # 2. Execute symbolic or mathematical algorithm
    # 3. Return solution satisfying target predicate
    pass
```

---

## 3. Telemetry Feedback Schema (JSON)

When execution fails, the Orchestrator serializes this feedback for the Specialist's next turn:

```json
{
  "status": "failure",
  "turn": 1,
  "failure_class": "invariant_broken | timeout | rejected_candidate | crash",
  "broken_invariant": "Description of which mathematical or physical constraint failed.",
  "observed_delta": {
    "expected": "Expected observation or boundary state.",
    "actual": "Actual returned value or exit signal."
  },
  "suggested_adjustment": "Refine bound / check signedness / invert endianness."
}
```
