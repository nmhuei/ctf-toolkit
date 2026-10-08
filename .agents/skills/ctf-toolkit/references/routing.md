# Route CTF Requests

Use the user's direct words. Keep the active challenge and its evidence together.

## Route Order

1. decoy or rejected flag
2. status or tiến độ
3. next or continue
4. challenge ID or name
5. new hint or hypothesis
6. new environment limit

## Actions

### Select a challenge

Find one exact challenge workspace. Read metadata.json, challenge/NOTE.md, challenge files, and prior script notes.

Start local triage when the target is clear. Ask the user only when no exact match exists or more than one match is possible.

### Continue work

Read the last result in script/ or NOTE.md. Run the next unfinished check. Keep the same challenge and session.

If a tool failed, use references/recovery.md. Do not repeat the same failed action without a new check.

### Report status

Give these facts:

- current phase;
- last verified result;
- next action;
- blocker, if any.

### Reject a candidate

Mark the candidate rejected in script/analysis.md. Record where it came from and why it failed. Do not test the same candidate again without new evidence.

### Apply a new limit

Apply the user's new limit to the current task. Keep completed checks and results.

## Match a Target

Use this order:

1. exact challenge name;
2. category and display number, such as pwn5;
3. exact directory name;
4. one unique partial name.

If the match is not unique, ask the user to choose.
