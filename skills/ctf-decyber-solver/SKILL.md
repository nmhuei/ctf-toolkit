---
name: ctf-decyber-solver
description: Cognitive specialist reasoning guide. Use to synthesize pure computational recipes and automaton transition policies without socket or network pollution.
---

# De-Cyber Solver: Cognitive Recipe Generation

## 1. Overview

The Solver acts as a pure reasoning specialist.
It accepts a Formal Task Descriptor and outputs an executable Python recipe (`recipe.py`).
It executes zero network calls, zero socket I/O, and zero process spawning.

```
┌─────────────────────────────────────────────────────────────┐
│                       SOLVER ENGINE                         │
├─────────────────────────────────────────────────────────────┤
│ Formal Task Descriptor ────► 1. Model Mathematical System  │
│ (task_descriptor.json)       2. Solve Algebraic Constraints │
│                              3. Synthesize Recipe Function  │
│                              4. Write Offline Unit Tests    │
│                                      │                      │
│                                      ▼                      │
│                           recipe.py + test_recipe.py        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Recipe Execution Contract

Every generated recipe MUST adhere to the strict functional contract:

```python
def solve_model(inputs: dict) -> bytes | int | str:
    """Solve the formal system deterministically.
    
    Args:
        inputs: Dictionary of parsed input parameters or observations.
        
    Returns:
        Computed solution bytes, integer parameter, or output token.
    """
    ...
```

### Prohibited Actions in Solver Recipes
- ❌ Do NOT import `socket`, `requests`, `urllib`, `pwn.remote`.
- ❌ Do NOT call `subprocess.run`, `os.system`, or shell commands.
- ❌ Do NOT read environment variables or remote credentials.
- ❌ Do NOT write files outside the workspace directory.

---

## 3. The Automaton Protocol for Multi-Round Tasks

When a challenge requires multi-step interactive negotiation (e.g., heap menus, math oracles, games):
1. The Solver must NOT sit inside a live socket loop.
2. The Solver outputs an **Automaton Transition Policy**:
   ```python
   POLICY = {
       "INITIAL": {
           r"Select option:\s*": ("1\n", "ENTER_NAME"),
           r"Goodbye!": (None, "TERMINATED")
       },
       "ENTER_NAME": {
           r"Name:\s*": (lambda ctx: f"{ctx['username']}\n", "MENU")
       }
   }
   ```
3. The Orchestrator (`ctf-decyber-runner`) loads this policy into an event loop to execute with zero network delay.

---

## 4. Recipe Development Workflow

1. Read `script/task_descriptor.json` and `script/TASK.md`.
2. Inspect offline numerical fixtures (`observations.json`, `dump.hex`).
3. Formulate equations or constraints using Z3, SageMath, NumPy, or Python standard libraries.
4. Write the derivation function in `solver/recipe.py`.
5. Write an offline test in `solver/test_recipe.py` using sample fixtures.
6. Verify the recipe locally:
   ```bash
   python3 .agents/skills/ctf-decyber-solver/scripts/verify_recipe.py solver/recipe.py
   ```

---

## 5. Supporting Files

- `templates/recipe_template.py`: Standard functional recipe template.
- `templates/automaton_template.py`: State transition table template.
- `scripts/verify_recipe.py`: Recipe structure and contract validator.
- `scripts/graph_planner.py`: Dependency graph planner and reachability analyzer.
- `references/backward_reasoning.md`: Backward goal-regression from canonical I/O sinks guide.
