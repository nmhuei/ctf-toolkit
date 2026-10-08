# Record CTF Evidence

Keep each result tied to one challenge and one workspace.

## Use Challenge Folders

- Keep source artifacts in challenge/. Do not edit them.
- Put probes, logs, and analysis in script/.
- Put the final reusable solver in solver/.
- Keep credentials out of every folder and report.

## Track Each Candidate

Use these states:

- CANDIDATE: a flag-shaped value for the active challenge.
- LOCAL_CHECKED: a local verifier reproduces the value.
- SUBMITTED: the official platform returned a result.
- REJECTED: the platform rejected the value or the user marked it as a decoy.

A candidate is not a solved result. Mark the challenge solved only after an official acceptance or an authoritative local verifier.

## Submit One Candidate

For this user's authorized CTF tasks, submit each candidate promptly. Use the exact challenge ID and flag.

~~~bash
ctf submit <ID> '<FLAG>' -w <WORKSPACE>
~~~

Record the exact response. Do not use --auto unless the user asks for batch submission.

After a rejection, send the response to the same challenge session. Keep solving and record the next verified step.

## Report the Evidence

Include:

- challenge name and workspace;
- candidate state;
- verifier command and result, when available;
- exact platform response;
- next action.
