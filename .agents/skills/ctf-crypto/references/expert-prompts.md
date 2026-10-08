# Mathematical Review in a CTF

Use a specialist only for a formal subproblem that has exact inputs and an independent verifier.

## Current Tool Limit

Do not run scripts/run_astra_expert.py from ctf-crypto. The current runner invokes Codex with an approval and sandbox bypass option.

Use GPT-CLI for the main solve and local implementation. Use ctf-ask only for a permitted mathematical review. Do not ask a specialist to access a live target, credentials, or the challenge workspace.

## Write the Request

State that the task is an authorized CTF. Name the exact mathematical subproblem and provide the definitions needed to solve it.

Ask for:

- a derivation or method;
- assumptions and candidate values;
- the equations or checks that can verify the result.

Do not request hidden reasoning. Do not hide or change the true goal to avoid a safety check.

## Verify the Result

Treat every answer as a candidate. Verify it locally against all stated constraints. Do not report a solve from an explanation alone.
