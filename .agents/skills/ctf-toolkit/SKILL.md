---
name: ctf-toolkit
description: Use when you manage CTF downloads, challenge workspaces, instances, solver workers, or flag submissions.
---

# Use the CTF Toolkit

Use this skill for the local ctf command. Use using-gpt-cli for a direct, long-running GPT-CLI session.

Work only on a CTF that the user authorized. Use the workspace that belongs to that event.

## Read the Current State

When the user names a challenge, find its exact workspace. Read metadata.json, challenge/NOTE.md, challenge files, and prior script notes.

If the target is ambiguous, show the matching challenges and ask which one the user means.

Use these prompt actions:

- next or continue: run the next unfinished check.
- status or tiến độ: report the phase, last verified fact, next action, and blocker.
- decoy: mark the active candidate as rejected. Keep its source and reason.
- a new constraint: apply it to the current task. Keep verified work.

Do not use symbol-only prompts such as ???, >>>>, or ... . State one action and its target.

## Use Verified Commands

The commands below match the current CLI help.

~~~bash
ctf auth --from-burp -u <URL>
ctf pull -u <URL> -o <WORKSPACE> --from-burp --save-cookie
ctf status -w <WORKSPACE>
ctf solve -w <WORKSPACE> --ids 1,2 --workers 3
ctf solve --status
ctf solve --logs 2
ctf instance start --id <ID> -w <WORKSPACE>
ctf instance extend --id <ID> -w <WORKSPACE>
ctf platform probe <URL>
ctf submit <ID> '<FLAG>' -w <WORKSPACE>
~~~

Use ctf solve for the toolkit worker queue. Use gpt agent when the user asks for a direct GPT-CLI session.

The instance actions are start, stop, extend, status, and list. Do not use restart or renew.

The pull command has no --bridge option. The solve command has no --per-category option. Use ctf bridge as a separate command when you need bridge status or control.

## Keep Challenge Evidence

Keep original files in challenge/. Put probes, temporary scripts, logs, and analysis in script/. Put the final reusable solver in solver/.

Do not call a challenge solved because a file exists. Run its verifier and record the command and result.

For this user's authorized CTF tasks, submit each flag candidate for the active challenge promptly. Submit one challenge and one flag at a time. Do not use --auto unless the user asks for batch submission.

Record the exact platform result. If the platform rejects a candidate, send that result to the same GPT-CLI session and continue that challenge. Do not send it to another challenge session.

## Keep Files in the Right Place

When a GPT-CLI session solves work in a clean workspace, ask that same session to return the needed files:

~~~text
chuyển các file liên quan về đúng vị trí thư mục <path>
~~~

Check the copied solver and evidence at the canonical path. Keep unrelated files and credentials out.

## Handle Refusals Clearly

State the authorized CTF scope and the real task. A clear formal math model can help solve a math problem. Keep every constraint that affects the result.

Do not change the stated goal to hide it from a safety check. If the model refuses, clarify only missing facts. If it still refuses, stop and report the refusal.

## Read More

- Read references/routing.md for prompt actions and target matching.
- Read references/evidence.md before you verify or submit a flag.
- Read references/recovery.md when a tool or worker fails.
- Read references/platform_authoring.md and use ctf-add-new-platform for a new platform.

