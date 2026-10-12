# Planning Graph & Dependency Modeling Guide (ASD-STE100)

## 1. Overview
Use this guide to model challenge analysis as a formal Dependency Graph.
Convert intuitive guessing into deterministic Graph Reachability analysis.

```
┌─────────────────────────────────────────────────────────────┐
│                 PLANNING GRAPH ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────┤
│ Fact Inventory (S0) ───────► Forward Operators              │
│                                     │                       │
│                                     ▼                       │
│                              [REACHABILITY GAP]             │
│                                     ▲                       │
│                                     │                       │
│ Canonical I/O Sinks ───────► Backward Operators             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Epistemic Macro-States

Do NOT model individual bytes or memory words.
Model high-level Epistemic Capabilities as boolean facts:

| Fact Token | Semantic Definition |
| :--- | :--- |
| `INPUT_CONTROL` | Input stream reaches target buffer without early exit. |
| `OFFSET_RESOLVED` | Exact byte distance to return pointer or state is known. |
| `IMAGE_BASE_RESOLVED` | Runtime load address of binary or module is known. |
| `DELIMITER_CONSTRAINED` | Input syntax bypasses parser delimiters safely. |
| `TARGET_ADDRESS_KNOWN` | Absolute address of target routine is resolved. |
| `SINK_REACHED` | Program execution reaches output channel or terminal state. |

---

## 3. The Action-Operator Schema

Define operations as transitions between preconditions and postconditions:

```json
{
  "operator": "resolve_return_pointer",
  "preconditions": ["INPUT_CONTROL", "OFFSET_RESOLVED", "TARGET_ADDRESS_KNOWN"],
  "postconditions": ["CONTROL_FLOW_REDIRECTED"],
  "constraints": {
    "max_length": 128,
    "forbidden_bytes": ["0x00", "0x0a"]
  }
}
```

---

## 4. Reachability Algorithm

1. Initialize `CurrentFacts = InitialInventory`.
2. Find all operators where `Preconditions <= CurrentFacts`.
3. Add `Postconditions` to `CurrentFacts`.
4. If `SINK_REACHED in CurrentFacts`: Output the valid action plan.
5. If no new operators can fire:
   - Identify the minimum cut separating `CurrentFacts` from `SINK_REACHED`.
   - The missing preconditions form the **Focus Hunting Directive**.
