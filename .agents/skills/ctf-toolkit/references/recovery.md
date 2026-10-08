# Recover from CTF Tool Errors

Use the exact error and the saved task state. Do not guess the cause.

## Find the Failure

- For a GPT-CLI session, read gpt session log <SESSION_ID> --events.
- For the solver queue, read ctf status --solver.
- For one worker, read ctf solve --logs <ID>.
- Record the command, exit code, and last useful output.

## Continue the Same Task

After one SSE disconnect, inspect the same GPT-CLI session. Wait when the server still owns the turn. Do not start a new session only because the stream stopped.

If a tool error repeats, send one short steer with the exact failed command and the next check. If it fails again, stop and report the blocker. Keep the log.

Do not send a one-word continue after a tool error. Name the next action.

## Check Authentication

For a CTF platform error, check the saved credential source and platform status. Do not print a cookie or token.

For GPT-CLI HTTP 401 or 403, inspect the wire headers, account ID, Sentinel data, device ID, TLS profile, and token refresh. Do not assume quota or token expiry without evidence.

## Handle a Model Refusal

State the authorized CTF scope and the real task. Make one truthful clarification only when the prompt omitted a required fact.

Do not rename or hide the goal to avoid a safety check. If the model still refuses, stop and report the response.

Use ctf-ask only for a real mathematical subproblem with exact inputs and a local verifier. Do not use it to bypass a refusal.

## Protect Local Data

Use the configured credential store. Do not copy credentials into prompts, logs, or challenge notes.

Include a target address only when the authorized task needs it. Do not change a real address or service name only to alter a safety result.
