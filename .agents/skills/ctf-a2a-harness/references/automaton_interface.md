# Automaton Interface for Multi-Turn Interactive Challenges

## 1. Concept

For interactive network challenges (e.g., text RPGs, menu-driven binaries, heap spray sequencing), the Specialist compiles a deterministic State Automaton instead of reacting turn-by-turn.

```
State(0) ──["Option: "]──► Action: "1\n" ──► State(1)
State(1) ──["Name: "]────► Action: "admin\n" ──► State(2)
State(2) ──["Secret: "]──► Action: Payload ──► Final State
```

---

## 2. Policy Table Format

The Specialist provides the transition dictionary in `solver/recipe.py`:

```python
AUTOMATON_POLICY = {
    # Current State -> List of (Trigger Pattern, Response Action, Next State)
    "START": [
        (r"Choose option:", "1\n", "SELECT_ROLE"),
        (r"Goodbye", None, "TERMINATE")
    ],
    "SELECT_ROLE": [
        (r"Enter username:", "admin\n", "PROMPT_PAYLOAD")
    ],
    "PROMPT_PAYLOAD": [
        (r"Enter token:", lambda ctx: ctx["calculated_token"] + "\n", "READ_FLAG")
    ]
}
```

---

## 3. Orchestrator Automaton Runner

The Orchestrator executes this policy table using standard socket/telnet loops:

```python
def run_automaton(sock, policy, initial_state="START", context=None):
    current_state = initial_state
    buffer = ""
    while current_state != "TERMINATE":
        data = sock.recv(1024).decode(errors="ignore")
        if not data:
            break
        buffer += data
        for pattern, action, next_state in policy.get(current_state, []):
            if re.search(pattern, buffer):
                buffer = ""
                current_state = next_state
                if action is not None:
                    to_send = action(context) if callable(action) else action
                    sock.sendall(to_send.encode())
                break
```

This guarantees sub-millisecond socket interaction and prevents network timeouts.
